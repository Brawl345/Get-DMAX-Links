#!/usr/bin/env python3
from datetime import datetime, timedelta


class Image:
    """Defines information about an image"""

    def __init__(self, json):
        """
        Initializes the Image class with information for an image
        :param json: String. Raw JSON
        """

        self.height = json["height"]
        self.width = json["width"]
        self.src = json["src"]


class Show:
    """Defines information about a DMAX show"""

    def __init__(self, json):
        """
        Initializes the Show class with information for a show
        :param json: String. Raw JSON
        """

        self.id = json["id"]
        self.alternateId = json["alternateId"]
        self.name = json["name"]

        if "description" in json:
            self.description = json["description"]

        if "episodeCount" in json:
            self.episodeCount = json["episodeCount"]

        if "seasonNumbers" in json:
            self.seasonNumbers = json["seasonNumbers"]

        if "image" in json:
            self.image = Image(json["image"])


class Episode:
    """Defines information about an episode"""

    def __init__(self, json):
        """
        Initializes the Episode class with information for an episode
        :param json: String. Raw JSON
        """

        self.id = json["id"]
        self.alternateId = json["alternateId"]

        if "airDate" in json:
            self.airDate = datetime.strptime(json["airDate"], '%Y-%m-%dT%H:%M:%SZ')

        if "name" in json:
            self.name = json["name"]

        if "title" in json:
            self.title = json["title"]

        if "description" in json:
            self.description = json["description"]

        if "episode" in json:
            self.episode = json["episode"]

        if "episodeNumber" in json:
            self.episodeNumber = json["episodeNumber"]
        else:
            self.episodeNumber = None

        if "season" in json:
            self.season = json["season"]

        if "seasonNumber" in json:
            self.seasonNumber = json["seasonNumber"]
        else:
            self.seasonNumber = None

        if "publishStart" in json:
            self.publishStart = datetime.strptime(json["publishStart"], '%Y-%m-%dT%H:%M:%SZ')

        if "publishEnd" in json:
            self.publishEnd = datetime.strptime(json["publishEnd"], '%Y-%m-%dT%H:%M:%SZ')

        if "videoDuration" in json:
            self.videoDuration = timedelta(milliseconds=json["videoDuration"])

        if "isFreePlayable" in json:
            self.isFreePlayable = json["isFreePlayable"]

        if "isPlayable" in json:
            self.isPlayable = json["isPlayable"]

        if "isNew" in json:
            self.isNew = json["isNew"]

        if "image" in json:
            self.image = Image(json["image"])

    def __repr__(self):
        return "Episode {0}: {1}".format(
            self.episodeNumber if hasattr(self, "episodeNumber") else "?",
            self.name
        )


class Season:
    """Defines information about a season"""

    def __init__(self, number, json):
        """
        Initializes the Season class with information for a season
        :param number: Int. Season Number
        :param json: String. Raw JSON
        """

        self.number = number
        self.episodes = []
        for episode in json:
            self.episodes.append(Episode(episode))

    def __repr__(self):
        return "Season {0}".format(self.number)


class DMAX:
    """Main class for Show and Episode classes"""

    def __init__(self, json):
        """
        Initializes the DMAX class
        :param json: String. Raw JSON
        """

        if "show" not in json or "videos" not in json:
            raise Exception("Invalid JSON.")

        self.show = Show(json["show"])
        self.seasons = []
        for seasonNumber in self.show.seasonNumbers:
            try:
                season_json = json["videos"]["episode"][str(seasonNumber)]
            except KeyError:
                continue
            self.seasons.append(Season(seasonNumber, season_json))

        self.specials = []
        if "standalone" in json["videos"]:
            for special in json["videos"]["standalone"]:
                self.specials.append(Episode(special))
