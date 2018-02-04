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
1. Contacts dmax.de and gets sonicToken from cookie
2. Contacts DMAX api and gets video id(s)
3. Sends sonicToken and video id(s) to the player API which returns the link(s)

## TODO
- [ ] Save token in config
- [ ] Specials ("standalone", e.g. https://www.dmax.de/api/show-detail/die-aquarium-profis)

![Screenshot](https://raw.githubusercontent.com/Brawl345/Get-DMAX-Links/master/screenshot.png)
