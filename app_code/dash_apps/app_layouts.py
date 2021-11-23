import logging
import dash_html_components as html
import app_code.common.web_logic as wl
from dash.dependencies import Input, Output
from app_code.common import app_logging as al

LOGGER = logging.getLogger(al.LOGGER_NAME)


APP_RACE_ENTRY = 'race_entry'
APP_RACE_MANAGER = 'race_manager'
APP_RACE_RESULT = 'race_result'
APP_BUY_BACK = 'buy_back'
APP_LIST = [APP_RACE_ENTRY, APP_RACE_MANAGER, APP_BUY_BACK, APP_RACE_RESULT]
APP_LAYOUTS = {}
for APP in APP_LIST:
    APP_LAYOUTS[APP] = [html.H3("%s layout not defined" % APP)]


@wl.DASH_APP.callback(Output('page-content', 'children'),
                      [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/race_manager':
        wl.DASH_APP.title = "Race Manager"
        return APP_LAYOUTS[APP_RACE_MANAGER]
    elif pathname == '/buy_back':
        wl.DASH_APP.title = "Race Manager"
        return APP_LAYOUTS[APP_BUY_BACK]
    elif pathname == '/race_results':
        wl.DASH_APP.title = "Race Results"
        return APP_LAYOUTS[APP_RACE_RESULT]

    return APP_LAYOUTS[APP_RACE_ENTRY]


@wl.FLASK_APP.route("/")
def update_title_race_entry():
    wl.DASH_APP.title = "Race Entry"
    return wl.DASH_APP.index()


@wl.FLASK_APP.route("/race_manager")
def update_title_race_manager():
    wl.DASH_APP.title = "Race Manager"
    return wl.DASH_APP.index()


@wl.FLASK_APP.route("/race_results")
def update_title_race_results():
    wl.DASH_APP.title = "Race Results"
    return wl.DASH_APP.index()
