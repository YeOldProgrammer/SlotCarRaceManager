import json
import dash
import time
import logging
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from sqlalchemy import func
from dash.exceptions import PreventUpdate
# import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from app_code.common import app_logging as al
import app_code.common.db_data as dbd
import app_code.common.web_logic as wl
import app_code.common.config_data as cd
import app_code.common.db_custom_def as dcd
from app_code.common.dash_util import dash_kwarg
import app_code.common.race_logic as rl
import app_code.dash_apps.app_layouts as ala

LOGGER = logging.getLogger(al.LOGGER_NAME)

NO_ENTRY_COLOR = 'lightgrey'
inputs = []
outputs = []
BASE_ID = 'arr_'
NEW_RACE_BUTTON = BASE_ID + 'new_race'
DIV_DATA = BASE_ID + '_div_data'
URL_ID = BASE_ID + 'url'


ala.APP_LAYOUTS[ala.APP_RACE_RESULT] = html.Div(
    [
        dcc.Location(id=URL_ID),
        html.Div(
            [
                dbc.Row([
                    dbc.Col([
                        html.H1('Race Results'),
                    ], width='auto'),
                    dbc.Col([
                        html.Img(src=wl.DASH_APP.get_asset_url(cd.ENV_VARS['LOGO_FILE']),
                                 style={'margin-left': '20px'}),
                    ], width='auto'),
                ]),
            ],
            style={'height': '160px'}
            # style={'height': '100px', 'backgroundColor': 'blue', 'height': '100px'}
        ),
        html.Div(
            children=[],
            id=DIV_DATA,
            style={'margin-left': '60px', 'height': f"{cd.ENV_VARS['BODY_DISPLAY_HEIGHT']}px", 'overflow-y': 'scroll',
                   'overflow-x': 'hidden', 'backgroundColor': cd.ENV_VARS['BODY_DISPLAY_COLOR']}
        ),
        html.Div(
            [
                dbc.Button('New Race', id=NEW_RACE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
            ],
            style={'height': '100px'}
            # style={'height': '100px', 'backgroundColor': 'red'}
        ),
    ],
    style={'margin-left': '50px', 'margin-top': '50px'}
)


def parse_url_params_str(url_params_str):
    params = url_params_str.split('?')

    params_dict = {}
    params_dict['url'] = params[0]

    if len(params) > 1:
        tokens = params[1].split('&')
        for token in tokens:
            token_split = token.split('=')
            params_dict[token_split[0]] = token_split[1]

    return params_dict


@wl.DASH_APP.callback(
    Output(DIV_DATA, 'children'),
    Output(URL_ID, 'href'),
    [
        Input(NEW_RACE_BUTTON, "n_clicks"),
        Input(URL_ID, "href"),
    ],

)
def generate_graph(new_race_button, orig_url_params_str):
    cb_start_time = time.time()
    ctx = dash.callback_context

    url_params_dict = parse_url_params_str(orig_url_params_str)
    race_data_obj = rl.RaceData()
    new_url_params_str = dash.no_update

    if 'race_id' not in url_params_dict:
        LOGGER.info("Buy Back - Race_id was not specified")
        new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_entry"
        raise PreventUpdate

    race_id = int(url_params_dict['race_id'])
    new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/buy_back?race_id=%d" % race_id
    race_data_obj.load_cars(race_id=url_params_dict['race_id'], heat_id=1)

    if orig_url_params_str != new_url_params_str:
        LOGGER.info("    URL Change\n        from: %s\n          to: %s", orig_url_params_str, new_url_params_str)

    race_data_obj = rl.RaceData()
    race_data_obj.load_cars(race_id=race_id, heat_id=1)

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == NEW_RACE_BUTTON:
            new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_entry"
            return dash.no_update, new_url_params_str

    race_obj_list = dcd.RaceDb.query. \
        filter_by(race_id=race_id). \
        order_by(dcd.RaceDb.eliminated). \
        all()

    div_data = []
    max_heat = 0
    winner_count = 0
    for race_obj in race_obj_list:
        max_heat = max(race_obj.eliminated, max_heat)
        car_name = race_data_obj.car_id_to_car_name[race_obj.car_id]['car_name']
        driver_name = race_data_obj.car_id_to_car_name[race_obj.car_id]['driver_name']
        value = max_heat - race_obj.eliminated
        if race_obj.eliminated == 0:
            div_data.append(dbc.Row([
                dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url('place_1.png'),
                                 style={'height': '100px', 'width': '100px'}),
                        width='auto'),
                dbc.Col(html.H3(driver_name),
                        width='auto'),
                dbc.Col(html.H4(car_name),
                        width='auto'),
            ], align='center', style={'margin-top': '20px'}))

            winner_count += 1
        elif value <= 1:
            winner_count += 1

    for race_obj in reversed(race_obj_list):
        value = max_heat - race_obj.eliminated
        car_name = race_data_obj.car_id_to_car_name[race_obj.car_id]['car_name']
        driver_name = race_data_obj.car_id_to_car_name[race_obj.car_id]['driver_name']
        if value == 0:
            div_data.append(dbc.Row([
                dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url('place_2.png'),
                                 style={'height': '100px', 'width': '100px'}),
                        width='auto'),
                dbc.Col(html.H3(driver_name),
                        width='auto'),
                dbc.Col(html.H4(car_name),
                        width='auto'),
            ], align='center', style={'margin-top': '20px'}))

        elif value == 1:
            div_data.append(dbc.Row([
                dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url('place_3.png'),
                                 style={'height': '100px', 'width': '100px'}),
                        width='auto'),
                dbc.Col(html.H3(driver_name),
                        width='auto'),
                dbc.Col(html.H4(car_name),
                        width='auto'),
            ], align='center', style={'margin-top': '20px'}))

        elif value == 2 and winner_count < 4:
            div_data.append(dbc.Row([
                dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url('place_4.png'),
                                 style={'height': '100px', 'width': '100px'}),
                        width='auto'),
                dbc.Col(html.H3(driver_name),
                        width='auto'),
                dbc.Col(html.H4(car_name),
                        width='auto'),
            ], align='center', style={'margin-top': '20px'}))

    return div_data, dash.no_update
