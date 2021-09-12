import os
import sys
from dotenv import load_dotenv

APP_NAME = 'race_manager'
APP_TYPE_ENTRY = 'entry'
APP_TYPE_DISPLAY = 'display'

BASE_DIR = os.getcwd()
ENV_VARS = {}


def load_data():
    env_var_file = os.path.join(os.getcwd(), 'data', APP_NAME + '.cfg')
    if os.path.exists(env_var_file) is False:
        print(f"Missing configuration file '{env_var_file}'")
        sys.exit(1)

    load_dotenv(env_var_file)

    ENV_VARS['BASE_DIR'] = os.getcwd()
    ENV_VARS['DATA_DIR'] = os.path.join(ENV_VARS['BASE_DIR'], 'data')
    ENV_VARS['LOG_DIR'] = os.path.join(ENV_VARS['DATA_DIR'], 'logs')
    ENV_VARS['LOG_FILE'] = os.path.join(ENV_VARS['LOG_DIR'], f"{APP_NAME}.log")
    ENV_VARS['DISPLAY_HEIGHT'] = os.environ.get('DISPLAY_HEIGHT')
    ENV_VARS['MAX_RACE_COUNT'] = int(os.environ.get('MAX_RACE_COUNT'))


load_data()
