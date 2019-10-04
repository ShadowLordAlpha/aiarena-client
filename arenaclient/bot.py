import hashlib
import json
import logging
import os
import stat
import zipfile

import requests

from arenaclient.utl import Utl


class Bot:
    """
    Class for setting up the config for a bot.
    """

    def __init__(self, config, data):
        self._config = config

        self._logger = logging.getLogger(__name__)
        self._logger.addHandler(self._config.LOGGING_HANDLER)
        self._logger.setLevel(self._config.LOGGING_LEVEL)

        self._utl = Utl(self._config)

        self.id = data["id"]
        self.name = data["name"]
        self.game_display_id = data["game_display_id"]
        self.bot_zip = data["bot_zip"]
        self.bot_zip_md5hash = data["bot_zip_md5hash"]
        self.bot_data = data["bot_data"]
        self.bot_data_md5hash = data["bot_data_md5hash"]
        self.plays_race = data["plays_race"]
        self.type = data["type"]

    def get_bot_file(self):
        """
        Download the bot's folder and extracts it to a specified location.

        :return: bool
        """
        self._utl.printout(f"Downloading bot {self.name}")
        # Download bot and save to .zip
        r = requests.get(
            self.bot_zip, headers={"Authorization": "Token " + self._config.API_TOKEN}
        )
        bot_download_path = os.path.join(self._config.TEMP_PATH, self.name + ".zip")
        with open(bot_download_path, "wb") as bot_zip:
            bot_zip.write(r.content)
        # Load bot from .zip to calculate md5
        with open(bot_download_path, "rb") as bot_zip:
            calculated_md5 = hashlib.md5(self._utl.file_as_bytes(bot_zip)).hexdigest()
        if self.bot_zip_md5hash == calculated_md5:
            self._utl.printout("MD5 hash matches transferred file...")
            self._utl.printout(f"Extracting bot {self.name} to bots/{self.name}")
            # Extract to bot folder
            with zipfile.ZipFile(bot_download_path, "r") as zip_ref:
                zip_ref.extractall(f"bots/{self.name}")

            # if it's a linux bot, we need to add execute permissions
            if self.type == "cpplinux":
                # Chmod 744: rwxr--r--
                os.chmod(
                    f"bots/{self.name}/{self.name}",
                    stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH,
                )

            if self.get_bot_data_file():
                return True
            else:
                return False
        else:
            self._utl.printout(
                f"MD5 hash ({self.bot_zip_md5hash}) does not match transferred file ({calculated_md5})"
            )
            return False

    # Get bot data
    def get_bot_data_file(self):
        """
        Download bot's personal data folder and extract to specified location.

        :return: bool
        """
        if self.bot_data is None:
            return True

        self._utl.printout(f"Downloading bot data for {self.name}")
        # Download bot data and save to .zip
        r = requests.get(
            self.bot_data, headers={"Authorization": "Token " + self._config.API_TOKEN}
        )
        bot_data_path = os.path.join(self._config.TEMP_PATH, self.name + "-data.zip")
        with open(bot_data_path, "wb") as bot_data_zip:
            bot_data_zip.write(r.content)
        with open(bot_data_path, "rb") as bot_data_zip:
            calculated_md5 = hashlib.md5(self._utl.file_as_bytes(bot_data_zip)).hexdigest()
        if self.bot_data_md5hash == calculated_md5:
            self._utl.printout("MD5 hash matches transferred file...")
            self._utl.printout(f"Extracting data for {self.name} to bots/{self.name}/data")
            with zipfile.ZipFile(bot_data_path, "r") as zip_ref:
                zip_ref.extractall(f"bots/{self.name}/data")
            return True
        else:
            self._utl.printout(
                f"MD5 hash ({self.bot_data_md5hash}) does not match transferred file ({calculated_md5})"
            )
            return False

    def get_bot_data(self):
        """
        Get the bot's config from the ai-arena website and returns a config dictionary.

        :return: bot_name
        :return: bot_data
        """
        bot_name = self.name
        bot_race = self.plays_race
        bot_type = self.type
        bot_id = self.game_display_id

        race_map = {"P": "Protoss", "T": "Terran", "Z": "Zerg", "R": "Random"}
        bot_type_map = {
            "python": ["run.py", "Python"],
            "cppwin32": [f"{bot_name}.exe", "Wine"],
            "cpplinux": [f"{bot_name}", "BinaryCpp"],
            "dotnetcore": [f"{bot_name}.dll", "DotNetCore"],
            "java": [f"{bot_name}.jar", "Java"],
            "nodejs": ["main.jar", "NodeJS"],
        }

        bot_data = {
            "Race": race_map[bot_race],
            "RootPath": os.path.join(self._config.BOTS_DIRECTORY, bot_name),
            "FileName": bot_type_map[bot_type][0],
            "Type": bot_type_map[bot_type][1],
            "botID": bot_id,
        }
        return bot_name, bot_data

    def get_ladder_bots_data(self):
        """
        Get the config file (ladderbots.json) from the bot's directory.

        :param bot:
        :return:
        """
        bot_directory = os.path.join(self._config.BOTS_DIRECTORY, self, "ladderbots.json")
        with open(bot_directory, "r") as ladder_bots_file:
            json_object = json.load(ladder_bots_file)
        return self, json_object

