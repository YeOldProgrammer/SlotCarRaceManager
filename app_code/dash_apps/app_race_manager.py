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
    inputs.append(Input(START_BUTTON, 'n_clicks'))
    inputs.append(Input(DONE_BUTTON, 'n_clicks'))
    inputs.append(Input(NEXT_HEAT_BUTTON, 'n_clicks'))
    inputs.append(Input(RE_SHUFFLE_BUTTON, 'n_clicks'))
    inputs.append(Input(NEW_RACE_BUTTON, 'n_clicks'))
    inputs.append(Input(STATS_ROW, 'children'))
    outputs.append(Output(URL_ID, 'href'))
    outputs.append(Output(STATS_ROW, 'children'))
    outputs.append(Output(START_BUTTON, 'style'))
    outputs.append(Output(DONE_BUTTON, 'style'))
    outputs.append(Output(NEXT_HEAT_BUTTON, 'style'))
    outputs.append(Output(RE_SHUFFLE_BUTTON, 'style'))
    outputs.append(Output(REMAINING_PIE_CHART, 'figure'))
    outputs.append(Output(TIMER_TRIGGER, 'n_intervals'))
    outputs.append(Output(TIMER_TRIGGER, 'interval'))

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
        race_data_obj.refresh_stats()
        heat_id = int(race_data_obj.heat_id)
        driver_count = len(race_data_obj.driver_name_to_driver_id)
        orig_car_count = len(race_data_obj.car_name_to_car_id)
        total_race_count = race_data_obj.total_race_count
        completed_race_count = race_data_obj.completed_race_count
        car_count = race_data_obj.orig_car_count
        heat = race_data_obj.heat_id
        max_heat = race_data_obj.max_heat_id

        labels = ['Completed', 'Remaining']
        values = [completed_race_count, total_race_count - completed_race_count]
        colors = ['lightgreen', 'lightgrey']
        display_text = "%d%%" % ((completed_race_count / total_race_count) * 100)

    else:
        heat_id = 0
        driver_count = 0
        orig_car_count = 0
        labels = ['Remaining']
        values = [0]
        colors = ['lightgrey']
        display_text = ''

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5,
                                 marker_colors=colors)])
    fig.update_traces(textinfo='none')
    fig.update_layout(showlegend=False,
                      margin={'t': 0, 'l': 0, 'r': 0, 'b': 0},
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      title_text=display_text,
                      title_x=0.5,
                      title_y=0.5,
                      font = dict(color='white'),
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
        dcc.Interval(id=TIMER_TRIGGER, n_intervals=cd.ENV_VARS['RACE_DURATION_SEC'] + 5, interval=1*1000),
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
                    ], width='auto'),
                    dbc.Col([
                        dcc.Graph(id=REMAINING_TIME_CHART, figure=graph, style={'height': '140px', 'width': '140px'})
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
                dbc.Button('Start', id=START_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                dbc.Button('Done', id=DONE_BUTTON, style={'display': 'none'}),
                dbc.Button('Next Heat', id=NEXT_HEAT_BUTTON, style={'display': 'none'}),
                dbc.Button('Re-Shuffle', id=RE_SHUFFLE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                dbc.Button('New Race Button', id=NEW_RACE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                html.Img(src=wl.DASH_APP.get_asset_url(cd.ENV_VARS['LOGO_FILE']), style={'margin-left': '20px'}),
                html.Div([
                    html.H4("Purse"),
                    html.Hr(),
                    html.Div("1st: X"),
                    html.Div("2nd: X"),
                    html.Div("3rd: X"),
                    html.Div("4th: X"),
                ])
            ],
            style={'height': '100px'}
            # style={'height': '100px', 'backgroundColor': 'red'}
        ),
    ],
    style={'margin-left': '50px', 'margin-top': '50px'}
)


@wl.DASH_APP.callback(
    Output(REMAINING_TIME_CHART, 'figure'),
    Input(TIMER_TRIGGER, 'n_intervals')
)
def generate_timer(interval):
    time_remaining = interval
    fig = go.Figure(data=[go.Pie(labels=['Elapsed', 'Remain'],
                                 values=[time_remaining, cd.ENV_VARS['RACE_DURATION_SEC'] - time_remaining],
                                 marker={'colors': ['red', 'blue']},
                                 hole=0.5)])
    fig.update_traces(textinfo='none')
    display_time = cd.ENV_VARS['RACE_DURATION_SEC'] - time_remaining
    if display_time < 0:
        raise PreventUpdate

    fig.update_layout(showlegend=False,
                      margin={'t': 0, 'l': 0, 'r': 0, 'b': 0},
                      paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)',
                      title_text=display_time,
                      title_x=0.5,
                      title_y=0.5,
                      font=dict(color='white'),
                      )

    # LOGGER.info("Race Manager Callback: Timer (%s)", display_time)
    return fig


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
    updated_timer_value = dash.no_update

    button_id = ''
    timer_enabled = True
    need_build = False

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        refresh = False
        if button_id == NEW_RACE_BUTTON:
            new_url_params_str = url_params_dict.\
                get('url', f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_manager").replace('race_manager', 'race_entry')
            LOGGER.info("Race Manager Callback (%s) - New Race Button Clicked", refresh)
        elif button_id == URL_ID:
            LOGGER.info("Race Manager Callback (%s) - URL Clicked)", refresh)
            refresh = True
            updated_timer_value = 0
        else:
            LOGGER.info("Race Manager Callback (%s) - Button Clicked (%s)", refresh, button_id)
    else:
        refresh = True
        timer_enabled = False
        LOGGER.info("Race Manager Callback (%s) - Nothing clicked", refresh)

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
                updated_timer_value = 0
                timer_enabled = False
                refresh = True
                url_params_dict['heat_id'] = heat_obj.heat_id
                LOGGER.info("    Found race_id %s, heat_id %s", url_params_dict['race_id'], url_params_dict['heat_id'])
            else:
                url_params_dict['heat_id'] = heat_obj.heat_id
                LOGGER.info("    Found race_id %s, heat_id %s", url_params_dict['race_id'], url_params_dict['heat_id'])
        else:
            if button_id == RE_SHUFFLE_BUTTON:
                refresh = True
                timer_enabled = False
                LOGGER.info("    Race_id %s, heat_id %s specified - reshuffle", url_params_dict['race_id'], url_params_dict['heat_id'])
                need_build = True
                updated_timer_value = 0
            elif button_id == NEXT_HEAT_BUTTON:
                timer_enabled = False
                updated_timer_value = 0
                LOGGER.info("    Race_id %s, heat_id %s specified - new heat", url_params_dict['race_id'], url_params_dict['heat_id'])
                race_data_obj.load_cars(race_id=url_params_dict['race_id'], heat_id=url_params_dict['heat_id'])
                abort_text = race_data_obj.next_heat()
                if abort_text == '':
                    url_params_dict['heat_id'] = race_data_obj.heat_id + 1
                    need_build = True
                    refresh = True
            elif button_id == DONE_BUTTON:
                timer_enabled = False
                updated_timer_value = 0
            elif button_id == START_BUTTON:
                timer_enabled = True
                updated_timer_value = 0
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
        new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_entry"

    if orig_url_params_str != new_url_params_str:
        LOGGER.info("    URL Change\n        from: %s\n          to: %s", orig_url_params_str, new_url_params_str)

    latest_run_id, none_raced, all_raced, clicked_current = calculate_race_pos(
        race_data_obj=race_data_obj, kwargs=kwargs, button_id=button_id)

    LOGGER.info("        Refresh:%s latest_run_id=%d none=%s all=%s clicked_current=%s",
                refresh, latest_run_id, none_raced, all_raced, clicked_current)

    if clicked_current is True:
        updated_timer_value = 0

    if none_raced is True:
        start_style = {'margin-left': '20px', 'margin-top': '20px'}
        shuffle_style = {'margin-left': '20px', 'margin-top': '20px'}
    else:
        start_style = {'display': 'none'}
        shuffle_style = {'display': 'none'}

    stats_data, graph = gen_stats_row(race_data_obj)
    if all_raced is True:
        if race_data_obj.heat_id == race_data_obj.max_heat_id:
            done_style = {'margin-left': '20px', 'margin-top': '20px'}
            next_heat_style = {'display': 'none'}
        else:
            next_heat_style = {'margin-left': '20px', 'margin-top': '20px'}
            done_style = {'display': 'none'}
        timer_enabled = False
    else:
        next_heat_style = {'display': 'none'}
        done_style = {'display': 'none'}

    timer_graph = dash.no_update
    if timer_enabled is True:
        timer_interval = 1000  # once a second
    else:
        timer_interval = 86400000  # once a day

    LOGGER.info("        Interval time Enabled:%s (%d)", timer_enabled, timer_interval)

    rv1 = [new_url_params_str, stats_data, start_style, done_style, next_heat_style, shuffle_style, graph,
           updated_timer_value, timer_interval]

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
            if refresh is True and run_id == latest_run_id + 1:
                display_text = 'Racing'
                check_visible = True
            elif refresh is True and run_id == latest_run_id + 2:
                display_text = 'On Deck'
                check_visible = False
            else:
                display_text = ''
                check_visible = False
        else:
            if run_id <= latest_run_id + 1:
                check_visible = True
            else:
                check_visible = False

            if run_id == latest_run_id - 1:
                display_text = ''
                # LOGGER.info("        Before:%d", run_id)
            elif run_id == latest_run_id:
                display_text = ''
                # LOGGER.info("        Checked:%d", run_id)
            elif run_id == latest_run_id + 1:
                display_text = 'Racing'
                current_race = True
                # LOGGER.info("        After1:%d", run_id)
            elif run_id == latest_run_id + 2:
                display_text = 'On Deck'
                # LOGGER.info("        After2:%d", run_id)
            else:
                display_text = ''
                # LOGGER.info("        Other:%d", run_id)

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
            LOGGER.info("        Update Row %3d (%-7s) - %s (Odd car out)", run_id, 'Click', display_data)
            rv1.append(div_data)
            continue

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

        LOGGER.info("        Update Row %3d (%-7s) - %s check=%s text=%s",
                    run_id, 'Click', display_data, check_visible, display_text)
        rv1.append(div_data)

    race_data_obj.display_race_info()

    output_return = rv1
    LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
    return output_return


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
