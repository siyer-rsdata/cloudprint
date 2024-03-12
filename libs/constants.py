from dotenv import load_dotenv
import os


def get_constant(constant: str):
    return os.getenv(constant)


class Environment(object):
    _self = None

    def __new__(cls):
        # Create an instance of this class only if it does not already exist.
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self):

        # This requires setting the "CLOUD_PRINTER_ENV" environment variable to "dev" or "prod",
        # the conf filename takes the form: .env_constants.<environment>
        # Load the .env_constants.{CLOUD_PRINTER_ENV} config file
        # Add the .env_constants file specific to the environment inside the conf folder
        env = os.getenv('CLOUD_PRINTER_ENV')

        # Get the absolute path of this directory containing this script.
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Specify the path to .env file inside the conf folder
        env_path = os.path.join(os.path.dirname(current_dir), 'conf',  f'.env_constants.{env}')

        # Load environment variables from the .env file into the OS.
        load_dotenv(dotenv_path=env_path)
