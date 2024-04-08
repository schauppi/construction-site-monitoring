from src.logging.logging_config import setup_logging

import logging
import os

setup_logging()
logger = logging.getLogger()

def get_latest_image(save_path: str, cam: str) -> str:
    """
    Get the path of the latest image in the specified directory.

    Args:
        save_path (str): The directory path where the images are saved.
        cam (str): The camera identifier.

    Returns:
        str: The path of the latest image.
    """
    try:
        images = os.listdir(save_path + cam)
        images.sort()
        latest_image = images[-1]
        latest_image_path = os.path.join(save_path + cam, latest_image)
        return latest_image_path
    except FileNotFoundError:
        logger.error(f"Directory '{save_path + cam}' does not exist.")
        raise
    except IndexError:
        logger.error(f"No images found in directory '{save_path + cam}'.")
        raise
