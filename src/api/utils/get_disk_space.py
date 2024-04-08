from src.logging.logging_config import setup_logging

import logging
import shutil

setup_logging()
logger = logging.getLogger()

def get_disk_space(path:str) -> tuple:
    """
    Get the disk space information for the specified path.

    Args:
        path (str): The path for which to get the disk space information.

    Returns:
        tuple: A tuple containing the total, used, and free space in bytes.
    """
    try:
        total, used, free = shutil.disk_usage(path)
        
        logger.info(f"Disk space information for path {path}:")
        logger.info(f"Total space: {total} bytes")
        logger.info(f"Used space: {used} bytes")
        logger.info(f"Free space: {free} bytes")
        
        return total, used, free
    
    except Exception as e:
    
        logger.error(f"An error occurred while getting disk space: {str(e)}")
        raise
