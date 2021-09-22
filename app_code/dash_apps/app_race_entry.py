import dash
import time
import logging
import dash_table
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import app_code.common.db_data as dbd
import dash_html_components as html
from sqlalchemy import func
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import app_code.common.web_logic as wl
from app_code.common import app_logging as al
from app_code.common.dash_util import dash_kwarg
import app_code.common.db_custom_def as dcd
import app_code.dash_apps.app_layouts as ala

LOGGER = logging.getLogger(al.LOGGER_NAME)

BASE_ID = 'are_'
START_RACE_BUTTON = BASE_ID + 'start_race'
DRIVER_DELETE_BUTTON = BASE_ID + 'driver_delete'
DRIVER_ADD_BUTTON = BASE_ID + 'driver_add'
DRIVER_DROPDOWN = BASE_ID + 'driver_dropdown'
CAR_AVAILABLE_TABLE = BASE_ID + 'car_available_table'
CAR_DATA_TABLE = BASE_ID + 'car_data_table'
CAR_DELETE_BUTTON = BASE_ID + 'driver_delete'
CAR_ADD_SEL_BUTTON = BASE_ID + 'car_add_sel'
CAR_ADD_ALL_BUTTON = BASE_ID + 'car_add_all'
CAR_REMOVE_BUTTON = BASE_ID + 'car_remove'
URL_ID = BASE_ID + 'url'

ala.APP_LAYOUTS[ala.APP_RACE_ENTRY] = html.Div([
    html.H1('Race Entry'),
    dcc.Location(id=URL_ID),
    dbc.Row([
        dbc.Col(
            [
                html.H3("Race Data"),
            ],
            width='auto',
            style={"border": "2px black solid", 'padding': '20px', 'margin-left': '50px'}
        ),
    ]),
    dbc.Row([
        dbc.Col(
            [
                html.H3("Entries"),
                dash_table.DataTable(
                    id=CAR_DATA_TABLE,
                    columns=[
                        {'name': 'Driver', 'id': 'driver_name', 'type': 'text'},
                        {'name': 'Car', 'id': 'car_name', 'type': 'text'},
                    ],
                    data=None,
                    selected_rows=[],
                    row_selectable="multi",
                    sort_action='native',
                    sort_mode='multi',
                    sort_by=[{'column_id': 'driver_name', 'direction': 'asc'},
                             {'column_id': 'car_name', 'direction': 'asc'}],
                    style_data={
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                    },
                    style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                    style_cell={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'white'
                    },
                ),
                html.Button('Remove from race', id=CAR_REMOVE_BUTTON,
                            style={'margin-left': '50px', 'margin-top': '10px'}),
            ],
            width='auto',
            style={"border": "2px black solid", 'padding': '20px', 'margin-left': '50px'}
        ),
        dbc.Col(
            [
                html.H3("Available Drivers"),
                dcc.Dropdown(id=DRIVER_DROPDOWN, value='', style={'color': 'black'}),
                dbc.Row([
                    dbc.Col([
                        html.Button('Add New Driver', id=DRIVER_ADD_BUTTON,
                                    style={'margin-left': '20px'}),
                    ], width='auto'),
                    dbc.Col([
                        dcc.ConfirmDialogProvider(
                            children=html.Button('Delete Driver from DB (and all associated cars)'),
                            id=DRIVER_DELETE_BUTTON,
                            message='Are you sure you want to delete this driver from the DB?',
                        ),
                    ], width='auto'),
                ]),
                html.H3("Available Cars", style={'margin-top': '20px'}),
                dash_table.DataTable(
                    id=CAR_AVAILABLE_TABLE,
                    columns=[
                        {'name': 'Car', 'id': 'car_name', 'type': 'text'},
                    ],
                    data=None,
                    selected_rows=[],
                    row_selectable="multi",
                    style_data={
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                    },
                    style_header={'backgroundColor': 'rgb(30, 30, 30)'},
                    style_cell={
                        'backgroundColor': 'rgb(50, 50, 50)',
                        'color': 'white'
                    },
                ),
                html.Button('Add Selected Car(s)', id=CAR_ADD_SEL_BUTTON,
                            style={'margin-left': '20px'}),
                html.Button('Add All Car(s)', id=CAR_ADD_ALL_BUTTON,
                            style={'margin-left': '20px'}),
                html.Button('Delete Selected Cars from DB', id=CAR_DELETE_BUTTON,
                            style={'margin-left': '20px'}),
            ],
            width='auto',
            style={"border": "2px black solid", 'padding': '20px', 'margin-left': '50px'}
        ),
    ],
    style={'margin-top': '20px'}),
    html.Button('Start New Race', id=START_RACE_BUTTON, style={'margin-left': '50px', 'margin-top': '10px'}),
])


