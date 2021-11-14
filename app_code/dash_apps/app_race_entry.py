import dash
import time
import logging
import dash_table
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import app_code.common.db_data as dbd
import dash_html_components as html
from sqlalchemy import func, case
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import app_code.common.web_logic as wl
from app_code.common import app_logging as al
from app_code.common import config_data as cd
from app_code.common.dash_util import dash_kwarg
import app_code.common.db_custom_def as dcd
import app_code.dash_apps.app_layouts as ala

LOGGER = logging.getLogger(al.LOGGER_NAME)

BASE_ID = 'are_'
CONFIRM_ID = BASE_ID + 'confirm_id'
START_RACE_BUTTON = BASE_ID + 'start_race'
ADD_DRIVER_MODAL = BASE_ID + 'add_driver_modal'
ADD_DRIVER_OPEN = BASE_ID + 'add_driver_button_open'
ADD_DRIVER_INPUT = BASE_ID + 'add_driver_input'
ADD_DRIVER_INSERT = BASE_ID + 'add_driver_button_insert'
ADD_DRIVER_CANCEL = BASE_ID + 'add_driver_button_cancel'
DRIVER_DELETE_BUTTON = BASE_ID + 'driver_delete'
RACE_ENTRIES = BASE_ID + 'race_entries'
RACE_DRIVERS = BASE_ID + 'race_drivers'

ERROR_PROMPT_MODAL = BASE_ID + 'error_prompt_modal'
ERROR_PROMPT_OPEN = BASE_ID + 'error_prompt_open'

ADD_CAR_MODAL = BASE_ID + 'add_car_modal'
ADD_CAR_OPEN = BASE_ID + 'add_car_button_open'
ADD_CAR_INPUT = BASE_ID + 'add_car_input'
ADD_CAR_INSERT = BASE_ID + 'add_car_button_insert'
ADD_CAR_REFRESH = BASE_ID + 'add_car_button_refresh'
ADD_CAR_CANCEL = BASE_ID + 'add_car_button_cancel'
ADD_CAR_DRIVER_LABEL = BASE_ID + 'add_car_driver_label'

