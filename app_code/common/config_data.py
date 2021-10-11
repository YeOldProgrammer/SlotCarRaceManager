import os
import socket
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
    data_dir = os.path.join(os.getcwd(), 'default_data')
    env_var_file = os.path.join(data_dir, APP_NAME + '.cfg')
    if os.path.exists(env_var_file) is False:
        if os.path.isdir(data_dir) is False:
            os.makedirs(data_dir)

        with open(env_var_file, 'w') as CFG_FH:
            CFG_FH.write("""BODY_DISPLAY_HEIGHT=500
BODY_DISPLAY_COLOR=none
MAX_RACE_COUNT=50
""")
        print(f"Generating configuration file '{env_var_file}'")

    load_dotenv(env_var_file)

    ENV_VARS['BASE_DIR'] = os.getcwd()
    ENV_VARS['DATA_DIR'] = os.path.join(ENV_VARS['BASE_DIR'], 'data')
    ENV_VARS['DEFAULT_DATA_DIR'] = os.path.join(ENV_VARS['BASE_DIR'], 'default_data')
    ENV_VARS['LOG_DIR'] = os.path.join(ENV_VARS['DATA_DIR'], 'logs')
    ENV_VARS['LOG_FILE'] = os.path.join(ENV_VARS['LOG_DIR'], f"{APP_NAME}.log")
    ENV_VARS['BODY_DISPLAY_HEIGHT'] = os.environ.get('BODY_DISPLAY_HEIGHT')
    ENV_VARS['BODY_DISPLAY_COLOR'] = os.environ.get('BODY_DISPLAY_COLOR')
    ENV_VARS['MAX_RACE_COUNT'] = int(os.environ.get('MAX_RACE_COUNT'))
    ENV_VARS['RACE_DURATION_SEC'] = int(os.environ.get('RACE_DURATION_SEC'))
    try:
        ENV_VARS['IP_ADDRESS'] = socket.gethostbyname(socket.gethostname())
    except Exception as error_text:
        print(f"Failed to get local IP address ({error_text})")
    ENV_VARS['IP_ADDRESS'] = '127.0.0.1'

    if os.path.isdir(ENV_VARS['DATA_DIR']) is False:
        print(f"Generating data directory in '{ENV_VARS['DATA_DIR']}'")
        os.makedirs(ENV_VARS['DATA_DIR'])


load_data()