@wl.DASH_APP.callback(
    [
        Output(DRIVER_DROPDOWN, 'options'),
        Output(CAR_AVAILABLE_TABLE, 'data'),
        Output(CAR_AVAILABLE_TABLE, 'selected_rows'),
        Output(CAR_DATA_TABLE, 'data'),
        Output(CAR_DATA_TABLE, 'selected_rows'),
        Output(URL_ID, 'href')
    ],
    [
        Input(DRIVER_DROPDOWN, 'value'),
        Input(DRIVER_ADD_BUTTON, 'n_clicks'),
        Input(DRIVER_DELETE_BUTTON, 'submit_n_clicks'),
        Input(CAR_ADD_SEL_BUTTON, 'n_clicks'),
        Input(CAR_ADD_ALL_BUTTON, 'n_clicks'),
        Input(CAR_DELETE_BUTTON, 'n_clicks'),
        Input(CAR_REMOVE_BUTTON, 'n_clicks'),
        Input(START_RACE_BUTTON, 'n_clicks'),
    ],
    [
        State(CAR_AVAILABLE_TABLE, 'selected_rows'),
        State(CAR_AVAILABLE_TABLE, 'data'),
        State(CAR_DATA_TABLE, 'selected_rows'),
        State(CAR_DATA_TABLE, 'data'),
        State(URL_ID, 'href')
    ]
)
def display_page(driver_dropdown, driver_add_n_clicks, driver_delete_n_clicks, car_add_sel_n_clicks,
                 car_add_all_n_clicks, car_delete_n_clicks, car_remove_n_clicks, start_race_n_clicks,
                 car_available_selected, car_available_data, car_data_selected, car_data, orig_url):
    cb_start_time = time.time()
    ctx = dash.callback_context

    driver_obj_list = dcd.DriverDb.query.all()
    driver_list = []
    car_list = []
    car_mapping = {}
    updated_car_selected = dash.no_update
    updated_car_data_selected = dash.no_update
    new_url = dash.no_update

    driver_id = 0
    driver_mapping = {}
    for driver_obj in driver_obj_list:
        driver_list.append({'label': driver_obj.driver_name, 'value': driver_obj.driver_name})
        driver_mapping[driver_obj.driver_name] = driver_obj.id

    if driver_dropdown != '' and driver_dropdown in driver_mapping:
        driver_id = driver_mapping[driver_dropdown]
        car_obj_list = dcd.CarDb.query.filter_by(driver_id=driver_id).all()

        for car_obj in car_obj_list:
            car_list.append({'car_name': car_obj.car_name})
            car_mapping[car_obj.car_name] = car_obj.id

    if not ctx.triggered:
        LOGGER.debug("Race Entry Callback - not triggered - Callback time:%0.02f", time.time() - cb_start_time)
        return driver_list, car_list, updated_car_selected, dash.no_update, dash.no_update, new_url

    car_queued = dash.no_update
    LOGGER.info("Race Entry Callback")

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == CAR_ADD_SEL_BUTTON or button_id == CAR_ADD_ALL_BUTTON:
        car_queued = []
        car_names = []

        if button_id == CAR_ADD_SEL_BUTTON:
            for car_idx in car_available_selected:
                car_name = car_available_data[car_idx]['car_name']
                car_names.append(car_name)
            LOGGER.info("    Clicked Add Selected Car Button %d (%s)", len(car_names), car_names)
        else:
            for car_dict in car_available_data:
                car_names.append(car_dict['car_name'])
            LOGGER.info("    Clicked Add All Cars Button %d (%s)", len(car_names), car_names)

        for car_name in car_names:
            # Check to see if
            found = False
            if car_data is not None:
                for found_car_dict in car_data:
                    if found_car_dict['car_name'] == car_name and found_car_dict['driver_name'] == driver_dropdown:
                        found = True
                        break

            if found is False:
                if car_data is not None and len(car_queued) == 0:
                    for found_car_dict in car_data:
                        car_queued.append(found_car_dict)

                car_queued.append({'car_name': car_name,
                                   'driver_name': driver_dropdown,
                                   'car_id': car_mapping[car_name],
                                   'driver_id': driver_mapping[driver_dropdown]
                                   })

        queued_count = len(car_queued)
        if queued_count == 0:
            LOGGER.info("        All cars already added.")
            car_queued = dash.no_update
        else:
            LOGGER.info("        %d new cars added.", queued_count)

    elif button_id == DRIVER_DROPDOWN:
        LOGGER.info("    Changed selected driver: (%s)", driver_dropdown)
        updated_car_selected = []

    elif button_id == CAR_REMOVE_BUTTON:
        car_queued = []
        car_names = []
        for car_idx, car_data_dict in enumerate(car_data):
            if car_idx in car_data_selected:
                continue
            car_names.append(car_data_dict['car_name'])
            car_queued.append(car_data_dict)
        LOGGER.info("    Remove Car From Race Button Clicked (%s)", car_names)
        updated_car_data_selected = []

    elif button_id == START_RACE_BUTTON:
        if car_data is None or len(car_data) == 0:
            LOGGER.info("    Start New Race Clicked - unable to start race - no cars selected")
            raise PreventUpdate

        LOGGER.info("    Start New Race Clicked")
        race_id = dbd.DB_DATA['DB'].session.query(func.max(dcd.RaceDb.race_id)).first()[0]
        if race_id is None:
            race_id = 0
        race_id += 1

        new_url = f'http://127.0.0.1:8080/race_manager?race_id={race_id}'

        # Shouldn't happen, but delete anything with new race id
        dcd.RaceDb.query.filter_by(race_id=race_id).delete()
        dcd.HeatDb.query.filter_by(race_id=race_id).delete()

        for car_dict in car_data:
            car_obj = dcd.CarDb.query.filter_by(car_name=car_dict['car_name']).first()
            race_obj = dcd.RaceDb(
                {'race_id': race_id, 'car_id': car_obj.id, 'in_race': True, 'buy_ins': 0,
                 'track_left_count': 0, 'track_right_count': 0})
            dbd.DB_DATA['DB'].session.add(race_obj)
            dbd.DB_DATA['DB'].session.commit()

    elif button_id == DRIVER_DELETE_BUTTON:
        LOGGER.info("    Delete Driver from DB (%s)", driver_dropdown)
        driver_id = driver_mapping[driver_dropdown]
        dcd.CarDb.query.filter_by(driver_id=driver_id).delete()
        dcd.DriverDb.query.filter_by(id=driver_id).delete()

        # Should driver data be removed?
        # dcd.RaceDb.query.filter_by(id=driver_id).delete()
        # dcd.HeatDb.query.filter_by(race_id=race_id).delete()

        dbd.DB_DATA['DB'].session.commit()
        driver_list.remove({'label': driver_dropdown, 'value': driver_dropdown})
        car_in_list = []
        for car_dict in car_data:
            if car_dict['driver_id'] == driver_id:
                car_in_list.append(car_dict['car_name'])

        LOGGER.info("        Car in list removed (%s)", car_in_list)

        car_queued = []
        for car_idx, car_data_dict in enumerate(car_data):
            if car_idx in car_data_selected:
                continue
            car_queued.append(car_data_dict)
        updated_car_data_selected = []
        car_list = []

        for car_name in car_in_list:
            car_queued.remove({
                'car_name': car_name,
                'driver_name': driver_dropdown,
                'car_id': car_mapping[car_name],
                'driver_id': driver_id
            })

    if orig_url != new_url and new_url != dash.no_update:
        LOGGER.info("        Changing url\nfrom:%s\n  to:%s", orig_url, new_url)

    LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
    return driver_list, car_list, updated_car_selected, car_queued, updated_car_data_selected, new_url
