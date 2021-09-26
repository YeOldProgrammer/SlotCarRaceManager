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
BASE_ID = 'arm_'
CLICK_LEFT = 'left_check'
CLICK_RIGHT = 'right_check'
HEAT_SLIDER = BASE_ID + 'slider'
NEXT_HEAT_BUTTON = BASE_ID + 'next_heat'
RE_SHUFFLE_BUTTON = BASE_ID + 'shuffle'
NEW_RACE_BUTTON = BASE_ID + 'new_race'
REMAINING_PIE_CHART = BASE_ID + "race_remaining_pie_chart"
STATS_ROW = BASE_ID + 'stats'
URL_ID = BASE_ID + 'url'


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
    inputs.append(Input(NEXT_HEAT_BUTTON, 'n_clicks'))
    inputs.append(Input(RE_SHUFFLE_BUTTON, 'n_clicks'))
    inputs.append(Input(NEW_RACE_BUTTON, 'n_clicks'))
    inputs.append(Input(STATS_ROW, 'children'))
    outputs.append(Output(URL_ID, 'href'))
    outputs.append(Output(STATS_ROW, 'children'))
    outputs.append(Output(REMAINING_PIE_CHART, 'figure'))

    for idx in range(cd.ENV_VARS['MAX_RACE_COUNT']):
        run_id = idx
        key = gen_key(run_id)
        check_id = gen_check_id(run_id)
        run_row_id = BASE_ID + key + '_race_row'

        inputs.append(Input(check_id, 'value'))
        outputs.append(Output(run_row_id, 'children'))

        div_data, display_data = generate_row_data(run_id=run_id,
                                                   display_text='',
                                                   check_visible=False,
                                                   row_visible=False)

        div_data_output.append(
            dbc.Row(
                children=div_data,
                id=run_row_id,
                style={'margin-top': '10px'}
            )
        )

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


def gen_stats_row(race_data_obj=None):
    max_heat = 0
    if race_data_obj is not None:
        heat_id = int(race_data_obj.heat_id)
        driver_count = len(race_data_obj.driver_name_to_driver_id)
        orig_car_count = len(race_data_obj.car_name_to_car_id)
    else:
        heat_id = 0
        driver_count = 0
        orig_car_count = 0

    car_count = orig_car_count
    if race_data_obj is None:
        labels = ['Remaining']
        values = [0]
        colors = ['lightgrey']
    else:
        total_race_count = 0
        completed_race_count = 0
        car_count = race_data_obj.orig_car_count
        heat = 0

        while car_count > 1:
            heat += 1
            max_heat += 1
            odd = car_count % 2
            half = int(car_count/2)
            total_race_count += half
            car_count = half + odd
            if heat < race_data_obj.heat_id:
                completed_race_count += half

        for run_dict in race_data_obj.run_data:
            if run_dict['selected'] != 0 and run_dict['odd'] is False:
                completed_race_count += 1

        labels = ['Completed', 'Remaining']
        values = [completed_race_count, total_race_count - completed_race_count]
        colors = ['lightgreen', 'lightgrey']

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5,
                                 marker_colors=colors)])
    fig.update_layout(showlegend=False, margin={'t': 0, 'l': 0, 'r': 0, 'b': 0},
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)'
                      )

    row_data = [
        dbc.Col(html.H3("Heat: %d of %d" % (heat_id, max_heat)), style={'display': 'block'}, width='auto'),
        dbc.Col(html.H3("Drivers: %d" % driver_count), style={'display': 'block'}, width='auto'),
        dbc.Col(html.H3("Cars: %d" % orig_car_count, style={'display': 'block'}), width='auto'),
    ]

    return row_data, fig


