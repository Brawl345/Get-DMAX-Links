# Get DMAX Links

[![Build](https://github.com/Brawl345/Get-DMAX-Links/actions/workflows/build.yml/badge.svg)](https://github.com/Brawl345/Get-DMAX-Links/actions/workflows/build.yml)

This handy program gets links of a show from Discovery. You can also specify a season with `-s` and an episode with `-e`
.

The resulting information will be saved in an Excel file.

Check the `python` branch for the Python version if you prefer that. The current Go version is much faster though.

## Supported sites

* DMAX.de (dmaxde, default)
* de.hgtv.com (hgtv)
* TLC.de (tlcde)

Specify the shortcode ("realm") with `-r`.

## Usage

1. Navigate to "[Releases](https://github.com/Brawl345/Get-DMAX-Links/releases)"
2. Download the binary for your system
3. Use it: `get-dmax-links SHOWID [-s SEASON] [-e EPISODE] [-r REALM]`
   1. To get the show id, click one of these links, search for the show and copy the "showId" value:
      - DMAX: https://de-api.loma-cms.com/feloma/page/sendungen/?environment=dmax&v=2
      - TLC: https://de-api.loma-cms.com/feloma/page/sendungen/?environment=tlc&v=2
      - HGTV: https://de-api.loma-cms.com/feloma/page/sendungen/?environment=hgtv&v=2
   2. For realms, see the supported sites above. Default is DMAX.de (dmaxde).
4. Check help with `get-dmax-links --help`

## How it works

1. Contacts Discovery API to get tokens and show + video data
2. Sends token and video id(s) to the player API which returns the link(s)

![Screenshot](./screenshot.png?raw=true)
