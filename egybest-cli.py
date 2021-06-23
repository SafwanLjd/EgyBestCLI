#!/usr/bin/env python3

from pySmartDL import SmartDL
from pathlib import Path
from egybest import *
import click
import tkvlc
import json
import os

ICON_URL = "https://github.com/SafwanLjd/EgyBestCLI/releases/download/v1.2/EgyBest.ico"

DEFAULT_CONFIG = \
"""{
	"quality": {
		"2160": 1,
		"1080": 2,
		"720":  3,
		"480":  4,
		"360":  5,
		"240":  6
	}
}"""

try:
    HOME_DIR = str(Path.home())
    CONFIG_DIR = f"{HOME_DIR}/.config"
    CONFIG_FILE = f"{CONFIG_DIR}/egybest-conf.json"
    ICON_FILE = f"{CONFIG_DIR}/EgyBest.ico"

    if not os.path.isdir(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    if not os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as file:
            file.write(DEFAULT_CONFIG)

    CONFIG_DATA = json.loads(open(CONFIG_FILE, "r").read())
    QUALITY_PREFERENCE = CONFIG_DATA["quality"]

    if not os.path.isfile(ICON_FILE):
        SmartDL(urls=ICON_URL, dest=ICON_FILE, progress_bar=False).start()

except Exception as exception:
    try:
        CONFIG_DATA = json.loads(DEFAULT_CONFIG)
        QUALITY_PREFERENCE = CONFIG_DATA["quality"]
    finally:
        print(f"Exception: {exception}")


@click.option("-o", "--stdout", is_flag=True, help="Print The Video URL to Standard Output")
@click.option("-w", "--watch", is_flag=True, help="Watch Directly Without Downloading")
@click.option("-ms", "--manual-search", is_flag=True, help="Select From Search Results Manually")
@click.option("-mq", "--manual-quality", is_flag=True, help="Select The Video Quality Manually")
@click.option("-e", "-E", "--episode")
@click.option("-s", "-S", "--season")
@click.option("-t", "--title", required=True, help="The Name of The Desired Movie/Show")
@click.command()
def egybest(title: str, season: int, episode: int, manual_quality: bool, manual_search: bool, watch: bool, stdout: bool):
    """A Command-Line Interface Wrapper For EgyBest That Allows You to Download Movies, Episodes, and Even Whole Seasons!"""
    isMovie = (season is None)

    if not isMovie and not season.isdigit():
        raise TypeError("--season Must Have A Numerical Value.")
    
    if isMovie and episode:
        stdout or print("Ignoring --episode And Searching For A Movie Because No Season Was Specified")

    if stdout and (manual_quality or manual_search):
        errorMessage = ""
        if manual_search:
            errorMessage += "Error: You Can Not Select From Search Manually Because You Specified --stdout\nThe Closest Result to Your Search Query Will Be Chosen Automatically.\n"
        if manual_quality:
            errorMessage += "Error: You Can Not Select The Video Quality Manually Because You Specified --stdout\nPlease Set The Video Quality Preferences in The \"~/.config/egybest-conf.json\" File.\n"

        raise ValueError(errorMessage)

    if watch and stdout:
        print("Ignoring --stdout Because You Specified --watch")
        stdout = False

    bulk = (not isMovie and not episode)

    if not isMovie and not bulk and not episode.isdigit():
        raise TypeError("--episode Must Have A Numerical Value.")

    stdout or print("Searching... ")
    eb = EgyBest()
    results = eb.search(title, includeMovies=isMovie, includeShows=(not isMovie))
    resultsLength = len(results)

    if resultsLength == 0:
        raise IndexError(f"No Results Were Found For The Title \"{title}\" on EgyBest!")

    if manual_search:
        if resultsLength == 1:
            print("Only Found 1 Result, Ignoring --manual-search")
            searchResult = results[0]
        else:
            print("")
            for i in range(resultsLength):
                print(f"{i+1}- {results[i].title}")

            choice = input(f"\nWhich One Did You Mean [1-{resultsLength}]? ")

            if not choice.isdigit():
                raise TypeError(f"Error: You Can Only Pass A Number [1-{resultsLength}].")

            choice = int(choice)
            if choice < 0 or choice >= resultsLength:
                raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {resultsLength}, But You Chose \"{choice}\".")

            searchResult = results(choice - 1)
    else:
        searchResult = results[0]
    
    stdout or print(f"Found \"{searchResult.title}\"... ")

    if isMovie:
        selectedEpisodes = [searchResult]
    else:
        stdout or print("Getting Seasons... ")
        seasons = searchResult.getSeasons()

        season = int(season) - 1
        if season >= len(seasons):
            raise IndexError("The Specified Season Does Not Exist on EgyBest!")

        selectedSeason = seasons[season]

        stdout or print("Getting Episodes... ")
        episodes = selectedSeason.getEpisodes()

        if not bulk:
            episode = int(episode) - 1
            if episode >= len(episodes):
                raise IndexError("The Specified Episode Does Not Exist on EgyBest!")

            selectedEpisodes = [episodes[episode]]

        else:
            selectedEpisodes = episodes        

    stdout or print(f"\nGetting Media Link", end="")
    stdout or (bulk and print(f"s For {len(selectedEpisodes)} Episodes (Might Take A Few Minutes)", end=""))
    stdout or print("... ")

    downloadSources = []
    for i in range(len(selectedEpisodes)):
        downloadOptions = selectedEpisodes[i].getDownloadSources()
        downloadOptionsLength = len(downloadOptions)

        if not bulk and manual_quality:
            if downloadOptionsLength == 1:
                print("Only Found 1 Quality Option, Ignoring --manual-quality")
                downloadSources.append(downloadOptions[0])
            else:
                print("")
                for i in range(downloadOptionsLength):
                    print(f"{i+1}- {downloadOptions[i].quality}p")

                choice = input(f"Select Your Preferred Video Quality [1-{downloadOptionsLength}]: ")

                if not choice.isdigit():
                    raise TypeError(f"Error: You Can Only Pass A Number [1-{downloadOptionsLength}].")
                
                choice = int(choice)
                if choice <= 0 or choice > downloadOptionsLength:
                    raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {downloadOptionsLength}, But You Chose \"{choice}\".")

                downloadSources.append(downloadOptions[choice - 1])
        else:
            if manual_quality and bulk:
                print("Ignoring --maunal-quality Because You Selected A Whole Season, Getting Quality Preferences From The Config File")

            downloadOptions.sort(key=lambda element: QUALITY_PREFERENCE[str(element.quality)])
            downloadSources.append(downloadOptions[0])

    if stdout:
        for downloadSource in downloadSources:
            print(downloadSource.link)
    elif watch:
        downloadSource = downloadSources[0]
        windowTitle = " ".join(downloadSource.fileName.replace("-ep-", "-episode-").split("-")[:-1]).title() + " - " + str(downloadSource.quality) + "p"
        player = tkvlc.Player(downloadSource.link, title=windowTitle, iconPath=ICON_FILE)
        player.start()
    else:
        for downloadSource in downloadSources:
            download(downloadSource)


def download(downloadSource):
    print(f"\nDownloading \"{downloadSource.fileName}\"... ")
    downloader = SmartDL(urls=downloadSource.link, dest=f"./{downloadSource.fileName}")

    try:
        downloader.start(blocking=True)
    except KeyboardInterrupt:
        downloader.stop()
        raise InterruptedError("Download Stopped!")



if __name__ == "__main__":

    if "QUALITY_PREFERENCE" in globals() and QUALITY_PREFERENCE:
        
        try:
            egybest(prog_name="egybest")
        
        except Exception as exception:
            print(exception)
        
        except KeyboardInterrupt:
            print("Aborted!")
