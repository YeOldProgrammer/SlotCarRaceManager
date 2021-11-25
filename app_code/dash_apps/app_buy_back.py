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
BASE_ID = 'abb_'
CLICK_LEFT = 'left_check'
CLICK_RIGHT = 'right_check'
HEAT_SLIDER = BASE_ID + 'slider'
START_BUTTON = BASE_ID + 'start_heat'
DONE_BUTTON = BASE_ID + 'done_heat'
NEXT_HEAT_BUTTON = BASE_ID + 'next_heat'
RE_SHUFFLE_BUTTON = BASE_ID + 'shuffle'
NEW_RACE_BUTTON = BASE_ID + 'new_race'
REMAINING_PIE_CHART = BASE_ID + "race_remaining_pie_chart"
REMAINING_TIME_CHART = BASE_ID + "time_remaining_pie_chart"
STATS_ROW = BASE_ID + 'stats'
URL_ID = BASE_ID + 'url'
TIMER_TRIGGER = BASE_ID + 'timer_trigger'
BODY_DIV = BASE_ID + 'body_div'
CLIENT_INFO = BASE_ID + 'client_info'


CLIENTSIDE_CALLBACK = """
    function(href) {
        var w = window.innerWidth;
        var h = window.innerHeight;
        return {'height': h, 'width': w};
    }
"""

# LOGGER.error("Init Client Side Callback: app_buy_back")
wl.DASH_APP.clientside_callback(CLIENTSIDE_CALLBACK, Output(CLIENT_INFO, 'children'), Input(URL_ID, 'href'))


def gen_key(race_id):
    key = 'key_%03d' % race_id
    return key


def gen_check_id(race_id):
    key = gen_key(race_id)
    check_id = BASE_ID + key + '_check_value'
    return check_id


def get_run_id(check_id):
    if 'check' not in check_id:
        return -1

    run_id = int(check_id.split('_')[2])
    return run_id


def gen_initial_div_data():
    div_data_output = []

    inputs.append(Input(URL_ID, 'href'))
    inputs.append(Input(DONE_BUTTON, 'n_clicks'))
    outputs.append(Output(URL_ID, 'href'))
    outputs.append(Output(BODY_DIV, 'style'))

    for idx in range(int(cd.ENV_VARS['MAX_RACE_COUNT'] / 2)):
        run_id = idx
        key = gen_key(run_id)
        check_id = gen_check_id(run_id)
        run_row_id = BASE_ID + key + '_race_row'
        driver_id = BASE_ID + key + '_driver_id'
        inputs.append(Input(check_id, 'value'))
        outputs.append(Output(run_row_id, 'style'))
        outputs.append(Output(check_id, 'options'))
        outputs.append(Output(check_id, 'value'))
        outputs.append(Output(driver_id, 'children'))

        div_data_output.append(
            dbc.Row(
                dbc.Col(
                    [
                        html.H4('', id=driver_id),
                        dcc.Checklist(id=check_id,
                                      labelStyle={'display': 'block', 'margin-left': '20px'},
                                      inputStyle={"margin-right": "10px"}
                                      )
                    ],
                    width='auto',
                    style={"border": "2px black solid",
                           'padding': '20px',
                           'margin-left': '20px',
                           'margin-top': '10px'
                           },
                ),
                id=run_row_id,

            )
        )
    inputs.append(Input(CLIENT_INFO, 'children'))
    return div_data_output


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


def build_url_params_str(params_dict):
    url_params_str = ''
    if len(params_dict) > 0:
        for param in params_dict:
            if param == 'url':
                continue

            if url_params_str == '':
                url_params_str += '?'
            else:
                url_params_str += '&'
            url_params_str += param + '=' + str(params_dict[param])
        url_params_str = params_dict.get('url', '') + url_params_str

    return url_params_str


