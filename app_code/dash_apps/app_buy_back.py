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


def generate_row_data(run_id=None,
                      left_car='',
                      left_driver='',
                      left_check=False,
                      right_car='',
                      right_driver='',
                      right_check=False,
                      row_visible=True,
                      check_visible=True,
                      current_race=False,
                      left_row_color='transparent',
                      left_font_color='lightgrey',
                      right_row_color='transparent',
                      right_font_color='lightgrey',
                      display_text=''):

    if row_visible is False:
        master_display_value_il = 'none'
        master_display_value_bl = 'none'
        check_display_value = 'none'
        display_data = 'Row not visible'
    elif check_visible is False:
        master_display_value_il = 'inline-block'
        master_display_value_bl = 'block'
        check_display_value = 'none'
        display_data = 'Check not visible'
    else:
        master_display_value_il = 'inline-block'
        master_display_value_bl = 'block'
        check_display_value = 'block'
        display_data = ''

    if current_race is False:
        border_style = "2px black solid"
    else:
        border_style = "5px red solid"

    value_array = []
    if left_check is True and right_check is True:
        value_array.append(CLICK_LEFT)
        value_array.append(CLICK_RIGHT)
        if check_display_value == 'block':
            display_data += ', both are winner'
    elif left_check is True:
        value_array.append(CLICK_LEFT)
        if check_display_value == 'block':
            display_data += ', left is winner'
    elif right_check is True:
        value_array.append(CLICK_RIGHT)
        if check_display_value == 'block':
            display_data += ', right is winner'
    else:
        if check_display_value == 'block':
            display_data += ', no winner selected'

    if run_id is not None:
        check_id = gen_check_id(run_id)
        display_run_id = run_id + 1
        display_col = dbc.Col(html.H3(f'{display_run_id}'),
                              style={'width': '50px', 'display': master_display_value_il}, width='auto')
        check_list = dcc.Checklist(
            options=[
                {'label': '.    .', 'value': CLICK_LEFT},
                {'label': '', 'value': CLICK_RIGHT}
            ],
            value=value_array,
            id=check_id,
            style={'display': check_display_value}
        )
    else:
        display_col = dbc.Col(html.H3('', style={'width': '50px', 'display': 'none'}), width='auto')
        check_list = html.Div()

    data = [
        display_col,
        dbc.Col(
            [
                html.H4(left_driver, style={'display': 'inline-block', 'width': '200px'}),
                html.H5(left_car),
            ],
            width='auto',
            style={"border": border_style,
                   'display': master_display_value_il,
                   'backgroundColor': left_row_color,
                   'color': left_font_color,
                   'padding': '20px'}
        ),
        dbc.Col(
            [
                html.H3(style={'width': '40px'}),
                check_list,
            ],
            width='auto',
            style={'display': master_display_value_bl}
        ),
        dbc.Col(
            [
                html.H4(right_driver, style={'display': 'inline-block', 'width': '200px'}),
                html.H5(right_car),
            ],
            width='auto',
            style={"border": border_style,
                   'display': master_display_value_il,
                   'backgroundColor': right_row_color,
                   'color': right_font_color,
                   'padding': '20px'}
        ),
        dbc.Col(
            [
                html.H4(html.Div(display_text),
                        style={'display': 'inline-block', 'width': '200px'},
                        ),
            ],
            width='auto',
            style={'backgroundColor': 'transparent', 'padding': '20px', 'display': master_display_value_il}
        ),
    ]

    return data, display_data


def gen_initial_div_data():
    div_data_output = []

    inputs.append(Input(URL_ID, 'href'))
    inputs.append(Input(DONE_BUTTON, 'n_clicks'))
    outputs.append(Output(URL_ID, 'href'))

    # for idx in range(cd.ENV_VARS['MAX_RACE_COUNT']):
    #     run_id = idx
    #     key = gen_key(run_id)
    #     check_id = gen_check_id(run_id)
    #     run_row_id = BASE_ID + key + '_race_row'
    #
    #     inputs.append(Input(check_id, 'value'))
    #     outputs.append(Output(run_row_id, 'children'))
    #
    #     div_data, display_data = generate_row_data(run_id=run_id,
    #                                                display_text='',
    #                                                check_visible=False,
    #                                                row_visible=False)
    #
    #     div_data_output.append(
    #         dbc.Row(
    #             children=div_data,
    #             id=run_row_id,
    #             style={'margin-top': '10px'}
    #         )
    #     )

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

    orig_url_params_str = kwargs[URL_ID]
    url_params_dict = parse_url_params_str(orig_url_params_str)
    race_data_obj = rl.RaceData()
    new_url_params_str = ''

    button_id = ''
    abort_text = ''
    if 'race_id' not in url_params_dict:
        LOGGER.info("    Race_id was not specified")
        new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_entry"
    else:
        new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/buy_back?race_id=%d&heat_id=%d" % \
                             (int(url_params_dict['race_id']), 1)
        race_data_obj.load_cars(race_id=url_params_dict['race_id'], heat_id=1)
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == DONE_BUTTON:
                LOGGER.info("    Race_id %s specified", url_params_dict['race_id'])

    if orig_url_params_str != new_url_params_str:
        LOGGER.info("    URL Change\n        from: %s\n          to: %s", orig_url_params_str, new_url_params_str)

    rv1 = [new_url_params_str]




    LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
    return rv1


def calculate_race_pos(race_data_obj, kwargs, button_id):
    latest_run_id = -1
    none_raced = True
    all_raced = False
    clicked_current = False
    clicked_run_id = -1

    # Look for clicked button
    race_results = []
    run_id = 0
    for kwarg in kwargs:
        run_id = get_run_id(kwarg)

        if run_id < 0:
            continue

        if CLICK_LEFT in kwargs[kwarg] or CLICK_RIGHT in kwargs[kwarg] and \
                run_id < len(race_data_obj.run_data) and race_data_obj.run_data[run_id]['odd'] is False:
            race_results.append(True)
        else:
            race_results.append(False)

        if button_id == kwarg:
            clicked_run_id = run_id
            if CLICK_LEFT in kwargs[kwarg] and CLICK_RIGHT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_BOTH_WINNER)
            elif CLICK_LEFT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_LEFT_WINNER)
            elif CLICK_RIGHT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_RIGHT_WINNER)
            else:
                race_data_obj.set_race_info(run_id, cd.VALUE_NO_WINNER)

    first_found = False
    done_count = 0
    for race_idx in range(run_id - 1, -1, -1):
        if race_results[race_idx] is True:
            done_count += 1

            if first_found is False and race_idx < len(race_data_obj.run_data) and \
                    race_data_obj.run_data[race_idx]['odd'] is False:
                latest_run_id = race_idx
                none_raced = False
                first_found = True

    if done_count >= race_data_obj.run_count:
        all_raced = True

    if clicked_run_id == latest_run_id:
        clicked_current = True

    return latest_run_id, none_raced, all_raced, clicked_current
