#!/usr/bin/env python3

# TODO:
# - Set sonicToken in a config file
# - If 400 -> new token
import argparse
import logging
import sys
from os.path import exists

import xlsxwriter
from requests import get

logger = logging.getLogger("DMAX")
logging.getLogger('requests.packages.urllib3.connectionpool').setLevel('WARNING')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description="Gets direct links for DMAX series")
parser.add_argument("alternateId", type=str, help="alternateId of the series (last part of URL)")
parser.add_argument("-s", metavar="Season", type=int, default=0, help="Season to get (default: 0 = all)")
parser.add_argument("-e", metavar="Episode", type=int, default=0,
                    help="Episode of season to get (default: 0 = all) - season MUST be set!")

base_url = "https://www.dmax.de/"
player_url = "https://sonic-eu1-prod.disco-api.com/playback/videoPlaybackInfo/"


def get_sonic_token():
    logger.info("Getting sonicToken")
    try:
        req = get(base_url)
    except Exception as exception:
        logger.critical("Connection error: " + str(exception))
        return None

    cookies = req.cookies.get_dict()
    if "sonicToken" not in cookies:
        logger.error("No sonicToken found, can not proceed")
        return None
    return cookies["sonicToken"]


def get_dmax_ids(alternate_id, season, episode):
    if season == 0 and episode > 0:
        logger.critical("No season set, can not proceed.")
        return None
    series_url = base_url + "api/show-detail/" + alternate_id
    logger.info("Contacting " + series_url)
    try:
        req = get(series_url)
    except Exception as exception:
        logger.critical("Connection error: " + str(exception))
        return None

    if req.status_code != 200:
        logger.error("HTTP error code " + str(req.status_code))
        return None

    data = req.json()
    episode_data = data["videos"]["episode"]

    video_data = []

    if season == 0 and episode == 0:  # Get EVERYTHING
        logger.info("Getting video ids of every epsiode from every season")
        for s in episode_data:
            for e in episode_data[s]:
                episode_dict = dict()
                episode_dict["id"] = e["id"]
                episode_dict["name"] = e["name"]
                episode_dict["description"] = e["description"]
                episode_dict["season"] = e["seasonNumber"]
                episode_dict["episode"] = e["episodeNumber"]
                episode_dict["prettyName"] = "{show_name} - S{season}E{episode} - {episode_name}".format(
                    show_name=data["show"]["name"],
                    season=e["season"],
                    episode=e["episode"],
                    episode_name=e["name"]
                )
                video_data.append(episode_dict)
    elif season > 0 and episode == 0:  # Get the whole season
        logger.info("Getting video ids of every episode from season " + str(season))
        try:
            for e in episode_data[str(season)]:
                episode_dict = dict()
                episode_dict["id"] = e["id"]
                episode_dict["name"] = e["name"]
                episode_dict["description"] = e["description"]
                episode_dict["season"] = e["seasonNumber"]
                episode_dict["episode"] = e["episodeNumber"]
                episode_dict["prettyName"] = "{show_name} - S{season}E{episode} - {episode_name}".format(
                    show_name=data["show"]["name"],
                    season=e["season"],
                    episode=e["episode"],
                    episode_name=e["name"]
                )
                video_data.append(episode_dict)
        except KeyError:
            logger.error("Season does not exist!")
            return None
    else:  # Get single episode from season
        logger.info("Getting video id of episode " + str(episode) + " from season " + str(season))
        episode_dict = dict()
        try:
            s = episode_data[str(season)]
        except KeyError:
            logger.error("Season does not exist!")
            return None
        for e in s:  # Search every episode in season for given episode number
            if e["episodeNumber"] == episode:
                episode_dict["id"] = e["id"]
                episode_dict["name"] = e["name"]
                episode_dict["description"] = e["description"]
                episode_dict["season"] = e["seasonNumber"]
                episode_dict["episode"] = e["episodeNumber"]
                episode_dict["prettyName"] = "{show_name} - S{season}E{episode} - {episode_name}".format(
                    show_name=data["show"]["name"],
                    season=e["season"],
                    episode=e["episode"],
                    episode_name=e["name"]
                )
                video_data.append(episode_dict)
        if not episode_dict:
            logger.error("Episode not found!")
            return None

    return video_data


def get_dmax_links(token, video_data):
    logger.info("Getting links of episodes, this can take a while!")
    filename = args.alternateId + ".xlsx"
    if exists(filename):
        file_num = 1
        filename = args.alternateId + "-1.xlsx"
        if exists(filename):
            while exists(args.alternateId + "-" + str(file_num) + ".xlsx"):
                file_num += 1
                filename = args.alternateId + "-" + str(file_num) + ".xlsx"
    logger.info("Saving to " + filename)
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    worksheet.write(0, 0, "Name", bold)
    worksheet.write(0, 1, "Description", bold)
    worksheet.write(0, 2, "File name", bold)
    worksheet.write(0, 3, "Link", bold)
    worksheet.write(0, 4, "Command", bold)
    row = 1
    col = 0
    for n, episode in enumerate(video_data):
        logger.info("Getting link " + str(n + 1) + " of " + str(len(video_data)))
        video_id = episode["id"]
        try:
            req = get(player_url + str(video_id), headers={
                "Authorization": "Bearer " + token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0"
            })
        except Exception as exception:
            logger.error("Connection for video id " + str(video_id) + " error: " + str(exception))
            continue

        if req.status_code != 200:
            logger.error("HTTP error code " + str(req.status_code) + "for video id " + str(video_id))
            continue

        data = req.json()
        dl_link = data["data"]["attributes"]["streaming"]["hls"]["url"]

        table_data = (
            [episode["name"], dl_link],
        )
        worksheet.write(row, col, episode["name"])
        worksheet.write(row, col + 1, episode["description"])
        worksheet.write(row, col + 2, episode["prettyName"])
        worksheet.write(row, col + 3, dl_link)
        worksheet.write(row, col + 4, "youtube-dl \"" + dl_link + "\" -o \"" + episode["prettyName"] + ".mp4\"")
        row = row + 1

    workbook.close()


if __name__ == '__main__':
    args = parser.parse_args()
    sonic_token = get_sonic_token()
    if not sonic_token:
        sys.exit(1)
    vid_data = get_dmax_ids(args.alternateId, args.s, args.e)
    if not vid_data:
        sys.exit(1)
    get_dmax_links(sonic_token, vid_data)
