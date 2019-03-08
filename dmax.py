#!/usr/bin/env python3
import argparse
import logging
import os

import xlsxwriter
from requests import get

import formats

logger = logging.getLogger("DMAX")
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel('WARNING')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.dmax.de/"
API_URL = BASE_URL + "api/show-detail/{0}"
PLAYER_URL = "https://sonic-eu1-prod.disco-api.com/playback/videoPlaybackInfo/"
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"


class WorkbookWriter:
    """Wrapper around xlswriter."""

    def __init__(self, filename):
        """
        Initializes the WorkookWriter class
        :param filename: Name of XLS file
        """
        self.workbook = xlsxwriter.Workbook(filename)
        self.worksheet = self.workbook.add_worksheet()
        self.bold = self.workbook.add_format({'bold': True})
        self.row = 0
        self._col = 0
        self.write_header()

    def col(self, start=False):
        """Returns the current column and moves to the next.
           If start is True, it will move back to 0.
        """
        curcol = self._col
        if start:
            self._col = 0
        else:
            self._col += 1
        return curcol

    def write_header(self):
        self.worksheet.write(self.row, self.col(), "Name", self.bold)
        self.worksheet.write(self.row, self.col(), "Description", self.bold)
        self.worksheet.write(self.row, self.col(), "File name", self.bold)
        self.worksheet.write(self.row, self.col(), "Link", self.bold)
        self.worksheet.write(self.row, self.col(start=True), "Command", self.bold)
        self.row += 1

    def __del__(self):
        self.workbook.close()


def main(showid, chosen_season=0, chosen_episode=0, includespecials=False):
    if chosen_episode < 0 or chosen_season < 0:
        print("ERROR: Episode/Season must be > 0.")
        return
    if chosen_episode > 0 and chosen_season == 0:
        print("ERROR: Season must be set.")
        return

    logger.info("Getting show data")
    try:
        req = get(API_URL.format(showid))
    except Exception as e:
        logger.critical("Connection error: {0}".format(str(e)))
        return

    if req.status_code != 200:
        logger.error("This show does not exist.")
        return

    data = req.json()
    if "errors" in data:
        logger.error("This show does not exist.")
        return

    cookies = req.cookies.get_dict()
    if "sonicToken" not in cookies:
        logger.error("No sonicToken found, can not proceed")
        return
    token = cookies["sonicToken"]
    show = formats.DMAX(data)

    episodes = []
    if includespecials:
        for special in show.specials:
            episodes.append(special)

    if chosen_season == 0 and chosen_episode == 0:  # Get EVERYTHING
        for season in show.seasons:
            for episode in season.episodes:
                episodes.append(episode)
    elif chosen_season > 0 and chosen_episode == 0:  # Get whole season
        for season in show.seasons:
            if season.number == chosen_season:
                for episode in season.episodes:
                    episodes.append(episode)
        if not episodes:
            logger.error("This season does not exist.")
            return
    else:  # Get single episode
        for season in show.seasons:
            if season.number == chosen_season:
                for episode in season.episodes:
                    if episode.episodeNumber == chosen_episode:
                        episodes.append(episode)
        if not episodes:
            logger.error("Episode not found.")
            return

    if not episodes:
        logger.info("No Episodes to download.")
        return

    xlsname = "{0}.xlsx".format(showid)
    file_num = 0
    while os.path.isfile(xlsname):
        file_num += 1
        xlsname = "{0}-{1}.xlsx".format(showid, file_num)
    xls = WorkbookWriter(xlsname)

    for num, episode in enumerate(episodes):
        logger.info("Getting link {0} of {1}".format(num + 1, len(episodes)))
        if episode.season == "" and episode.episode == "":
            filename = "{show_name} - {episode_name}".format(
                show_name=show.show.name,
                episode_name=episode.name
            )
        elif episode.season == "" and episode.episode != "":
            filename = "{show_name} - S{season}E{episode} - {episode_name}".format(
                show_name=show.show.name,
                season=episode.season,
                episode=episode.episode,
                episode_name=episode.name
            )
        else:
            filename = "{show_name} - S{season}E{episode} - {episode_name}".format(
                show_name=show.show.name,
                season=episode.season,
                episode=episode.episode,
                episode_name=episode.name
            )
        xls.worksheet.write(xls.row, xls.col(), episode.name)
        xls.worksheet.write(xls.row, xls.col(), episode.description)
        xls.worksheet.write(xls.row, xls.col(), filename)

        try:
            req = get(PLAYER_URL + episode.id, headers={
                "Authorization": "Bearer " + token,
                "User-Agent": USER_AGENT
            })
        except Exception as exception:
            logger.error("Connection for video id {0} failed: {1}".format(episode.id, str(exception)))
            xls.row += 1
            xls._col = 0
            continue

        if req.status_code != 200:
            logger.error("HTTP error code {0} for video id {1]".format(req.status_code, episode.id))
            xls.row += 1
            xls._col = 0
            continue

        data = req.json()
        video_link = data["data"]["attributes"]["streaming"]["hls"]["url"]
        xls.worksheet.write(xls.row, xls.col(), video_link)
        xls.worksheet.write(xls.row, xls.col(start=True),
                            "youtube-dl \"{0}\" -o \"{1}.mp4\"".format(video_link, filename)
                            )

        xls.row += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gets direct links for DMAX series")
    parser.add_argument(
        "alternateId",
        type=str,
        help="alternateId of the series (last part of URL)"
    )
    parser.add_argument(
        "-s",
        metavar="Season",
        type=int,
        default=0,
        dest="season",
        help="Season to get (default: 0 = all)"
    )
    parser.add_argument(
        "-e",
        metavar="Episode",
        type=int,
        default=0,
        dest="episode",
        help="Episode of season to get (default: 0 = all) - season MUST be set!"
    )
    parser.add_argument(
        '--specials',
        action='store_true',
        default=False,
        dest='includespecials',
        help='Download specials'
    )
    arguments = parser.parse_args()
    main(
        showid=arguments.alternateId,
        chosen_season=arguments.season,
        chosen_episode=arguments.episode,
        includespecials=arguments.includespecials
    )
