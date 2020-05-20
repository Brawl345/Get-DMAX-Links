#!/usr/bin/env python3
import argparse
import logging
import os
import re

import xlsxwriter
from requests import get

import formats

logger = logging.getLogger("DMAX")
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel('WARNING')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

API_BASE = "https://eu1-prod.disco-api.com"
SHOW_INFO_URL = API_BASE + "/content/videos//?include=primaryChannel,primaryChannel.images,show,show.images," \
                           "genres,tags,images,contentPackages&sort=-seasonNumber,-episodeNumber" \
                           "&filter[show.id]={0}&filter[videoType]=EPISODE&page[number]=1&page[size]=100"
PLAYER_URL = "https://sonic-eu1-prod.disco-api.com/playback/videoPlaybackInfo/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0"


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


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


def main(showid, chosen_season=0, chosen_episode=0):
    if chosen_episode < 0 or chosen_season < 0:
        print("ERROR: Episode/Season must be > 0.")
        return
    if chosen_episode > 0 and chosen_season == 0:
        print("ERROR: Season must be set.")
        return

    logger.info("Getting Authorization token...")
    try:
        token = get(API_BASE + "/token?realm=dmaxde").json()["data"]["attributes"]["token"]
    except Exception as e:
        logger.critical("Connection error: {0}".format(str(e)))
        return

    logger.info("Getting show data")
    try:
        req = get(SHOW_INFO_URL.format(showid), headers={"Authorization": "Bearer " + token})
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

    show = formats.DMAX(data)
    logger.info("=> {0}".format(show.show.name))

    episodes = []
    if chosen_season == 0 and chosen_episode == 0:  # Get EVERYTHING
        episodes = show.episodes
    elif chosen_season > 0 and chosen_episode == 0:  # Get whole season
        for episode in show.episodes:
            if episode.seasonNumber == chosen_season:
                episodes.append(episode)
        if not episodes:
            logger.error("This season does not exist.")
            return
    else:  # Get single episode
        for episode in show.episodes:
            if episode.seasonNumber == chosen_season and episode.episodeNumber == chosen_episode:
                episodes.append(episode)
        if not episodes:
            logger.error("Episode not found.")
            return

    if not episodes:
        logger.info("No Episodes to download.")
        return

    xlsname = "{0}.xlsx".format(get_valid_filename(show.show.name))
    file_num = 0
    while os.path.isfile(xlsname):
        file_num += 1
        xlsname = "{0}-{1}.xlsx".format(get_valid_filename(show.show.name), file_num)
    xls = WorkbookWriter(xlsname)

    length = len(episodes)
    for num, episode in enumerate(episodes):
        logger.info("Getting link {0} of {1}".format(num + 1, length))
        if not episode.season and not episode.episode:
            filename = "{show_name} - {episode_name}".format(
                    show_name=show.show.name,
                    episode_name=episode.name
            )
        elif not episode.season and episode.episode:
            filename = "{show_name} - E{episode} - {episode_name}".format(
                    show_name=show.show.name,
                    episode=str(episode.episode).zfill(2),
                    episode_name=episode.name
            )
        else:
            filename = "{show_name} - S{season}E{episode} - {episode_name}".format(
                    show_name=show.show.name,
                    season=str(episode.season).zfill(2),
                    episode=str(episode.episode).zfill(2),
                    episode_name=episode.name
            )
        xls.worksheet.write(xls.row, xls.col(), episode.name)
        xls.worksheet.write(xls.row, xls.col(), episode.description)
        xls.worksheet.write(xls.row, xls.col(), filename)

        try:
            req = get(PLAYER_URL + episode.id, headers={
                "Authorization": "Bearer " + token,
                "User-Agent":    USER_AGENT
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

    logger.info("=> Saved to {0}".format(xlsname))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gets direct links for DMAX series")
    parser.add_argument(
            "showId",
            type=int,
            help="showId of the series (check HTML page code)"
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
    arguments = parser.parse_args()
    main(
            showid=arguments.showId,
            chosen_season=arguments.season,
            chosen_episode=arguments.episode
    )
