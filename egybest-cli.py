#!/usr/bin/env python3

from pySmartDL import SmartDL
from pathlib import Path
from egybest import *
import click
import json
import os

HOME_DIR = str(Path.home())
CONFIG_DIR = f"{HOME_DIR}/.config"
EGYBEST_DIR = f"{CONFIG_DIR}/egybest"
CONFIG_FILE = f"{EGYBEST_DIR}/egybest-conf.json"
ICON_FILE = f"{EGYBEST_DIR}/EgyBest.ico"
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
    is_movie = (season is None)

    if not is_movie and not season.isdigit():
        raise TypeError("--season Must Have A Numerical Value.")
    
    if is_movie and episode:
        stdout or print("Ignoring --episode And Searching For A Movie Because No Season Was Specified")

    if stdout and (manual_quality or manual_search):
        err_msg = ""
        if manual_search:
            err_msg += "Error: You Can Not Select From Search Manually Because You Specified --stdout\nThe Closest Result to Your Search Query Will Be Chosen Automatically.\n"
        if manual_quality:
            err_msg += "Error: You Can Not Select The Video Quality Manually Because You Specified --stdout\nPlease Set The Video Quality Preferences in The \"~/.config/egybest-conf.json\" File.\n"

        raise ValueError(err_msg)

    if watch and stdout:
        print("Ignoring --stdout Because You Specified --watch")
        stdout = False

    bulk = (not is_movie and not episode)

    if not is_movie and not bulk and not episode.isdigit():
        raise TypeError("--episode Must Have A Numerical Value.")

    stdout or print("Searching... ")
    eb = EgyBest()
    results = eb.search(title, includeMovies=is_movie, includeShows=(not is_movie))
    results_len = len(results)

    if results_len == 0:
        raise IndexError(f"No Results Were Found For The Title \"{title}\" on EgyBest!")

    if manual_search:
        if results_len == 1:
            print("Only Found 1 Result, Ignoring --manual-search")
            search_result = results[0]
        else:
            print("")
            for i in range(results_len):
                print(f"{i+1}- {results[i].title}")

            choice = input(f"\nWhich One Did You Mean [1-{results_len}]? ")

            if not choice.isdigit():
                raise TypeError(f"Error: You Can Only Pass A Number [1-{results_len}].")

            choice = int(choice)
            if choice < 0 or choice >= results_len:
                raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {results_len}, But You Chose \"{choice}\".")

            search_result = results(choice - 1)
    else:
        search_result = results[0]
    
    stdout or print(f"Found \"{search_result.title}\"... ")

    if is_movie:
        selected_episodes = [search_result]
    else:
        stdout or print("Getting Seasons... ")
        seasons = search_result.getSeasons()

        season = int(season) - 1
        if season >= len(seasons):
            raise IndexError("The Specified Season Does Not Exist on EgyBest!")

        selected_season = seasons[season]

        stdout or print("Getting Episodes... ")
        episodes = selected_season.getEpisodes()

        if not bulk:
            episode = int(episode) - 1
            if episode >= len(episodes):
                raise IndexError("The Specified Episode Does Not Exist on EgyBest!")

            selected_episodes = [episodes[episode]]

        else:
            selected_episodes = episodes        

    stdout or print(f"\nGetting Media Link", end="")
    stdout or (bulk and print(f"s For {len(selected_episodes)} Episodes (Might Take A Few Minutes)", end=""))
    stdout or print("... ")

    dl_srcs = []
    for i in range(len(selected_episodes)):
        dl_options = selected_episodes[i].getDownloadSources()
        dl_options_len = len(dl_options)

        if not bulk and manual_quality:
            if dl_options_len == 1:
                print("Only Found 1 Quality Option, Ignoring --manual-quality")
                dl_srcs.append(dl_options[0])
            else:
                print("")
                for i in range(dl_options_len):
                    print(f"{i+1}- {dl_options[i].quality}p")

                choice = input(f"Select Your Preferred Video Quality [1-{dl_options_len}]: ")

                if not choice.isdigit():
                    raise TypeError(f"Error: You Can Only Pass A Number [1-{dl_options_len}].")
                
                choice = int(choice)
                if choice <= 0 or choice > dl_options_len:
                    raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {dl_options_len}, But You Chose \"{choice}\".")

                dl_srcs.append(dl_options[choice - 1])
        else:
            if manual_quality and bulk:
                print("Ignoring --maunal-quality Because You Selected A Whole Season, Getting Quality Preferences From The Config File")

            dl_options.sort(key=lambda element: get_quality_prefrence()[str(element.quality)])
            dl_srcs.append(dl_options[0])

    if stdout:
        for dl_src in dl_srcs:
            print(dl_src.link)

    elif watch:
        import tkvlc

        if not os.path.isfile(ICON_FILE):
            SmartDL(urls=ICON_URL, dest=ICON_FILE, progress_bar=False).start()

        dl_src = dl_srcs[0]
        window_title = " ".join(dl_src.fileName.split("-")[:-1]).title() + " - " + str(dl_src.quality) + "p"
        player = tkvlc.Player(dl_src.link, title=window_title, iconPath=ICON_FILE)
        player.start()

    else:
        for dl_src in dl_srcs:
            download(dl_src)


def download(dl_src):
    print(f"\nDownloading \"{dl_src.fileName}\"... ")
    downloader = SmartDL(urls=dl_src.link, dest=f"./{dl_src.fileName}")

    try:
        downloader.start(blocking=True)
    except KeyboardInterrupt:
        downloader.stop()
        raise InterruptedError("Download Stopped!")


def get_quality_prefrence():
    try:
        quality_prefrence = json.loads(open(CONFIG_FILE, "r").read())["quality"]

    except Exception as exception:
        try:
            if not os.path.isdir(CONFIG_DIR):
                os.mkdir(CONFIG_DIR)
            
            if not os.path.isdir(EGYBEST_DIR):
                os.mkdir(EGYBEST_DIR)
            
            if not os.path.isfile(CONFIG_FILE):
                with open(CONFIG_FILE, "w") as file:
                    file.write(DEFAULT_CONFIG)

        finally:
            quality_prefrence = json.loads(DEFAULT_CONFIG)["quality"]

    return quality_prefrence


if __name__ == "__main__":

    try:
        egybest(prog_name="egybest")
    
    except Exception as exception:
        print(exception)
    
    except KeyboardInterrupt:
        print("Aborted!")
