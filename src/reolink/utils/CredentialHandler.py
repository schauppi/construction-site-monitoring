import json
import os

class CredentialHandler():
    """
    Class to handle the credentials for the Reolink cameras.

    Methods:
        load_credentials: Load the credentials for the camera.

    """
    def __init__(self) -> None:
        """
        Initialize the CredentialHandler with the path to the credentials file.
        """
        _base_path = os.path.dirname(__file__)
        _credential_path = os.path.join(_base_path, '..', '..', '..', 'reolink_credentials.json')
        self._credential_path = os.path.normpath(_credential_path)

    def load_credentials(self, cam: int):
        """
        Load the credentials for the camera.

        Args:
            cam (int): The camera number.

        Returns:
            tuple: The username, password and ip of the camera.
        """
        try:
            with open(self._credential_path) as file:
                credentials = json.load(file)
        except FileNotFoundError:
            print(f"Credentials file not found: {self._credential_path}")
            return None, None, None
        except Exception as e:
            print(f"Error loading credentials file: {e}")
            return None, None, None

        try:
            cam_credentials = credentials["credentials"][str(cam)]
            username = cam_credentials["username"]
            password = cam_credentials["password"]
            ip = cam_credentials["ip"]

            return username, password, ip
        except KeyError:
            print(f"No credentials found for camera {cam}")
            return None, None, None
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None, None, None