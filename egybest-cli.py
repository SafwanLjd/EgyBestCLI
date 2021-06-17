#!/usr/bin/env python3

from pySmartDL import SmartDL
from shutil import copyfile
from pathlib import Path
from time import sleep
from egybest import *
import click
import json
import os

HOME_DIR = str(Path.home())
CONFIG_DIR = f"{HOME_DIR}/.config"
CONFIG_FILE = f"{CONFIG_DIR}/egybest-conf.json"

if not os.path.isdir(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

if not os.path.isfile(CONFIG_FILE):
    copyfile("./defaults.json", CONFIG_FILE)

CONFIG_DATA = json.loads(open(CONFIG_FILE, "r").read())
QUALITY_PREFERENCE = CONFIG_DATA['quality']



@click.option('-o', '--stdout', is_flag=True, help='Print The Video URL to Standard Output')
@click.option('-ms', '--manual-search', is_flag=True, help='Select From Search Results Manually')
@click.option('-mq', '--manual-quality', is_flag=True, help='Select The Video Quality Manually')
@click.option('-e', '-E', '--episode')
@click.option('-s', '-S', '--season')
@click.option('-t', '--title', required=True, help='The Name of The Desired Movie/Show')
@click.command()
def egybest(title: str, season: int, episode: int, manual_quality: bool, manual_search: bool, stdout: bool):
    """A Command-Line Interface Wrapper For EgyBest That Allows You to Download Movies, Episodes, and Even Whole Seasons!"""
    isMovie = (season is None)

    if not isMovie and not season.isdigit():
        raise TypeError("--season Must Have A Numerical Value")

    if stdout and (manual_quality or manual_search):
        errorMessage = ""
        if manual_search:
            errorMessage += "Error: You Can't Select From Search Manually Because You Specified --stdout\nThe Closest Result to Your Search Query Will Be Chosen Automatically.\n"
        if manual_quality:
            errorMessage += "Error: You Can't Select The Video Quality Manually Because You Specified --stdout\nPlease Set The Video Quality Preferences in The \"~/.config/egybest-conf.json\" File.\n"

        raise ValueError(errorMessage)

    bulk = (not isMovie and episode is None)

    stdout or print("Searching... ")
    results = search(title, includeMovies=isMovie, includeShows=(not isMovie))
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
                raise TypeError(f"Error: You Can Only Pass A Number [1-{resultsLength}]")
            elif choice < 0 or choice >= resultsLength:
                raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {resultsLength}, But You Chose \"{choice}\"")

            searchResult = results(int(choice) - 1)
    else:
        searchResult = results[0]

    if isMovie:
        selectedEpisodes = [searchResult]
    else:
        stdout or print("Getting Seasons... ")
        seasons = searchResult.getSeasons()

        season = int(season) - 1
        if season >= len(seasons):
            raise IndexError("The Specified Season Doesn't Exist on EgyBest!")

        selectedSeason = seasons[season]

        stdout or print("Getting Episodes... \n")
        episodes = selectedSeason.getEpisodes()

        if not bulk:
            episode = int(episode) - 1
            if episode >= len(episodes):
                raise IndexError("The Specified Episode Doesn't Exist on EgyBest!")

            selectedEpisodes = [episodes[episode]]

        else:
            selectedEpisodes = episodes        

    stdout or print(f"Getting Media Link", end="")
    stdout or (bulk and print(f" For {len(selectedEpisodes)} Episodes (Might Take A Few Minutes)", end=""))
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

                choice = input(
                    f"Select Your Preferred Video Quality [1-{downloadOptionsLength}]: ")

                if not choice.isdigit():
                    raise TypeError(
                        f"Error: You Can Only Pass A Number [1-{downloadOptionsLength}]")
                elif choice <= 0 or choice > downloadOptionsLength:
                    raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {downloadOptionsLength}, But You Chose \"{choice}\"")

                downloadSources.append(downloadOptions[int(choice) - 1])
        else:
            if manual_quality and bulk:
                print("Ignoring --maunal-quality Because You Selected A Whole Season, Getting Quality Preferences From The Config File")

            downloadOptions.sort(
                key=lambda element: QUALITY_PREFERENCE[str(element.quality)])
            downloadSources.append(downloadOptions[0])

    if stdout:
        for downloadSource in downloadSources:
            print(downloadSource.link)
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



if __name__ == '__main__':
    try:
        egybest(prog_name='egybest')
    except Exception as exception:
        print(exception)
    except KeyboardInterrupt:
        print("Aborted!")
