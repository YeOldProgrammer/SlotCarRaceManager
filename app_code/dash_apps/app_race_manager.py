import json
import dash
import logging
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from sqlalchemy import func
from dash.exceptions import PreventUpdate
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

print("DISPLAY HEIGHT")
print(json.dumps(cd.ENV_VARS, indent=4, default=str))

inputs = []
outputs = []
BASE_ID = 'arm_'
CLICK_LEFT = 'left_check'
CLICK_RIGHT = 'right_check'
NEXT_HEAT_BUTTON = BASE_ID + 'next_heat'
RE_SHUFFLE_BUTTON = BASE_ID + 'shuffle'
NEW_RACE_BUTTON = BASE_ID + 'new_race'
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
        return 0

    run_id = int(check_id.split('_')[2])
    return run_id


def generate_row_data(run_id,
                      left_car='',
                      left_driver='',
                      left_check=False,
                      right_car='',
                      right_driver='',
                      right_check=False,
                      row_visible=True,
                      check_visible=True,
                      left_row_color='transparent',
                      right_row_color='transparent',
                      display_text=''):

    check_id = gen_check_id(run_id)

    if row_visible is False:
        master_display_value_il = 'none'
        master_display_value_bl = 'none'
        check_display_value = 'none'
        display_data = 'Row not visible'
    elif check_visible is False:
        master_display_value_il = 'inline-block'
        master_display_value_bl = 'block'
        check_display_value = 'block'
        display_data = 'Check not visible'
    else:
        master_display_value_il = 'inline-block'
        master_display_value_bl = 'block'
        check_display_value = 'block'
        display_data = ''

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

    display_run_id = run_id + 1

    data = [
        dbc.Col(html.H3(f'{display_run_id}'),
                style={'width': '50px', 'display': master_display_value_il}, width='auto'),
        dbc.Col(
            [
                html.H4(left_driver, style={'display': 'inline-block', 'width': '200px'}),
                html.H5(left_car),
            ],
            width='auto',
            style={"border": "2px black solid", 'display': master_display_value_il, 'backgroundColor': left_row_color,
                   'padding': '20px'}
        ),
        dbc.Col(
            [
                html.H3(style={'width': '40px'}),
                dcc.Checklist(options=[{'label': '.    .', 'value': CLICK_LEFT}, {'label': '', 'value': CLICK_RIGHT}],
                              value=value_array,
                              id=check_id,
                              style={'display': check_display_value}),
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
            style={"border": "2px black solid", 'display': master_display_value_il, 'backgroundColor': right_row_color,
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

    for idx in range(cd.ENV_VARS['MAX_RACE_COUNT']):
        run_id = idx
        key = gen_key(run_id)
        check_id = gen_check_id(run_id)
        run_row_id = BASE_ID + key + '_race_row'

        inputs.append(Input(check_id, 'value'))
        outputs.append(Output(run_row_id, 'children'))

        div_data, display_data = generate_row_data(run_id, display_text='', check_visible=False, row_visible=True)

        div_data_output.append(
            dbc.Row(
                children=div_data,
                id=run_row_id,
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


div_data = gen_initial_div_data()


ala.APP_LAYOUTS[ala.APP_RACE_MANAGER] = html.Div(
    [
        dcc.Location(id=URL_ID),
        html.Div(
            [
                html.H1('Race Manager'),
                dbc.Row(id=STATS_ROW, style={'margin-left': '55px'}),
            ],
            style={'height': '100px', 'backgroundColor': 'blue', 'height': '100px'}
        ),
        html.Div(
            children=div_data,
            style={'margin-left': '60px', 'height': f"{cd.ENV_VARS['DISPLAY_HEIGHT']}px", 'overflow-y': 'scroll',
                   'overflow-x': 'hidden'}
        ),
        html.Div(
            [
                html.Button('Next Heat', id=NEXT_HEAT_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                html.Button('Re-Shuffle', id=RE_SHUFFLE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                html.Button('New Race Button', id=NEW_RACE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
            ],
            style={'height': '100px', 'backgroundColor': 'red'}
        ),
    ],
    style={'margin-left': '50px', 'margin-top': '50px'}
)


def gen_stats_row(race_data_obj):
    row_data = [
        dbc.Col(html.H3("Heat: %d" % int(race_data_obj.heat_id)),
                style={'display': 'block'}, width='auto'),
        dbc.Col(html.H3("Drivers: %d" % len(race_data_obj.driver_name_to_driver_id)),
                style={'display': 'block'}, width='auto'),
        dbc.Col(html.H3("Cars: %d" % len(race_data_obj.car_name_to_car_id),
                        style={'display': 'block'}), width='auto'),
    ]

    return row_data


@wl.DASH_APP.callback(
    outputs,
    inputs,
)
@dash_kwarg(inputs)
def generate_graph(**kwargs):

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
        else:
            LOGGER.info("Race Manager Callback (%s) - Button Clicked (%s)", refresh, button_id)
    else:
        refresh = True
        LOGGER.info("Race Manager Callback (%s) - Nothing clicked", refresh)

    need_build = False
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
    if 'check_value' in button_id:
        check_run_id = get_run_id(button_id)

    rv1 = [new_url_params_str, gen_stats_row(race_data_obj)]

    race_data = kwargs[STATS_ROW]
    first_race_id = 0

    for kwarg in kwargs:
        run_id = get_run_id(kwarg)

        if run_id <= 0:
            continue

        if CLICK_LEFT in kwargs[kwarg]:
            race_data_obj.set_race_info(run_id, 1)
        elif CLICK_RIGHT in kwargs[kwarg]:
            race_data_obj.set_race_info(run_id, 2)

    for run_id in range(int(cd.ENV_VARS['MAX_RACE_COUNT'])):
        if run_id >= race_data_obj.run_count:
            if refresh is True:
                div_data, display_data = generate_row_data(run_id,
                                                           left_check=False,
                                                           right_check=False,
                                                           display_text='',
                                                           row_visible=False
                                                           )
                LOGGER.info("        Update Row %d (Refresh) - %s", run_id, display_data)
                rv1.append(div_data)
            else:
                rv1.append(dash.no_update)
            continue

        if refresh is False and run_id == check_run_id:
            rv1.append(dash.no_update)
            continue

        display_text = ''
        left_click = False
        right_click = False
        run_data = race_data_obj.run_data[run_id]
        if run_data['selected'] == 1:
            left_click = True
        elif run_data['selected'] == 2:
            right_click = True

        div_data, display_data = generate_row_data(run_id=run_id,
                                                   left_driver=run_data['cars'][0]['driver'],
                                                   left_car=run_data['cars'][0]['car'],
                                                   left_check=left_click,
                                                   right_driver=run_data['cars'][1]['driver'],
                                                   right_car=run_data['cars'][1]['car'],
                                                   right_check=right_click,
                                                   display_text=display_text,
                                                   check_visible=False)
        LOGGER.info("        Update Row %d (Click) - %s", run_id, display_data)
        rv1.append(div_data)

    race_data_obj.display_race_info()

    output_return = rv1

    return output_return