DRIVER_DROPDOWN = BASE_ID + 'driver_dropdown'
CAR_AVAILABLE_TABLE = BASE_ID + 'car_available_table'
RACE_PARTICIPANTS_TABLE = BASE_ID + 'race_participants_table'
CAR_DELETE_BUTTON = BASE_ID + 'car_del'
CAR_ADD_SEL_BUTTON = BASE_ID + 'car_add_sel'
CAR_ADD_ALL_BUTTON = BASE_ID + 'car_add_all'
CAR_REMOVE_FROM_RACE_BUTTON = BASE_ID + 'car_remove'
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
        dbc.Col(html.Img(src=wl.DASH_APP.get_asset_url(cd.ENV_VARS['LOGO_FILE']), style={'margin-left': '20px'})),
    ]),
    dbc.Row([
        dbc.Col(
            [
                html.H3("Drivers: 0", id=RACE_DRIVERS),
                html.H3("Entries: 0", id=RACE_ENTRIES),
                dash_table.DataTable(
                    id=RACE_PARTICIPANTS_TABLE,
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
                        'color': 'white',
                        'textAlign': 'left'
                    },
                ),
                dbc.Button('Remove from race', id=CAR_REMOVE_FROM_RACE_BUTTON,
                            style={'margin-top': '10px', 'width': '100%'}),
            ],
            width='auto',
            style={"border": "2px black solid", 'padding': '20px', 'margin-left': '50px'}
        ),
        dbc.Col(
            [
                html.H3("Available Drivers"),
                dcc.Dropdown(id=DRIVER_DROPDOWN, value='', style={'color': 'black'}),
                dbc.Row([
                    # dbc.Col([
                    #     dbc.Button('Delete Driver from DB (and all associated cars)',
                    #                id=DRIVER_DELETE_BUTTON, style={'margin-left': '20px'}),
                    # ], width='auto'),
                    dbc.Col([
                        dbc.Button("Add New Driver", id=ADD_DRIVER_OPEN, style={'margin-left': '20px'}),
                    ], width='auto'),
                    dbc.Col([
                        dbc.Button('Delete Driver from DB (and all associated cars)',
                                   id=DRIVER_DELETE_BUTTON, style={'margin-left': '20px'}),
                        # dcc.ConfirmDialogProvider(
                        #     children=html.Button('Delete Driver from DB (and all associated cars)'),
                        #     id=DRIVER_DELETE_BUTTON,
                        #     message='Are you sure you want to delete this driver from the DB?',
                        # ),
                    ], width='auto'),
                ]),
                html.H3("Available Cars", style={'margin-top': '20px'}),
                dash_table.DataTable(
                    id=CAR_AVAILABLE_TABLE,
                    columns=[
                        {'name': 'Car', 'id': 'car_name', 'type': 'text'},
                        {'name': 'Races', 'id': 'races', 'type': 'int'},
                        {'name': 'Heat Wins', 'id': 'heat_wins', 'type': 'int'},
                        {'name': 'Heat Losses', 'id': 'heat_losses', 'type': 'int'},
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
                        'color': 'white',
                        'textAlign': 'left'
                    },
                ),
                dbc.Button(id=ERROR_PROMPT_OPEN, n_clicks=0, style={'display': 'none'}),
                dbc.Alert(
                    "A driver is not selected",
                    id=ERROR_PROMPT_MODAL,
                    dismissable=True,
                    fade=False,
                    is_open=False,
                ),

                dbc.Button('Add Selected Car(s)', id=CAR_ADD_SEL_BUTTON, style={'margin-left': '20px'}),
                dbc.Button('Add All Car(s)', id=CAR_ADD_ALL_BUTTON, style={'margin-left': '20px'}),
                dbc.Button('Add New Car', id=ADD_CAR_OPEN, style={'margin-left': '20px'}),
                dbc.Button('Delete Selected Cars from DB', id=CAR_DELETE_BUTTON, style={'margin-left': '20px'}),
                dbc.Button('Refresh', id=ADD_CAR_REFRESH, style={'margin-left': '20px', 'display': 'none'}),
            ],
            width='auto',
            style={"border": "2px black solid", 'padding': '20px', 'margin-left': '50px'}
        ),],
        style={'margin-top': '20px'}
    ),
    dbc.Button('Start New Race', id=START_RACE_BUTTON,
               style={'margin-left': '50px', 'margin-top': '10px'}),

    # Add New Driver
    dbc.Modal(
        [
            dbc.ModalHeader("Add a new driver"),
            dbc.ModalBody([
                html.H4("Driver Name:"),
                dcc.Input(id=ADD_DRIVER_INPUT, type="text", placeholder="", style={'width': '100%'}),
            ], style={'display': 'inline-block'}),
            dbc.ModalFooter([
                dbc.Button("Insert Driver", id=ADD_DRIVER_INSERT, className="ml-auto"),
                dbc.Button("Cancel", id=ADD_DRIVER_CANCEL, className="ml-auto"),
            ]),
        ],
        id=ADD_DRIVER_MODAL,
    ),

    # Add New Car
    dbc.Modal(
        [
            dbc.ModalHeader(id=ADD_CAR_DRIVER_LABEL, children="HEADER"),
            dbc.ModalBody([
                html.H4("Car Names (one per line):"),
                dcc.Textarea(id=ADD_CAR_INPUT, rows=10, style={'width': '100%'}),
            ], style={'display': 'inline-block'}),
            dbc.ModalFooter([
                dbc.Button("Insert Car", id=ADD_CAR_INSERT, className="ml-auto"),
                dbc.Button("Cancel", id=ADD_CAR_CANCEL, className="ml-auto"),
            ]),
        ],
        id=ADD_CAR_MODAL,
    ),

])


