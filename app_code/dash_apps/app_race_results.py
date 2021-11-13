import os
import json
import dash
import time
import logging
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from sqlalchemy import func
from dash.exceptions import PreventUpdate
import plotly.express as px
# import plotly.graph_objects as go
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
REFRESH_BUTTON = BASE_ID + 'refresh'
DIV_DATA = BASE_ID + '_div_data'
URL_ID = BASE_ID + 'url'
DRIVER_GRAPH = BASE_ID + 'driver_graph'
DRIVER_TABLE = BASE_ID + 'driver_table'
RACE_GRAPH = BASE_ID + 'race_graph'
RACE_TABLE = BASE_ID + 'race_table'


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
            children=dbc.Row([
                dbc.Col(children=[
                    html.Div(children=[], id=DIV_DATA),
                ], width='auto'),
                dbc.Col(children=[
                    dcc.Loading(children=[
                        dcc.Graph(id=RACE_GRAPH),
                        dash_table.DataTable(
                            id=RACE_TABLE,
                            data=[],
                            columns=[],
                            sort_action='native',
                            sort_mode='single',
                            style_cell={'padding': '10px'},
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'color': 'white'
                            },
                            style_data={
                                'backgroundColor': 'rgb(50, 50, 50)',
                                'color': 'white'
                            },
                        ),
                        dcc.Graph(id=DRIVER_GRAPH),
                        dash_table.DataTable(
                            id=DRIVER_TABLE,
                            data=[],
                            columns=[],
                            sort_action='native',
                            sort_mode='single',
                            style_cell={'padding': '10px'},
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'color': 'white'
                            },
                            style_data={
                                'backgroundColor': 'rgb(50, 50, 50)',
                                'color': 'white'
                            },
                        ),
                    ])
                ], width='auto'),
            ]),
            style={'margin-left': '60px', 'height': f"{cd.ENV_VARS['BODY_DISPLAY_HEIGHT']}px", 'overflow-y': 'scroll',
                   'overflow-x': 'hidden', 'backgroundColor': cd.ENV_VARS['BODY_DISPLAY_COLOR']}
        ),
        html.Div(
            children=[
                dbc.Button('New Race', id=NEW_RACE_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
                dbc.Button('Refresh', id=REFRESH_BUTTON, style={'margin-left': '20px', 'margin-top': '20px'}),
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
    Output(DIV_DATA, 'style'),
    Output(URL_ID, 'href'),
    Output(RACE_GRAPH, 'figure'),
    Output(DRIVER_GRAPH, 'figure'),
    Output(RACE_TABLE, 'data'),
    Output(RACE_TABLE, 'columns'),
    Output(DRIVER_TABLE, 'data'),
    Output(DRIVER_TABLE, 'columns'),
    Output(NEW_RACE_BUTTON, 'style'),
    Output(REFRESH_BUTTON, 'style'),
    [
        Input(NEW_RACE_BUTTON, "n_clicks"),
        Input(REFRESH_BUTTON, "n_clicks"),
        Input(URL_ID, "href"),
    ],

)
def generate_graph(new_race_button, refresh_button, orig_url_params_str):
    cb_start_time = time.time()
    ctx = dash.callback_context

    url_params_dict = parse_url_params_str(orig_url_params_str)
    race_data_obj = rl.RaceData()
    new_url_params_str = dash.no_update

    if 'race_id' not in url_params_dict:
        LOGGER.info("Buy Back - Race_id was not specified")
        new_url_params_str = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_entry"
        raise PreventUpdate

    final = False
    if 'final' in url_params_dict:
        if url_params_dict['final'] == '1':
            final = True

    if final is True:
        div_data_style = {'margin-left': '0px', 'margin-top': '0px'}
        refresh_style = {'display': 'none'}
        new_race_style = {'margin-left': '0px', 'margin-top': '0px'}
    else:
        div_data_style = {'display': 'none'}
        refresh_style = {'margin-left': '0px', 'margin-top': '0px'}
        new_race_style = {'display': 'none'}

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
            return dash.no_update, dash.no_update, new_url_params_str, dash.no_update, dash.no_update, [], [], [], [],\
                   dash.no_update, dash.no_update

    race_dict_list, heat_dict_list, race_df, heat_df, driver_df = race_data_obj.get_race_results(print_results=True)
    save_report_data(race_data_obj, race_dict_list, heat_dict_list)

    div_data = []
    for race_dict in race_dict_list:
        if race_dict['rank'] <= 5:
            div_data.append(dbc.Row([
                dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url('place_%d.png' % race_dict['rank']),
                                 style={'height': '100px', 'width': '100px'}),
                        width='auto'),
                dbc.Col(html.H3(race_dict['driver_name']),
                        width='auto'),
                dbc.Col(html.H4(race_dict['car_name']),
                        width='auto'),
            ], align='center', style={'margin-top': '20px'}))

    race_fig = px.bar(race_df.sort_values(by='eliminated'), x='eliminated', y='car_name', color='driver_name')
    race_fig.update_layout({
        'font_color': 'white',
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'xaxis_title': 'Heat Reached',
        'yaxis_title': 'Car Name',
        'title': 'Race Results'
    })

    driver_fig = px.bar(driver_df.sort_values(by='win_count'), x='win_count', y='driver_name')
    driver_fig.update_layout({
        'font_color': 'white',
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'xaxis_title': 'Total Wins',
        'yaxis_title': 'Driver Name',
        'title': 'Driver Results'
    })

    race_columns = [
        {'name': 'Driver Name', 'id': 'driver_name'},
        {'name': 'Car Name', 'id': 'car_name'},
        {'name': 'Rank', 'id': 'rank'},
        {'name': 'Wins', 'id': 'win_count'},
        {'name': 'Skips', 'id': 'odd_skips'},
        {'name': 'Buy Backs', 'id': 'buy_back'},
        {'name': 'Heat Reached', 'id': 'eliminated'},
    ]

    driver_columns = [
        {'name': 'Driver Name', 'id': 'driver_name'},
        {'name': 'Cars', 'id': 'car_count'},
        {'name': 'Wins', 'id': 'win_count'},
        {'name': 'Loses', 'id': 'lose_count'},
        {'name': 'Heat Reached', 'id': 'max_heat'},
        {'name': 'Odd Cars', 'id': 'odd_count'},
        {'name': 'Buy Backs', 'id': 'buy_back'},
    ]

    return div_data, div_data_style, dash.no_update, race_fig, driver_fig, \
           race_df.to_dict('records'), race_columns, \
           driver_df.to_dict('records'), driver_columns, \
           new_race_style, refresh_style