div_data = gen_initial_div_data()
stats_data, graph = gen_stats_row()
ala.APP_LAYOUTS[ala.APP_RACE_MANAGER] = html.Div(
    [
        dcc.Location(id=URL_ID),
        html.Div(
            [
                dbc.Row([
                    dbc.Col([
                        html.H1('Race Manager'),
                        dbc.Row(id=STATS_ROW, children=stats_data, style={'margin-left': '55px'}),
                        html.Div(children=[
                            html.H4('Left Track', style={'margin-left': '100px', 'display': 'inline-block'}),
                            html.H4('Right Track', style={'margin-left': '220px', 'display': 'inline-block'}),
                        ], style={'display': 'inline-block'}),
                    ], width='auto'),
                    dbc.Col([
                        dcc.Graph(id=REMAINING_PIE_CHART, figure=graph, style={'height': '140px', 'width': '140px'})
                    ], width='auto')
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
                html.Button('Next Heat', id=NEXT_HEAT_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                html.Button('Re-Shuffle', id=RE_SHUFFLE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                html.Button('New Race Button', id=NEW_RACE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
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
    if ctx.triggered:
        refresh = False
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == NEW_RACE_BUTTON:
            new_url_params_str = url_params_dict.\
                get('url', 'http://127.0.0.1:8080/race_manager').replace('race_manager', 'race_entry')
            LOGGER.info("Race Manager Callback (%s) - New Race Button Clicked", refresh)
        elif button_id == URL_ID:
            LOGGER.info("Race Manager Callback (%s) - URL Clicked)", refresh)
            refresh = True
        else:
            LOGGER.info("Race Manager Callback (%s) - Button Clicked (%s)", refresh, button_id)
    else:
        refresh = True
        LOGGER.info("Race Manager Callback (%s) - Nothing clicked", refresh)

    need_build = False
    new_heat = False
    abort_text = ''
    if 'race_id' in url_params_dict:
        if 'heat_id' not in url_params_dict:
            heat_obj = dcd.HeatDb.\
                query.\
                filter_by(race_id=url_params_dict['race_id']).\
                order_by(dcd.HeatDb.heat_id.desc()).\
                first()

            if heat_obj is None:
                url_params_dict['heat_id'] = 1
                LOGGER.info("    No heat for race_id %s", url_params_dict['race_id'])
                need_build = True
            elif button_id == RE_SHUFFLE_BUTTON:
                refresh = True
                url_params_dict['heat_id'] = heat_obj.heat_id
                LOGGER.info("    Found race_id %s, heat_id %s", url_params_dict['race_id'], url_params_dict['heat_id'])
            else:
                url_params_dict['heat_id'] = heat_obj.heat_id
                LOGGER.info("    Found race_id %s, heat_id %s", url_params_dict['race_id'], url_params_dict['heat_id'])
        else:
            if button_id == RE_SHUFFLE_BUTTON:
                refresh = True
                LOGGER.info("    Race_id %s, heat_id %s specified - reshuffle", url_params_dict['race_id'], url_params_dict['heat_id'])
                need_build = True
            elif button_id == NEXT_HEAT_BUTTON:
                LOGGER.info("    Race_id %s, heat_id %s specified - new heat", url_params_dict['race_id'], url_params_dict['heat_id'])
                race_data_obj.load_cars(race_id=url_params_dict['race_id'], heat_id=url_params_dict['heat_id'])
                abort_text = race_data_obj.next_heat()
                if abort_text == '':
                    url_params_dict['heat_id'] = race_data_obj.heat_id + 1
                    need_build = True
                    refresh = True
            else:
                LOGGER.info("    Race_id %s, heat_id %s specified", url_params_dict['race_id'], url_params_dict['heat_id'])

        race_data_obj.load_cars(race_id=url_params_dict['race_id'], heat_id=url_params_dict['heat_id'])

        if need_build is True:
            race_data_obj.build_race()
        else:
            race_data_obj.load_run()

        if new_url_params_str == '':
            new_url_params_str = build_url_params_str(url_params_dict)
    else:
        LOGGER.info("    Race_id was not specified")
        new_url_params_str = 'http://127.0.0.1:8080/race_entry'

    if orig_url_params_str != new_url_params_str:
        LOGGER.info("    URL Change\n        from: %s\n          to: %s", orig_url_params_str, new_url_params_str)

    check_run_id = 0
    check_run_id_before = 0
    check_run_id_after = 0
    check_run_id_2_after = 0
    if 'check_value' in button_id:
        check_run_id = get_run_id(button_id)

        check_run_id_before = check_run_id - 1
        check_run_id_after = check_run_id + 1
        check_run_id_2_after = check_run_id + 2
        # check_run_id_before = -1
        # check_run_id_after = -1
        # check_run_id_2_after = -1
        #
        # if CLICK_LEFT in kwargs[button_id] or CLICK_RIGHT in kwargs[button_id]:
        #     for idx in range(check_run_id, race_data_obj.run_count):
        #         row_button_id = gen_check_id(idx)
        #         if CLICK_LEFT in kwargs[row_button_id] or CLICK_RIGHT in kwargs[row_button_id]:
        #             LOGGER.info("        clicked:%s - button:%s - value:%s (Clicked)",
        #                         button_id, row_button_id, kwargs[row_button_id])
        #         else:
        #             LOGGER.info("        clicked:%s - button:%s - value:%s (None)",
        #                         button_id, row_button_id, kwargs[row_button_id])
        # else:

    race_data = kwargs[STATS_ROW]
    first_race_id = 0

    # Look for clicked button
    for kwarg in kwargs:
        run_id = get_run_id(kwarg)

        if run_id < 0:
            continue

        if button_id == kwarg:
            if CLICK_LEFT in kwargs[kwarg] and CLICK_RIGHT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_BOTH_WINNER)
            elif CLICK_LEFT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_LEFT_WINNER)
            elif CLICK_RIGHT in kwargs[kwarg]:
                race_data_obj.set_race_info(run_id, cd.VALUE_RIGHT_WINNER)
            else:
                if first_race_id == 0:
                    first_race_id = run_id
                race_data_obj.set_race_info(run_id, cd.VALUE_NO_WINNER)

    LOGGER.info("        Refresh:%s b:%d i:%d a1:%d a2:%d",
                refresh, check_run_id_before, check_run_id, check_run_id_after, check_run_id_2_after)

    stats_data, graph = gen_stats_row(race_data_obj)
    rv1 = [new_url_params_str, stats_data, graph]

    for run_id in range(int(cd.ENV_VARS['MAX_RACE_COUNT'])):
        if run_id >= race_data_obj.run_count:
            if refresh is True:
                div_data, display_data = generate_row_data(run_id=run_id,
                                                           left_check=False,
                                                           right_check=False,
                                                           display_text='',
                                                           row_visible=False
                                                           )
                LOGGER.info("        Update Row %3d (%-7s) - %s", run_id, 'Refresh', display_data)
                rv1.append(div_data)
            else:
                rv1.append(dash.no_update)
            continue

        if refresh is False:
            if run_id < check_run_id_before or run_id > check_run_id_2_after:
                rv1.append(dash.no_update)
                continue

        display_text = ''
        check_visible = False
        current_race = False
        left_click = False
        right_click = False
        left_row_color = 'transparent'
        right_row_color = 'transparent'
        left_font_color = 'lightgrey'
        right_font_color = 'lightgrey'

        run_data = race_data_obj.run_data[run_id]
        if run_data['selected'] == cd.VALUE_LEFT_WINNER:
            left_click = True
            left_row_color = 'lightgreen'
            left_font_color = 'black'
        elif run_data['selected'] == cd.VALUE_RIGHT_WINNER:
            right_click = True
            right_row_color = 'lightgreen'
            right_font_color = 'black'

        if refresh is True:
            if refresh is True and run_id == first_race_id:
                display_text = 'Racing'
                check_visible = True
            elif refresh is True and run_id == first_race_id + 1:
                display_text = 'On Deck'
                check_visible = False
            else:
                display_text = ''
                check_visible = False
        else:
            if run_id == check_run_id_before:
                display_text = ''
                check_visible = True
                LOGGER.info("Before:%d", run_id)
            elif run_id == check_run_id:
                display_text = ''
                check_visible = True
                LOGGER.info("Checked:%d", run_id)
            elif run_id == check_run_id_after:
                display_text = 'Racing'
                check_visible = True
                current_race = True
                LOGGER.info("After1:%d", run_id)
            elif run_id == check_run_id_2_after:
                display_text = 'On Deck'
                check_visible = False
                LOGGER.info("After2:%d", run_id)
            else:
                display_text = ''
                check_visible = False
                LOGGER.info("Other:%d", run_id)

        if len(run_data['cars']) == 1:
            # Odd number of cars in this heat, odd car out
            display_text = ''
            div_data, display_data = generate_row_data(run_id=run_id,
                                                       left_driver=run_data['cars'][0]['driver'],
                                                       left_car=run_data['cars'][0]['car'],
                                                       left_check=True,
                                                       left_row_color=left_row_color,
                                                       left_font_color=left_font_color,
                                                       right_driver=None,
                                                       right_car=None,
                                                       right_row_color=right_row_color,
                                                       right_font_color=right_font_color,
                                                       right_check=right_click,
                                                       display_text=display_text,
                                                       check_visible=False,
                                                       row_visible=True)
        else:
            div_data, display_data = generate_row_data(run_id=run_id,
                                                       left_driver=run_data['cars'][0]['driver'],
                                                       left_car=run_data['cars'][0]['car'],
                                                       left_check=left_click,
                                                       left_row_color=left_row_color,
                                                       left_font_color=left_font_color,
                                                       right_driver=run_data['cars'][1]['driver'],
                                                       right_car=run_data['cars'][1]['car'],
                                                       right_row_color=right_row_color,
                                                       right_font_color=right_font_color,
                                                       right_check=right_click,
                                                       display_text=display_text,
                                                       check_visible=check_visible,
                                                       current_race=current_race,
                                                       row_visible=True)

        LOGGER.info("        Update Row %3d (%-7s) - %s", run_id, 'Click', display_data)
        rv1.append(div_data)

    race_data_obj.display_race_info()

    output_return = rv1
    LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
    return output_return
