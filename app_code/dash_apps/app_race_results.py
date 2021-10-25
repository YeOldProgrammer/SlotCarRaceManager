import os
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

    heat_obj_list = dcd.HeatDb.query. \
        filter_by(race_id=race_id). \
        order_by(dcd.HeatDb.heat_id, dcd.HeatDb.run_id). \
        all()

    save_report_data(race_data_obj, race_obj_list, heat_obj_list)

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


def save_report_data(race_data_obj, race_obj_list, heat_obj_list):
    race_list = []
    heat_list = []
    car_data = {}
    run_data = []

    for race_obj in race_obj_list:
        race_list.append(race_obj.__dict__)

    max_heat = 0
    for heat_obj in heat_obj_list:
        if heat_obj.heat_id > max_heat:
            max_heat = heat_obj.heat_id
    max_heat += 1
    max_last_heat = 0

    for heat_obj in heat_obj_list:
        heat_list.append(heat_obj.__dict__)
        driver_right = ''
        car_right = ''

        max_last_heat = 0
        car_left = race_data_obj.car_id_to_car_name[heat_obj.car_id_left]['car_name']
        driver_left = race_data_obj.car_id_to_car_name[heat_obj.car_id_left]['driver_name']
        if heat_obj.car_id_left not in car_data:
            car_data[heat_obj.car_id_left] = {
                'car_name': car_left,
                'driver_name': driver_left,
                'last_heat': 0,
                'rank': 0,
                'wins': 0,
                'wins_no_buy_back': 0,
                'buy_backs': 0,
                'results': ['     '] * max_heat
            }

        if heat_obj.car_id_right != 0:
            car_right = race_data_obj.car_id_to_car_name[heat_obj.car_id_right]['car_name']
            driver_right = race_data_obj.car_id_to_car_name[heat_obj.car_id_right]['driver_name']
            if heat_obj.car_id_right not in car_data:
                car_data[heat_obj.car_id_right] = {
                    'car_name': car_right,
                    'driver_name': driver_right,
                    'last_heat': 0,
                    'rank': 0,
                    'wins': 0,
                    'wins_no_buy_back': 0,
                    'buy_backs': 0,
                    'results': ['     '] * max_heat
                }

        if heat_obj.odd is True and heat_obj.heat_id >= max_heat:
            car_data[heat_obj.car_id_left]['results'][heat_obj.heat_id] = 'W    '
            car_data[heat_obj.car_id_left]['last_heat'] = heat_obj.heat_id
            run_data.append({
                'heat_id': heat_obj.heat_id, 'run_id': heat_obj.run_id,
                'driver_left': driver_left, 'car_left': car_left,
                'winner': 'Winner',
                'driver_right': driver_right, 'car_right': car_right,
            })
            max_last_heat = heat_obj.heat_id
        elif heat_obj.odd is True:
            car_data[heat_obj.car_id_left]['results'][heat_obj.heat_id] = 'O    '
            car_data[heat_obj.car_id_left]['last_heat'] = heat_obj.heat_id
            car_data[heat_obj.car_id_left]['buy_backs'] += 1
            run_data.append({
                'heat_id': heat_obj.heat_id, 'run_id': heat_obj.run_id,
                'driver_left': driver_left, 'car_left': car_left,
                'winner': '      ',
                'driver_right': driver_right, 'car_right': car_right,
            })
            max_last_heat = heat_obj.heat_id
        elif heat_obj.win_id == 1:
            car_data[heat_obj.car_id_left]['results'][heat_obj.heat_id] = 'L+:%02d' % heat_obj.run_id
            car_data[heat_obj.car_id_right]['results'][heat_obj.heat_id] = 'R-:%02d' % heat_obj.run_id
            car_data[heat_obj.car_id_left]['wins'] += 1
            if heat_obj.heat_id != 2:
                car_data[heat_obj.car_id_left]['wins_no_buy_back'] += 1
            car_data[heat_obj.car_id_left]['last_heat'] = heat_obj.heat_id
            car_data[heat_obj.car_id_right]['last_heat'] = heat_obj.heat_id
            max_last_heat = heat_obj.heat_id
            run_data.append({
                'heat_id': heat_obj.heat_id, 'run_id': heat_obj.run_id,
                'driver_left': driver_left, 'car_left': car_left,
                'winner': '<-----',
                'driver_right': driver_right, 'car_right': car_right,
            })
        elif heat_obj.win_id == 2:
            car_data[heat_obj.car_id_left]['results'][heat_obj.heat_id] = 'L-:%02d' % heat_obj.run_id
            car_data[heat_obj.car_id_right]['results'][heat_obj.heat_id] = 'R+:%02d' % heat_obj.run_id
            car_data[heat_obj.car_id_right]['wins'] += 1
            if heat_obj.heat_id != 2:
                car_data[heat_obj.car_id_right]['wins_no_buy_back'] += 1
            car_data[heat_obj.car_id_left]['last_heat'] = heat_obj.heat_id
            car_data[heat_obj.car_id_right]['last_heat'] = heat_obj.heat_id
            max_last_heat = heat_obj.heat_id
            run_data.append({
                'heat_id': heat_obj.heat_id, 'run_id': heat_obj.run_id,
                'driver_left': driver_left, 'car_left': car_left,
                'winner': '----->',
                'driver_right': driver_right, 'car_right': car_right,
            })
        else:
            pass

    output_dict = {
        'race': race_list,
        'heat': heat_list,
        'car_data': car_data,
    }

    rank = 0
    for heat_id in range(max_last_heat, 1, -1):
        found_data = []
        for car_id in car_data:
            car_info = car_data[car_id]
            if car_info['last_heat'] != heat_id:
                continue
            found_data.append(car_info)

        count = len(found_data)
        if count == 1:
            rank += 1
            found_data[0]['rank'] = rank
        elif count == 2:
            if found_data[0]['wins_no_buy_back'] > found_data[1]['wins_no_buy_back']:
                rank += 1
                found_data[0]['rank'] = rank
                rank += 1
                found_data[1]['rank'] = rank
            else:
                rank += 1
                found_data[1]['rank'] = rank
                rank += 1
                found_data[0]['rank'] = rank
        else:
            for found_rec in found_data:
                rank += 1
                found_rec['rank'] = rank

    car_data_format = "CARDATA | %-15s | %-15s | %2s | %2s | %2s | %2s | %2s | %s |"
    print(car_data_format % (
        'Driver', 'Car', ' R', ' W', 'AW', 'BB', 'LH', 'Ht:01 | Ht:02 | Ht:03 | Ht:04 | Ht:05 | Ht:06 | Ht:06 | Ht:07'
    ))
    car_data_format = "CARDATA | %-15s | %-15s | %2d | %2d | %2d | %2d | %2d | %s |"
    for driver_name in sorted(race_data_obj.driver_name_to_driver_id):
        for car_id in car_data:
            car_info = car_data[car_id]
            if car_info['driver_name'] != driver_name:
                continue

            print(car_data_format %
                  (driver_name, car_info['car_name'], car_info['rank'], car_info['wins'], car_info['wins_no_buy_back'],
                   car_info['buy_backs'], car_info['last_heat'], ' | '.join(car_info['results'][1:])))

    for run_dict in run_data:
        print("RUNDATA | %2d | %2d | %-15s | %-15s | %-6s | %-15s %-15s |" %
              (run_dict['heat_id'], run_dict['run_id'],
               run_dict['driver_left'], run_dict['car_left'],
               run_dict['winner'],
               run_dict['driver_right'], run_dict['car_right']))

    result_file = os.path.join(cd.ENV_VARS['LOG_DIR'], "results.log")
    with open(result_file, 'w') as result_fh:
        json.dump(output_dict, result_fh, indent=4, default=str)
