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
import app_code.common.race_logic as rl
import webbrowser

LOGGER = logging.getLogger(al.LOGGER_NAME)


@click.command()
def start_app():
    debug = False
    al.init_logging()

    LOGGER.info("Start")
    server = wl.DASH_APP.server

    rl.load_default_data()

    if debug is True:
        LOGGER.info("Start Dash Debug Server")
        wl.DASH_APP.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=True, port=8080)
    else:
        LOGGER.info("Start Cheroot Web Server and Web Browser")
        webbrowser.open('http://127.0.0.1:8080')
        ws.run_web_server(server)


if __name__ == '__main__':
    start_app()


