Get DMAX Links
==============
This handy python script gets links of a show from Discovery. You can also specify a season with `-s` and an episode with `-e`.

The resulting information will be saved in an Excel file.

## Supported sites
* DMAX.de (dmaxde, default)
* de.hgtv.com (hgtv)
* TLC.de (tlcde)

Specify the shortcode ("realm") with `-r`.

## Usage
1. Clone repo
2. `pip install -U -r requirements.txt`
    1. **NOTE**: On Linux you may have to call `pip3` because the normal pip will use Python 2
3. `python dmax.py SHOWID [--isasset] [-s SEASON] [-e EPISODE] [-r REALM]`
    1. **NOTE**: Same as above - you may need to call `python3` under Linux. This script WON'T work with Python 2!
    2. To get the show id, navigate to the page of the series you want to download, press CTRL+U to open the page source and search for "showid". It's inside a `<hyoga-player>` HTML tag.
    3. If you only find an assetid, just pass `--isasset` to the script and it will extract the showId first
    4. For realms, see the supported sites above. Default is DMAX.de.
4. Check help with `python dmax.py -h`

## How it works
1. Contacts Discovery API to get tokens and show + video data 
2. Sends token and video id(s) to the player API which returns the link(s)

![Screenshot](https://raw.githubusercontent.com/Brawl345/Get-DMAX-Links/master/screenshot.png)
