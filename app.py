import os
import sys
import click
import logging
from app_code.common import config_data as cd
from app_code.common import web_logic as wl
from app_code.common import app_logging as al
from app_code.common import db_data as dbd
from app_code.common import db_custom_def as dbcd
from app_code.common import web_server as ws
import app_code.dash_apps.app_layouts as ala
import app_code.dash_apps.app_race_entry as are
import app_code.dash_apps.app_race_manager as arm
import app_code.dash_apps.app_buy_back as abb
import app_code.dash_apps.app_race_results as arr
import app_code.common.race_logic as rl
import webbrowser

LOGGER = logging.getLogger(al.LOGGER_NAME)


@click.command()
@click.option('--init_db', is_flag=True, default=False)
@click.option('--list_races', is_flag=True, default=False)
@click.option('--list_race')
@click.option('--shuffle_race')
def start_app(**kwargs):
    debug = False
    al.init_logging()

    process_cli_args(**kwargs)

    LOGGER.info("Start (%s)", os.getcwd())
    server = wl.DASH_APP.server

    rl.display_loaded_data()

    if debug is True:
        LOGGER.info("Start Dash Debug Server")
        wl.DASH_APP.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=True, port=8080)
    else:
        LOGGER.info("Start Cheroot Web Server and Web Browser (%s)", cd.ENV_VARS['IP_ADDRESS'])
        webbrowser.open(f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080")
        ws.run_web_server(server)


def process_cli_args(**kwargs):
    if kwargs.get('init_db', False) is True:
        rl.load_config_data()
        sys.exit(0)

    if kwargs.get('list_races', False) is True:
        rl.list_race()
        sys.exit(0)

    list_race_id = kwargs.get('list_race', -1)
    if list_race_id is not None and int(list_race_id) > -1:
        rl.display_race(int(kwargs.get('list_race')))
        sys.exit(0)

    shuffle_race_id = kwargs.get('shuffle_race', -1)
    if shuffle_race_id is not None and int(kwargs.get('shuffle_race', -1)) > -1:
        rl.shuffle_race(int(kwargs.get('shuffle_race')))
        sys.exit(0)


if __name__ == '__main__':
    start_app()


