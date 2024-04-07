from src.logging.logging_config import setup_logging

import json
import os
import logging

class CredentialHandler():
    """
    Class to handle the credentials for the Reolink cameras.

    Methods:
        load_credentials: Load the credentials for the camera.
        url: Get the streaming URL for the camera.

    """
    def __init__(self, cam: int) -> None:
        """
        Initialize the CredentialHandler with the path to the credentials file.
        """
        setup_logging()
        self.logger = logging.getLogger()
        _base_path = os.path.dirname(__file__)
        _credential_path = os.path.join(_base_path, '..', '..', '..', 'reolink_credentials.json')
        self._credential_path = os.path.normpath(_credential_path)
        self.cam = cam

    def load_credentials(self):
        """
        Load the credentials for the camera.

        Returns:
            tuple: The username, password and ip of the camera.
        """
        try:
            with open(self._credential_path) as file:
                credentials = json.load(file)
        except FileNotFoundError:
            self.logger.error(f"Credentials file not found: {self._credential_path}")
            return None, None, None
        except Exception as e:
            self.logger.error(f"Error loading credentials file: {e}")
            return None, None, None

        try:
            cam_credentials = credentials["credentials"][str(self.cam)]
            username = cam_credentials["username"]
            password = cam_credentials["password"]
            ip = cam_credentials["ip"]

            self.logger.info(f"Loaded credentials for camera {self.cam}")
            return username, password, ip
        except KeyError:
            self.logger.error(f"No credentials found for camera {self.cam}")
            return None, None, None
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            return None, None, None

    @property
    def url(self):
        """
        Get the streaming URL for the camera.

        Returns:
            str: The streaming URL for the camera.
        """
        try:
            username, password, ip = self.load_credentials()
            self.logger.info(f"Getting streaming URL for camera {self.cam}")
            return "rtsp://{}:{}@{}:{}".format(username, password, ip, "554//h264Preview_01_sub")
        except Exception as e:
            self.logger.error(f"Error getting streaming URL: {e}")
            return None