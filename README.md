Get DMAX Links
==============
This handy python script gets links of a DMAX show. You can also specify a season with `-s` and an episode with `-e`.

The resulting information will be saved in an Excel file.

## Usage
1. Clone repo
2. `pip install -U -r requirements.txt`
3. `python dmax.py NAME-OF-SHOW [-s SEASON] [-e EPISODE]`
4. Check help with `python dmax.py -h`

## How it works
1. Contacts Discovery API to get tokens and show + video data 
2. Sends token and video id(s) to the player API which returns the link(s)

![Screenshot](https://raw.githubusercontent.com/Brawl345/Get-DMAX-Links/master/screenshot.png)
