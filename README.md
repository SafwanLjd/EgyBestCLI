# EgyBestCLI
This is a simple Command-Line tool that allows you to download media from EgyBest.
You can also use this tool to stream media directly without downloading it using the power of the `--stdout` flag.

_This project depends on the [PyEgyBest](https://github.com/SafwanLjd/PyEgyBest) Library that allows a selenium-less solution to interact with EgyBest_

_Tested on Python versions >= 3.6_



## Installation

### Downloading and Installing The Python Script
```bash
git clone "https://github.com/SafwanLjd/EgyBestCLI.git"
cd EgyBestCLI
pip install -r requirements.txt
python ./egybest-cli.py --help
```

### Downloading The Windows Binary
```bash
curl -o "https://github.com/SafwanLjd/EgyBestCLI/releases/download/1.0/egybest-cli.zip"
tar -xf egybest-cli.zip
cd egybest-cli
./egybest-cli.exe --help 
``` 



## Usage

### What Can This Script Do
* Download A Movie
* Download An Episode of A TV Show
* Download A Whole Season of A TV Show
* Print The Direct Media URL of an Episode/Movie (or All The Episode URLs of A Season, One URL Per Line) to Standard Output So You Can Do Stuff Like Pipe It Into Your Favorite Video Player

### Default Behavior
**The Script by default:**
* Picks the closest result to your search query automatically. You can pick a search result manually using the `--manual-search` flag
* Picks the video quality according to your config file.  You can pick it manually using the `--manual-quality` flag

### Examples
Download The Movie "Back to The Future"
```bash
egybest-cli --title "Back to The Future"
```

Download The First Episode of The First Season of The Show "Game of Thrones"
```bash
egybest-cli --title "Game of Thrones" -S 1 -E 1
```

Download All the Episodes of The Third Season of The Show "Peaky Blinders"
```bash
egybest-cli --title "Peaky Blinders" -S 3
```

Play The Fifth Episode of the Fourth Season of The Show "Mr. Robot" Directly in The MPV Video Player
```bash
mpv $(egybest-cli --title "Mr. Robot" -S 4 -E 5 --stdout)
```



## Configuration

There is a single config file which is `~/.config/egybest-conf.json`
Which is only used for video quality preferences at the moment.
The default file is set to choose the best available quality.

Default File:
```json
{
	"quality": {
		"2160": 1,
		"1080": 2,
		"720":  3,
		"480":  4,
		"360":  5,
		"240":  6
	}
}
```
_Lower Number = Higher Priority_