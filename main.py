import click
import logging
from app_code import config_data as cd
cd.load_data()
from app_code import app_logging as al
from app_code import db_data as dbd
dbd.init_db()
from app_code import db_custom_def as dbcd
dbcd.create_db()
from app_code import web_logic as wl
from app_code import web_server as ws


LOGGER = logging.getLogger(al.LOGGER_NAME)


@click.command()
def start_app():
    debug = False
    al.init_logging()

    LOGGER.info("Start")
    server = wl.DASH_APP.server
    if debug is True:
        wl.DASH_APP.run_server(debug=True, dev_tools_ui=True, dev_tools_props_check=True, port=8080)
    else:
        ws.run_web_server(server)


if __name__ == '__main__':
    start_app()


