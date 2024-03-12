import os.path
import subprocess
import logging

from libs.constants import get_constant

logger = logging.getLogger(__name__)


def create_cp_order(tmp_file: str, cp_file: str) -> str:
    command = [
        get_constant("CPUTIL_LOCATION"),
        "decode",
        get_constant("CPUTIL_OUTPUT_FORMAT"),
        tmp_file,
        cp_file
    ]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Per Subprocess documentation:
        # Typically, an exit status of 0 for returncode indicates that subprocess ran successfully.
        # We are performing an additional check whether the cp file exists.
        if result.returncode == 0 and os.path.exists(cp_file):
            logger.info(f"cp file: {cp_file} successfully created.")

            return cp_file

    except subprocess.CalledProcessError as e:
        logger.error("Error executing CPUtil command:", e)
