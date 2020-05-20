#!/usr/bin/env python3
from datetime import datetime, timedelta


class Show:
    """Defines information about a DMAX show"""

    def __init__(self, json):
        """
        Initializes the Show class with information for a show
        :param json: String. Raw JSON
        """

        self.alternateId = json["alternateId"]
        self.name = json["name"]

        if "description" in json:
            self.description = json["description"]

        if "episodeCount" in json:
            self.episodeCount = json["episodeCount"]

        if "seasonNumbers" in json:
            self.seasonNumbers = json["seasonNumbers"]

    def __repr__(self):
        return "DMAX-Show: {0}".format(self.name)


class Episode:
    """Defines information about an episode"""

    def __init__(self, json):
        """
        Initializes the Episode class with information for an episode
        :param json: String. Raw JSON
        """

        self.id = json["id"]
        json = json["attributes"]
        self.alternateId = json["alternateId"]

        if "airDate" in json:
            self.airDate = datetime.strptime(json["airDate"], '%Y-%m-%dT%H:%M:%SZ')

        if "name" in json:
            self.name = json["name"]

        if "description" in json:
            self.description = json["description"]

        if "episodeNumber" in json:
            self.episodeNumber = json["episodeNumber"]
            self.episode = self.episodeNumber
        else:
            self.episodeNumber = None
            self.episode = None

        if "seasonNumber" in json:
            self.seasonNumber = json["seasonNumber"]
            self.season = self.seasonNumber
        else:
            self.seasonNumber = None
            self.season = None

        if "publishStart" in json:
            self.publishStart = datetime.strptime(json["publishStart"], '%Y-%m-%dT%H:%M:%SZ')

        if "publishEnd" in json:
            self.publishEnd = datetime.strptime(json["publishEnd"], '%Y-%m-%dT%H:%M:%SZ')

        if "videoDuration" in json:
            self.videoDuration = timedelta(milliseconds=json["videoDuration"])

        if "drmEnabled" in json:
            self.drmEnabled = json["drmEnabled"]

        if "isNew" in json:
            self.isNew = json["isNew"]

    def __repr__(self):
        return "Episode {0}: {1}".format(
                self.episodeNumber if hasattr(self, "episodeNumber") else "?",
                self.name
        )


class DMAX:
    """Main class for Show and Episode classes"""

    def __init__(self, json):
        """
        Initializes the DMAX class
        :param json: String. Raw JSON
        """

        if "data" not in json or "included" not in json:
            raise Exception("Invalid JSON.")

        self.show = None
        for incl in json["included"]:
            if "type" in incl and incl["type"] == "show":
                self.show = Show(incl["attributes"])
                break

        if not self.show:
            raise Exception("No show data found.")

        self.episodes = []
        for episode in json["data"]:
            self.episodes.append(Episode(episode))