div_data = gen_initial_div_data()
ala.APP_LAYOUTS[ala.APP_BUY_BACK] = html.Div(
    [
        dcc.Location(id=URL_ID),
        html.Div(id=CLIENT_INFO),
        html.Div(
            [
                dbc.Row([
                    dbc.Col([
                        html.H1('Buy Back'),
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
            id=BODY_DIV,
            children=div_data,
            style={'margin-left': '60px', 'height': f"{cd.ENV_VARS['BODY_DISPLAY_HEIGHT']}px", 'overflow-y': 'scroll',
                   'overflow-x': 'hidden', 'backgroundColor': cd.ENV_VARS['BODY_DISPLAY_COLOR']}
        ),
        html.Div(
            [
                dbc.Button('Done', id=DONE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
            ],
            style={'height': '100px'}
            # style={'height': '100px', 'backgroundColor': 'red'}
        ),
    ],
    style={'margin-left': '50px', 'margin-top': '50px'}
)


@wl.DASH_APP.callback(
    outputs,
    inputs,
)
@dash_kwarg(inputs)
def generate_graph(**kwargs):
    cb_start_time = time.time()
    ctx = dash.callback_context

    screen_height = int(cd.ENV_VARS['BODY_DISPLAY_HEIGHT'])
    try:
        if CLIENT_INFO in kwargs:
            screen_height = int(kwargs[CLIENT_INFO]['height'])
            LOGGER.info("Screen:Buy Back: screen_height:%d found", screen_height)
        else:
            LOGGER.warning("Screen:Buy Back: screen_height:%d not found", screen_height)
    except Exception:
        LOGGER.warning("Screen:Buy Back: screen_height failed to be found", exc_info=True)

    body_height = screen_height - 300
    body_style = {
        'margin-left': '60px',
        'height': f"{body_height}px",
        'overflow-y': 'scroll',
        'overflow-x': 'hidden',
        'backgroundColor': cd.ENV_VARS['BODY_DISPLAY_COLOR']
    }

    LOGGER.info("Screen:Buy Back: screen_height:%d body_height:%d", screen_height, body_height)

    orig_url_params_str = kwargs[URL_ID]
    url_params_dict = parse_url_params_str(orig_url_params_str)
    race_data_obj = rl.RaceData()
    new_url_params_str = ''

    button_id = ''
    abort_text = ''
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

    race_obj_list = dcd.RaceDb.query. \
        filter_by(race_id=race_id). \
        filter_by(in_race=False). \
        all()

    rv1 = [new_url_params_str, body_style]
    driver_data = {}
    for race_obj in race_obj_list:
        driver = race_data_obj.car_id_to_car_name[race_obj.car_id]['driver_name']
        car_name = race_data_obj.car_id_to_car_name[race_obj.car_id]['car_name']
        if driver not in driver_data:
            driver_data[driver] = []
        driver_data[driver].append({'label': car_name, 'value': car_name})

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    else:
        button_id = None

    idx = 0
    for driver_name in driver_data:
        idx += 1
        car_list = []
        for data_dict in driver_data[driver_name]:
            car_list.append(data_dict['value'])

        rv1.append({'display': 'block'})
        rv1.append(driver_data[driver_name])
        if button_id is None:
            rv1.append(car_list)
        else:
            rv1.append(dash.no_update)
        rv1.append(driver_name)

    for idx in range(idx, int(cd.ENV_VARS['MAX_RACE_COUNT'] / 2)):
        rv1.append({'display': 'none'})
        rv1.append(dash.no_update)
        rv1.append(dash.no_update)
        rv1.append(dash.no_update)

    car_ids = []
    for data_key in kwargs:
        if 'check_value' in data_key and kwargs[data_key] is not None:
            for car_name in kwargs[data_key]:
                car_ids.append(race_data_obj.car_name_to_car_id[car_name]['car_id'])

    if button_id == DONE_BUTTON:
        buy_back_count = 0
        for race_obj in race_obj_list:
            if race_obj.car_id not in car_ids:
                # dcd.RaceDb.query.filter_by(car_id=race_obj.car_id).update({'in_race': False})
                continue

            dcd.RaceDb.query.filter_by(race_id=race_id, car_id=race_obj.car_id).update(
                {
                    'buy_back': True,
                    'in_race': True,
                    'eliminated': 0,
                }
            )
            buy_back_count += 1

        if buy_back_count > 0:
            dbd.DB_DATA['DB'].session.commit()

        if buy_back_count > 1:
            LOGGER.info("Buy Back Round Needed - Race_id %d - count=%d %s",
                        int(url_params_dict['race_id']), buy_back_count, car_ids)
            rv1[0] = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_manager?race_id=%d&heat_id=2&buy_back=1" % \
                     race_id
            LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
        else:
            LOGGER.info("Buy Back Round Skipped - Race_id %d - count=%d %s",
                        int(url_params_dict['race_id']), buy_back_count, car_ids)
            rv1[0] = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_manager?race_id=%d&heat_id=3" % race_id

            # for race_obj in race_obj_list:
            #     dcd.RaceDb.query.filter_by(car_id=race_obj.car_id).update({'in_race': True})

            race_data_obj.load_cars(race_id=int(url_params_dict['race_id']),
                                    heat_id=3,
                                    )
            race_data_obj.build_race()

            LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
            LOGGER.info(cd.HEAT_LINE % (race_id, 3))

    return rv1