def save_report_data(race_data_obj, race_dict_list, heat_dict_list):
    race_list = []
    heat_list = []
    car_data = {}
    run_data = []

    for race_dict in race_dict_list:
        race_list.append(race_dict)

    max_heat = 0
    for heat_dict in heat_dict_list:
        if heat_dict['heat_id'] > max_heat:
            max_heat = heat_dict['heat_id']
    max_heat += 1
    max_last_heat = 0

    for heat_dict in heat_dict_list:
        heat_list.append(heat_dict)
        driver_right = ''
        car_right = ''

        max_last_heat = 0
        car_left = race_data_obj.car_id_to_car_name[heat_dict['car_id_left']]['car_name']
        driver_left = race_data_obj.car_id_to_car_name[heat_dict['car_id_left']]['driver_name']
        if heat_dict['car_id_left'] not in car_data:
            car_data[heat_dict['car_id_left']] = {
                'car_name': car_left,
                'driver_name': driver_left,
                'last_heat': 0,
                'rank': 0,
                'wins': 0,
                'wins_no_buy_back': 0,
                'buy_backs': 0,
                'results': ['     '] * max_heat
            }

        if heat_dict['car_id_right'] != 0:
            car_right = race_data_obj.car_id_to_car_name[heat_dict['car_id_right']]['car_name']
            driver_right = race_data_obj.car_id_to_car_name[heat_dict['car_id_right']]['driver_name']
            if heat_dict['car_id_right'] not in car_data:
                car_data[heat_dict['car_id_right']] = {
                    'car_name': car_right,
                    'driver_name': driver_right,
                    'last_heat': 0,
                    'rank': 0,
                    'wins': 0,
                    'wins_no_buy_back': 0,
                    'buy_backs': 0,
                    'results': ['     '] * max_heat
                }

        if heat_dict['odd'] == 0 and heat_dict['heat_id'] >= max_heat:
            car_data[heat_dict['car_id_left']]['results'][heat_dict['heat_id']] = 'W    '
            car_data[heat_dict['car_id_left']]['last_heat'] = heat_dict['heat_id']
            run_data.append({
                'heat_id': heat_dict['heat_id'], 'run_id': heat_dict['run_id'],
                'driver_left': driver_left, 'car_left': car_left,
                'winner': 'Winner',
                'driver_right': driver_right, 'car_right': car_right,
            })
            max_last_heat = heat_dict['heat_id']
        elif heat_dict['odd'] == 1:
            car_data[heat_dict['car_id_left']]['results'][heat_dict['heat_id']] = 'O    '
            car_data[heat_dict['car_id_left']]['last_heat'] = heat_dict['heat_id']
            car_data[heat_dict['car_id_left']]['buy_backs'] += 1
            run_data.append({
                'heat_id': heat_dict['heat_id'], 'run_id': heat_dict['run_id'],
                'driver_left': driver_left, 'car_left': car_left,
                'winner': '      ',
                'driver_right': driver_right, 'car_right': car_right,
            })
            max_last_heat = heat_dict['heat_id']
        elif heat_dict['win_id'] == 1:
            car_data[heat_dict['car_id_left']]['results'][heat_dict['heat_id']] = 'L+:%02d' % heat_dict['run_id']
            car_data[heat_dict['car_id_right']]['results'][heat_dict['heat_id']] = 'R-:%02d' % heat_dict['run_id']
            car_data[heat_dict['car_id_left']]['wins'] += 1
            if heat_dict['heat_id'] != 2:
                car_data[heat_dict['car_id_left']]['wins_no_buy_back'] += 1
            car_data[heat_dict['car_id_left']]['last_heat'] = heat_dict['heat_id']
            car_data[heat_dict['car_id_right']]['last_heat'] = heat_dict['heat_id']
            max_last_heat = heat_dict['heat_id']
            run_data.append({
                'heat_id': heat_dict['heat_id'], 'run_id': heat_dict['run_id'],
                'driver_left': driver_left, 'car_left': car_left,
                'winner': '<-----',
                'driver_right': driver_right, 'car_right': car_right,
            })
        elif heat_dict['win_id'] == 2:
            car_data[heat_dict['car_id_left']]['results'][heat_dict['heat_id']] = 'L-:%02d' % heat_dict['run_id']
            car_data[heat_dict['car_id_right']]['results'][heat_dict['heat_id']] = 'R+:%02d' % heat_dict['run_id']
            car_data[heat_dict['car_id_right']]['wins'] += 1
            if heat_dict['heat_id'] != 2:
                car_data[heat_dict['car_id_right']]['wins_no_buy_back'] += 1
            car_data[heat_dict['car_id_left']]['last_heat'] = heat_dict['heat_id']
            car_data[heat_dict['car_id_right']]['last_heat'] = heat_dict['heat_id']
            max_last_heat = heat_dict['heat_id']
            run_data.append({
                'heat_id': heat_dict['heat_id'], 'run_id': heat_dict['run_id'],
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
