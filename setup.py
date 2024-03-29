from libs.constants import Environment
from libs.auth import Auth

import logging
import os


def init():
    # Initialize the environment, load all the constants into the OS.
    Environment()

    # Initialize Authorization
    Auth()

    # Configure logging
    logging.basicConfig(
        # Specify the file to which logs will be written
        filename=os.getenv('CLOUDPRINT_LOG'),

        # Set the logging level to DEBUG to capture all levels of messages
        level=logging.DEBUG,

        # Specify the log message format
        format='%(levelname)s - %(message)s'
    )

    # Create folder to save logs
    create_folder("logs")

    # Create folder to save temporary .stm and .cp files for each order that is to be sent to the printer.
    create_folder("tmp")


def create_folder(folder_name: str):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        logging.info(f"Folder:{folder_name} created successfully.")
    else:
        logging.info(f"Folder:{folder_name} already exists.")

