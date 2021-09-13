import os
import sys
from dotenv import load_dotenv

APP_NAME = 'race_manager'
APP_TYPE_ENTRY = 'entry'
APP_TYPE_DISPLAY = 'display'

BASE_DIR = os.getcwd()
ENV_VARS = {}

VALUE_NO_WINNER = 0
VALUE_LEFT_WINNER = 1
VALUE_RIGHT_WINNER = 2
VALUE_BOTH_WINNER = 3


def load_data():
    env_var_file = os.path.join(os.getcwd(), 'data', APP_NAME + '.cfg')
    if os.path.exists(env_var_file) is False:
        with open(env_var_file, 'w') as CFG_FH:
            CFG_FH.write("""DISPLAY_HEIGHT=500
MAX_RACE_COUNT=50
""")
        print(f"Generating configuration file '{env_var_file}'")

    load_dotenv(env_var_file)

    ENV_VARS['BASE_DIR'] = os.getcwd()
    ENV_VARS['DATA_DIR'] = os.path.join(ENV_VARS['BASE_DIR'], 'data')
    ENV_VARS['LOG_DIR'] = os.path.join(ENV_VARS['DATA_DIR'], 'logs')
    ENV_VARS['LOG_FILE'] = os.path.join(ENV_VARS['LOG_DIR'], f"{APP_NAME}.log")
    ENV_VARS['DISPLAY_HEIGHT'] = os.environ.get('DISPLAY_HEIGHT')
    ENV_VARS['MAX_RACE_COUNT'] = int(os.environ.get('MAX_RACE_COUNT'))


load_data()
