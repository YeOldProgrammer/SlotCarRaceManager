import sys
import json
import logging
from flask_sqlalchemy import SQLAlchemy
from app_code.common import config_data as cd, web_logic as wl, app_logging as al

LOGGER = logging.getLogger(al.LOGGER_NAME)


DB_DATA = {'DB': None, 'DB_ENGINES': {}}
APP_DB = 'app_db'


def get_db_engine(connection):
    if len(DB_DATA['DB_ENGINES']) == 0:
        return None

    if connection not in DB_DATA['DB_ENGINES']:
        raise ValueError("Invalid DB Name '%s' - valid values [%s]" %
                         (connection, ', '.join(list(DB_DATA['DB_ENGINES'].keys()))))

    engine = DB_DATA['DB'].get_engine(bind=connection)
    return engine


def init_db_app():
    wl.FLASK_APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    wl.FLASK_APP.config['SQLALCHEMY_BINDS'] = DB_DATA['DB_ENGINES']

    if len(DB_DATA['DB_ENGINES']) == 0:
        LOGGER.warning("Init DB App - no databased configured")
        return None

    try:
        DB_DATA['DB'] = SQLAlchemy(wl.FLASK_APP)
    except Exception as error_text:
        LOGGER.error("Failed to establish connection to DB - %s",
                     error_text, exc_info=True)
        sys.exit(1)


def init_db():
    db_name = 'sqlite'
    data_dump = json.dumps(cd.ENV_VARS, indent=4)

    sql_alchemy_db_app_url = f"sqlite:///{cd.ENV_VARS['DATA_DIR']}/{db_name}.db"
    DB_DATA['DB_ENGINES'].clear()
    DB_DATA['DB_ENGINES'][APP_DB] = sql_alchemy_db_app_url
    DB_DATA['DB'] = None
    init_db_app()
    if DB_DATA['DB'] is None:
        LOGGER.error("Failed to init DB")


init_db()
