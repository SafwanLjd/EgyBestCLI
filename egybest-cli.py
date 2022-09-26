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
DEFAULT_CONFIG = \
"""{
    "mirror": "https://egy.best",

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






def egybest(title: str, season: int, episode: int, manual_quality: bool, manual_search: bool, watch: bool, stdout: bool) -> None:
    """A Command-Line Interface Wrapper For EgyBest That Allows You to Download Movies, Episodes, and Even Whole Seasons!"""
    is_movie = (season is None)

    
    if not is_movie and not season.isdigit():
        raise TypeError("--season Must Have A Numerical Value.")
    
    if is_movie and episode:
        stdout or print("Ignoring --episode And Searching For A Movie Because No Season Was Specified")

    # if stdout and (manual_quality or manual_search):
    #     err_msg = ""
    #     if manual_search:
    #         err_msg += "Error: You Can Not Select From Search Manually Because You Specified --stdout\nThe Closest Result to Your Search Query Will Be Chosen Automatically.\n"
    #     if manual_quality:
    #         err_msg += "Error: You Can Not Select The Video Quality Manually Because You Specified --stdout\nPlease Set The Video Quality Preferences in The \"~/.config/egybest-conf.json\" File.\n"

    #     raise ValueError(err_msg)

    if watch and stdout:
        print("Ignoring --stdout Because You Specified --watch")
        stdout = False

    bulk = (not is_movie and not episode)

    if not is_movie and not bulk and not episode.isdigit():
        raise TypeError("--episode Must Have A Numerical Value.")

    stdout or print("Searching... ")

    eb = EgyBest(get_mirror())

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

    stdout or print(f"\nGetting Media Links", end="")
    stdout or (bulk and print(f" For {len(selected_episodes)} Episodes (Might Take A Few Minutes)", end=""))
    stdout or print("... ")

    dl_srcs = []
    choix=0

    for i in range(len(selected_episodes)):
        dl_options = selected_episodes[i].getDownloadSources()
        dl_options_len = len(dl_options)

        if dl_options_len == 0:
            raise ValueError(f"Error: Couldn't Find Any Media Links")

        if manual_quality:
            if not len(dl_srcs):
                selected_option,choix=set_quality(dl_options,dl_options_len)
                dl_srcs.append(selected_option)
            else:
                dl_options.sort(key=lambda element: get_quality_prefrence()[str(element.quality)])
                print("Setting quality to:",choix+1)
                dl_srcs.append(dl_options[choix])
                
            # if dl_options_len == 1:
            #     print("Only Found 1 Quality Option, Ignoring --manual-quality")
            #     dl_srcs.append(dl_options[0])
            # else:
            #     print("")
            #     for i in range(dl_options_len):
            #         print(f"{i+1}- {dl_options[i].quality}p")

            #     choice = input(f"Select Your Preferred Video Quality [1-{dl_options_len}]: ")

            #     if not choice.isdigit():
            #         raise TypeError(f"Error: You Can Only Pass A Number [1-{dl_options_len}].")
                
            #     choice = int(choice)
            #     if choice <= 0 or choice > dl_options_len:
            #         raise IndexError(f"Error: Invalid Choice! The Options Were From 1 to {dl_options_len}, But You Chose \"{choice}\".")

            #     dl_srcs.append(dl_options[choice - 1])
        else:
            # if not manual_quality:
            # option=set_quality(dl_options)
            # print("Ignoring --maunal-quality Because You Selected A Whole Season, Getting Quality Preferences From The Config File")
            print("Default quality set to 360p")
            dl_options.sort(key=lambda element: get_quality_prefrence()[str(element.quality)])
            dl_srcs.append(dl_options[3])

    if stdout:
        
        for dl_src in dl_srcs:
            print(dl_src.link)

    elif watch:
        import tkvlc

        dl_src = dl_srcs[0]
        window_title = " ".join(dl_src.fileName.split("-")[:-1]).title() + " - " + str(dl_src.quality) + "p"
        player = tkvlc.Player(dl_src.link, title=window_title)
        player.start()

    else:
        for dl_src in dl_srcs:
            download(dl_src)


def set_quality(dl_options,dl_options_len):
    if dl_options_len == 1:
        print("Only Found 1 Quality Option, Ignoring --manual-quality")                

        return dl_options[0],0        
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
        return dl_options[choice - 1] , choice - 1


def download(dl_src: str) -> None:
    print(f"\nDownloading \"{dl_src.fileName}\"... ")
    downloader = SmartDL(urls=dl_src.link, dest=f"./{dl_src.fileName}")

    try:
        downloader.start(blocking=True)
    except KeyboardInterrupt:
        downloader.stop()
        raise InterruptedError("Download Stopped!")

def get_quality_prefrence() -> str:
    return __get_from_config("quality")

def get_mirror() -> str:
    return __get_from_config("mirror")

def __get_from_config(key: str) -> str:
    value = ""
    try:
        try:
            file = open(CONFIG_FILE, "r").read()

        except Exception as exception:
            if not os.path.isdir(CONFIG_DIR):
                os.mkdir(CONFIG_DIR)
            
            if not os.path.isdir(EGYBEST_DIR):
                os.mkdir(EGYBEST_DIR)
            
            if not os.path.isfile(CONFIG_FILE):
                with open(CONFIG_FILE, "w") as file:
                    file.write(DEFAULT_CONFIG)
            
            file = open(CONFIG_FILE, "r").read()

        finally:
            value = json.loads(file)[key]
    
    except:
        value = json.loads(DEFAULT_CONFIG)[key]
    
    finally:
        return value


if __name__ == "__main__":

    try:
        egybest(prog_name="egybest")
    
    except Exception as exception:
        print(exception)
    
    except KeyboardInterrupt:
        print("Aborted!")