@wl.DASH_APP.callback(
    [
        Output(DRIVER_DROPDOWN, 'options'),
        # Output(DRIVER_DROPDOWN, 'value'),
        Output(CAR_AVAILABLE_TABLE, 'data'),
        Output(CAR_AVAILABLE_TABLE, 'selected_rows'),
        Output(RACE_PARTICIPANTS_TABLE, 'data'),
        Output(RACE_PARTICIPANTS_TABLE, 'selected_rows'),
        Output(URL_ID, 'href'),
        Output(ADD_CAR_OPEN, 'style'),
        Output(RACE_ENTRIES, 'children'),
        Output(RACE_DRIVERS, 'children')
    ],
    [
        Input(DRIVER_DROPDOWN, 'value'),
        Input(DRIVER_DELETE_BUTTON, 'n_clicks'),
        Input(CAR_ADD_SEL_BUTTON, 'n_clicks'),
        Input(CAR_ADD_ALL_BUTTON, 'n_clicks'),
        Input(CAR_DELETE_BUTTON, 'n_clicks'),
        Input(CAR_REMOVE_FROM_RACE_BUTTON, 'n_clicks'),
        Input(START_RACE_BUTTON, 'n_clicks'),
        Input(ADD_CAR_REFRESH, 'n_clicks'),
    ],
    [
        State(CAR_AVAILABLE_TABLE, 'selected_rows'),
        State(CAR_AVAILABLE_TABLE, 'data'),
        State(RACE_PARTICIPANTS_TABLE, 'selected_rows'),
        State(RACE_PARTICIPANTS_TABLE, 'data'),
        State(URL_ID, 'href')
    ]
)
def display_page(driver_dropdown, driver_delete_n_clicks, car_add_sel_n_clicks,
                 car_add_all_n_clicks, car_delete_n_clicks, car_remove_n_clicks, start_race_n_clicks, refresh_n_clicks,
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
    new_driver = dash.no_update
    display_entries = dash.no_update
    display_drivers = dash.no_update

    if driver_dropdown != '':
        default_add_new_car_style = {'margin-left': '20px'}
    else:
        default_add_new_car_style = {'display': 'none'}

    driver_id = 0
    driver_mapping = {}
    sortable_driver_name = {}
    for driver_obj in driver_obj_list:
        sortable_driver_name[driver_obj.driver_name] = driver_obj

    for driver_name in sorted(sortable_driver_name):
        driver_list.append({'label': driver_name, 'value': driver_name})
        driver_mapping[driver_name] = sortable_driver_name[driver_name].id

    if driver_dropdown != '' and driver_dropdown in driver_mapping:
        driver_id = driver_mapping[driver_dropdown]
        car_obj_list = dcd.CarDb.query.filter_by(driver_id=driver_id).all()

        for car_obj in car_obj_list:
            car_mapping[car_obj.car_name] = car_obj.id
            race_obj_list = dcd.RaceDb.query.filter_by(car_id=car_obj.id).all()
            race_sum_list = dcd.RaceDb.query.add_columns(dcd.RaceDb.car_id,
                                                         func.count(dcd.RaceDb.race_id),
                                                         func.count(dcd.RaceDb.eliminated),
                                                         func.count(case([(dcd.RaceDb.eliminated != 0, 1)])),
                                                         func.sum(dcd.RaceDb.track_left_count),
                                                         func.sum(dcd.RaceDb.track_right_count),
                                                         func.sum(dcd.RaceDb.odd_skips),
                                                         func.count(case([(dcd.RaceDb.buy_back, 1)])),
                                                         func.count(case([(dcd.RaceDb.eliminated == 0, 1)])),
                                                         ).filter_by(
                car_id=car_obj.id).all()

            heat_left_sum_list = dcd.HeatDb.query.add_columns(dcd.HeatDb.car_id_left,
                                                              func.count(dcd.HeatDb.win_id),
                                                              func.count(case([(dcd.HeatDb.win_id == 1, 1)])),
                                                              func.count(case([(dcd.HeatDb.odd, 1)]))).filter_by(
                car_id_left=car_obj.id).all()
            heat_right_sum_list = dcd.HeatDb.query.add_columns(dcd.HeatDb.car_id_right,
                                                               func.count(dcd.HeatDb.win_id),
                                                               func.count(case([(dcd.HeatDb.win_id == 2, 1)])),
                                                               func.count(case([(dcd.HeatDb.odd, 1)]))).filter_by(
                car_id_right=car_obj.id).all()

            race_sum_data = []
            for idx in range(2, 9 + 1):
                if race_sum_list[0][idx] is None:
                    race_sum_data.append(0)
                else:
                    race_sum_data.append(race_sum_list[0][idx])

            data = {
                'race_sum_list': {
                    'races': race_sum_data[0],
                    'eliminated': race_sum_data[2],
                    'track_left_count': race_sum_data[3],
                    'track_right_count': race_sum_data[4],
                    'odd_skips': race_sum_data[5],
                    'buy_back': race_sum_data[6],
                    'heat_wins': race_sum_data[3] + race_sum_data[4],
                    'heat_losses': race_sum_data[2] + race_sum_data[6],
                    'race_wins': race_sum_data[7],
                },
                'total': {
                    'count': heat_left_sum_list[0][2] + heat_right_sum_list[0][2],
                    'win_count': heat_left_sum_list[0][3] + heat_right_sum_list[0][3] - heat_left_sum_list[0][4],
                    'loss_count': (heat_left_sum_list[0][2] + heat_right_sum_list[0][2]) - (heat_left_sum_list[0][3] + heat_right_sum_list[0][3]),
                    'odd': heat_left_sum_list[0][4] + heat_right_sum_list[0][4],
                },
                'heat_left': {
                    'count': heat_left_sum_list[0][2],
                    'win_count': heat_left_sum_list[0][3] - heat_left_sum_list[0][4],
                    'loss_count': heat_left_sum_list[0][2] - heat_left_sum_list[0][3],
                    'odd': heat_left_sum_list[0][4],
                },
                'heat_right': {
                    'count': heat_right_sum_list[0][2],
                    'win_count': heat_right_sum_list[0][3] - heat_right_sum_list[0][4],
                    'loss_count': heat_right_sum_list[0][2] - heat_right_sum_list[0][3],
                    'odd': heat_right_sum_list[0][4],
                },
            }

            car_list.append({
                'car_name': car_obj.car_name,
                'races': race_sum_data[0],
                'race_wins': race_sum_data[7],
                'heat_wins': race_sum_data[3] + race_sum_data[4],
                'heat_losses': race_sum_data[2] + race_sum_data[6],
            })

            a = 1

    if not ctx.triggered:
        LOGGER.debug("Race Entry Callback - not triggered - Callback time:%0.02f", time.time() - cb_start_time)
        # return driver_list, new_driver, car_list, updated_car_selected, dash.no_update, dash.no_update, new_url,\
        #        default_add_new_car_style
        return driver_list, car_list, updated_car_selected, dash.no_update, dash.no_update, new_url,\
               default_add_new_car_style, display_entries, display_drivers

    car_queued = dash.no_update
    LOGGER.info("Race Entry Callback car_list=%s", car_list)

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == CAR_ADD_SEL_BUTTON or button_id == CAR_ADD_ALL_BUTTON:
        car_queued = []
        car_names = []
        driver_names = {}

        if button_id == CAR_ADD_SEL_BUTTON:
            for car_idx in car_available_selected:
                # car_name = car_available_data[car_idx]['car_name']
                car_name = car_list[car_idx]['car_name']
                car_names.append(car_name)
            LOGGER.info("    Clicked Add Selected Car Button %d (%s)", len(car_names), car_names)
        else:
            for car_dict in car_list:
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

        for entry in car_queued:
            driver_names[entry['driver_id']] = True

        queued_count = len(car_queued)
        if queued_count == 0:
            LOGGER.info("        All cars already added.")
            car_queued = dash.no_update
        else:
            LOGGER.info("        %d new cars added.", queued_count)

    elif button_id == DRIVER_DROPDOWN:
        LOGGER.info("    Changed selected driver: (%s) - %d cars", driver_dropdown, len(car_list))
        updated_car_selected = []
        # car_list, updated_car_selected, car_queued, updated_car_data_selected

    elif button_id == CAR_REMOVE_FROM_RACE_BUTTON:
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

        new_url = f"http://{cd.ENV_VARS['IP_ADDRESS']}:8080/race_manager?race_id={race_id}"

        # Shouldn't happen, but delete anything with new race id
        dcd.RaceDb.query.filter_by(race_id=race_id).delete()
        dcd.HeatDb.query.filter_by(race_id=race_id).delete()

        for car_dict in car_data:
            car_obj = dcd.CarDb.query.filter_by(car_name=car_dict['car_name']).first()
            race_obj = dcd.RaceDb(
                {
                    'race_id': race_id,
                    'car_id': car_obj.id,
                    'in_race': True,
                    'eliminated': 0,
                    'buy_back': False,
                    'odd_skips': 0,
                    'track_left_count': 0,
                    'track_right_count': 0
                }
            )
            dbd.DB_DATA['DB'].session.add(race_obj)
            dbd.DB_DATA['DB'].session.commit()

    elif button_id == DRIVER_DELETE_BUTTON:
        if driver_dropdown is None:
            raise PreventUpdate

        LOGGER.info("    Delete Driver from DB (%s)", driver_dropdown)
        if driver_dropdown not in driver_mapping:
            raise PreventUpdate

        driver_id = driver_mapping[driver_dropdown]
        dcd.CarDb.query.filter_by(driver_id=driver_id).delete()
        dcd.DriverDb.query.filter_by(id=driver_id).delete()

        dbd.DB_DATA['DB'].session.commit()
        driver_list.remove({'label': driver_dropdown, 'value': driver_dropdown})

        temp_car_queued = []
        if car_data is not None:
            for queued_dict in car_data:
                if queued_dict['driver_name'] != driver_dropdown:
                    temp_car_queued.append(queued_dict)

        car_queued = temp_car_queued
        car_list = []
        #
        # if car_data is None or len(car_data) == 0:
        #     LOGGER.info("    Delete Driver - unable to start race - no cars selected")
        #     display_entries, display_drivers = get_updated_drivers(car_queued)
        #     car_list = []
        #     updated_car_data_selected = []
        #     return driver_list, car_list, updated_car_selected, car_queued, updated_car_data_selected, new_url, \
        #            default_add_new_car_style, display_entries, display_drivers

        # car_in_list = []
        # for car_dict in car_data:
        #     if car_dict['driver_id'] == driver_id:
        #         car_in_list.append(car_dict['car_name'])
        #
        # LOGGER.info("        Car in list removed (%s)", car_in_list)
        #
        # car_queued = []
        # for car_idx, car_data_dict in enumerate(car_data):
        #     if car_idx in car_data_selected:
        #         continue
        #     car_queued.append(car_data_dict)
        # updated_car_data_selected = []
        # car_list = []
        #
        # for car_name in car_in_list:
        #     car_queued.remove({
        #         'car_name': car_name,
        #         'driver_name': driver_dropdown,
        #         'car_id': car_mapping[car_name],
        #         'driver_id': driver_id
        #     })
        #
        # new_driver = ''

    elif button_id == CAR_DELETE_BUTTON:
        if len(car_available_selected) == 0:
            LOGGER.info("        Nothing to remove")
            raise PreventUpdate

        for idx in car_available_selected:
            car_name = car_list[idx]['car_name']
            dcd.CarDb.query.filter_by(car_name=car_name).delete()

        output_list = []
        for val_dict in car_list:
            remove = False
            for idx in car_available_selected:
                car_name = car_list[idx]['car_name']
                if val_dict['car_name'] == car_name:
                    remove = True

            if remove is False:
                output_list.append(val_dict)

        car_list = output_list
        dbd.DB_DATA['DB'].session.commit()
        updated_car_selected = []

        car_queued = []
        if car_data is not None:
            for car_idx, car_data_dict in enumerate(car_data):
                if car_idx in car_data_selected:
                    continue
                car_queued.append(car_data_dict)

    if orig_url != new_url and new_url != dash.no_update:
        LOGGER.info("        Changing url\nfrom:%s\n  to:%s", orig_url, new_url)

    display_entries, display_drivers = get_updated_drivers(car_queued)
    LOGGER.info("    Callback time:%0.02f", time.time() - cb_start_time)
    # return driver_list, new_driver, car_list, updated_car_selected, car_queued, updated_car_data_selected, new_url,\
    #        default_add_new_car_style
    return driver_list, car_list, updated_car_selected, car_queued, updated_car_data_selected, new_url,\
           default_add_new_car_style, display_entries, display_drivers


def get_updated_drivers(car_queued):
    driver_names = {}
    if car_queued == dash.no_update:
        return dash.no_update, dash.no_update

    queued_count = len(car_queued)
    for entry in car_queued:
        driver_names[entry['driver_id']] = True

    driver_count = len(driver_names)
    display_drivers = 'Drivers: %d' % driver_count
    display_entries = 'Entries: %d' % queued_count
    return display_entries, display_drivers


@wl.DASH_APP.callback(
    [
        Output(ADD_DRIVER_MODAL, "is_open"),
        Output(DRIVER_DROPDOWN, "value"),
        Output(ADD_DRIVER_INPUT, "value"),
    ],
    [
        Input(ADD_DRIVER_OPEN, "n_clicks"),
        Input(ADD_DRIVER_INSERT, "n_clicks"),
        Input(ADD_DRIVER_CANCEL, "n_clicks"),
    ],
    [
        State(ADD_DRIVER_MODAL, "is_open"),
        State(ADD_DRIVER_INPUT, "value")
    ],
)
def modal_add_driver(open_button, insert_button, cancel_button, is_open, driver_input):
    if not open_button and not insert_button and not cancel_button:
        return is_open, dash.no_update, dash.no_update

    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == ADD_DRIVER_INSERT:
        LOGGER.info("ADD Driver (%s)", driver_input)
        driver_exist = dcd.DriverDb.query.filter_by(driver_name=driver_input).first()
        if driver_exist:
            return False, driver_input, ''

        driver_obj = dcd.DriverDb({'driver_name': driver_input})
        dbd.DB_DATA['DB'].session.add(driver_obj)
        dbd.DB_DATA['DB'].session.commit()
        return False, driver_input, ''

    return not is_open, dash.no_update, dash.no_update


@wl.DASH_APP.callback(
    Output(ADD_CAR_MODAL, "is_open"),
    Output(ADD_CAR_DRIVER_LABEL, "children"),
    Output(ADD_CAR_INPUT, "value"),
    Output(ADD_CAR_REFRESH, 'n_clicks'),
    [
        Input(ADD_CAR_OPEN, "n_clicks"),
        Input(ADD_CAR_INSERT, "n_clicks"),
        Input(ADD_CAR_CANCEL, "n_clicks")
    ],
    [
        State(ADD_CAR_MODAL, "is_open"),
        State(DRIVER_DROPDOWN, "value"),
        State(ADD_CAR_INPUT, "value"),
        State(ADD_CAR_REFRESH, 'n_clicks'),
    ],
)
def modal_add_car(open_button, insert_button, cancel_button, is_open, driver_name, car_input, refresh_n_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, '', '', dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == ADD_CAR_OPEN:
        if driver_name:
            add_header = 'Add new car for ' + driver_name
        else:

            add_header = 'No driver specified to add new cars for'
        return True, add_header, '', dash.no_update

    elif button_id == ADD_CAR_CANCEL:
        return False, dash.no_update, '', dash.no_update

    elif button_id != ADD_CAR_INSERT:
        LOGGER.error("Unknown button ID received '%s'", button_id)
        return False, dash.no_update, '', dash.no_update

    driver_obj = dcd.DriverDb.query.filter_by(driver_name=driver_name).first()
    if driver_obj is None:
        LOGGER.error("Unknown button ID received '%s'", button_id)
        return False, dash.no_update, '', dash.no_update

    car_name_list = car_input.split("\n")
    for car_name in car_name_list:
        car_name = car_name.strip()
        if car_name == '':
            continue

        LOGGER.info("ADD Driver (%s)", car_name)
        car_obj = dcd.CarDb({'driver_id': driver_obj.id, 'car_name': car_name})
        dbd.DB_DATA['DB'].session.add(car_obj)

    dbd.DB_DATA['DB'].session.commit()

    if refresh_n_clicks is None:
        refresh_n_clicks = 0

    refresh_value = refresh_n_clicks + 1
    return False, dash.no_update, '', refresh_value


@wl.DASH_APP.callback(
    Output(ERROR_PROMPT_MODAL, "is_open"),
    [Input(ERROR_PROMPT_OPEN, "n_clicks")],
    [State(ERROR_PROMPT_MODAL, "is_open")],
)
def toggle_alert(n, is_open):
    if n:
        return not is_open
    return is_open
