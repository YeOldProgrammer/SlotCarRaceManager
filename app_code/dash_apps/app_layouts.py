import logging
import dash_html_components as html
import app_code.common.web_logic as wl
from dash.dependencies import Input, Output
from app_code.common import app_logging as al

LOGGER = logging.getLogger(al.LOGGER_NAME)


APP_RACE_ENTRY = 'race_entry'
APP_RACE_MANAGER = 'race_manager'
APP_LIST = [APP_RACE_ENTRY, APP_RACE_MANAGER]
APP_LAYOUTS = {}
for APP in APP_LIST:
    APP_LAYOUTS[APP] = [html.H3("%s layout not defined" % APP)]


@wl.DASH_APP.callback(Output('page-content', 'children'),
                      [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/race_manager':
        LOGGER.info("Loading Race Manager - %s", pathname)
        return APP_LAYOUTS[APP_RACE_MANAGER]

    LOGGER.info("Loading Race Entry - %s", pathname)
    return APP_LAYOUTS[APP_RACE_ENTRY]
