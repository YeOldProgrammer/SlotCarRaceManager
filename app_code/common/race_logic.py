import random
import logging
import os
import json
from sqlalchemy import func, desc
import app_code.common.app_logging as al
import app_code.common.config_data as cd
import app_code.common.db_data as dbd
import app_code.common.db_custom_def as dcd
from itertools import combinations

LOGGER = logging.getLogger(al.LOGGER_NAME)


class RaceData:
    def __init__(self):
        self.race_id = 0
        self.heat_id = 0
        self.run_count = 0
        self.orig_car_count = 0
        self.run_data = []
        self.driver_balance = {}
        self.race_obj_list = []
        self.car_name_to_car_id = {}
        self.car_id_to_car_name = {}
        self.driver_name_to_driver_id = {}
        self.driver_id_to_driver_name = {}

    def load_cars(self, race_id, heat_id):
        self.race_id = int(race_id)
        self.heat_id = int(heat_id)
        self.run_count = 0
        self.race_obj_list = []
        self.car_name_to_car_id = {}
        self.car_id_to_car_name = {}
        self.driver_name_to_driver_id = {}
        self.driver_id_to_driver_name = {}
        self.orig_car_count = 0

        orig_race_obj_list = dcd.RaceDb.query.\
            filter_by(race_id=self.race_id).\
            all()
        self.orig_car_count = len(orig_race_obj_list)

        self.race_obj_list = dcd.RaceDb.query.\
            filter_by(race_id=self.race_id).\
            filter_by(in_race=True).\
            all()

        for race_obj in self.race_obj_list:
            car_obj = dcd.CarDb.query.filter_by(id=race_obj.car_id).first()
            driver_obj = dcd.DriverDb.query.filter_by(id=car_obj.driver_id).first()
            self.car_name_to_car_id[car_obj.car_name] = {
                'car_id': car_obj.id,
                'driver_name': driver_obj.driver_name,
                'driver_id': driver_obj.id,
            }

            self.car_id_to_car_name[car_obj.id] = {
                'car_name': car_obj.car_name,
                'driver_name': driver_obj.driver_name,
                'driver_id': driver_obj.id,
            }

            self.driver_name_to_driver_id[driver_obj.driver_name] = driver_obj.id
            self.driver_id_to_driver_name[driver_obj.id] = driver_obj.driver_name

    def build_race(self):
        LOGGER.info("    build_race")
        retry_count = 0
        shuffle_count = 0
        max_retries = 20
        while True:
            if retry_count > max_retries:
                LOGGER.info("        Max shuffles reached")
                break

            if self.shuffle_cars() is True:
                break
            retry_count += 1

        self.display_balance()
        self.load_run()

    def next_heat(self):
        # Check if race is in complete state
        race_obj_list = dcd.RaceDb.query. \
            filter_by(race_id=self.race_id). \
            filter_by(in_race=True). \
            all()

        run_obj_list = dcd.HeatDb.query.\
            filter_by(race_id=self.race_id).\
            filter_by(heat_id=self.heat_id).\
            order_by(dcd.HeatDb.run_id).\
            all()

        # Make each run has a winner
        for run_obj in run_obj_list:
            if run_obj.win_id == cd.VALUE_NO_WINNER:
                return "Not all runs have a winner declared"

            for race_obj in race_obj_list:
                if (run_obj.win_id == cd.VALUE_LEFT_WINNER and run_obj.car_id_right == race_obj.car_id) or \
                        (run_obj.win_id == cd.VALUE_RIGHT_WINNER and run_obj.car_id_left == race_obj.car_id):
                    race_obj.in_race = False

                elif run_obj.win_id == cd.VALUE_LEFT_WINNER and run_obj.car_id_left == race_obj.car_id:
                    race_obj.track_left_count += 1

                elif run_obj.win_id == cd.VALUE_RIGHT_WINNER and run_obj.car_id_right == race_obj.car_id:
                    race_obj.track_right_count += 1

        dbd.DB_DATA['DB'].session.commit()
        return ''

    def display_balance(self):
        LOGGER.info("        Balance")
        for driver in sorted(self.driver_balance):
            total = self.driver_balance[driver]['left'] + self.driver_balance[driver]['right']
            if total > 0:
                percent = max(self.driver_balance[driver]['left'], self.driver_balance[driver]['right']) / total * 100
            else:
                percent = 0
            LOGGER.info("            %-20s left=%2d right=%2d total=%2d (%3d%%)",
                        driver,
                        self.driver_balance[driver]['left'],
                        self.driver_balance[driver]['right'],
                        total,
                        percent
                        )

    def load_run(self):
        run_obj_list = dcd.HeatDb.query.\
            filter_by(race_id=self.race_id).\
            filter_by(heat_id=self.heat_id).\
            order_by(dcd.HeatDb.run_id).\
            all()

        self.run_count = len(run_obj_list)

        run_id = 0
        for run_obj in run_obj_list:
            car_id_1 = run_obj.car_id_left
            car_name_1 = self.car_id_to_car_name[car_id_1]['car_name']
            driver_name_1 = self.car_id_to_car_name[car_id_1]['driver_name']
            driver_id_1 = self.car_id_to_car_name[car_id_1]['driver_id']
            key1 = driver_name_1 + ':' + car_name_1

            if run_obj.car_id_right > 0:
                car_id_2 = run_obj.car_id_right
                car_name_2 = self.car_id_to_car_name[car_id_2]['car_name']
                driver_name_2 = self.car_id_to_car_name[car_id_2]['driver_name']
                driver_id_2 = self.car_id_to_car_name[car_id_2]['driver_id']
                key2 = driver_name_2 + ':' + car_name_2

                self.run_data.append({
                    'run_id': run_id,
                    'odd': run_obj.odd,
                    'selected': run_obj.win_id,
                    'cars': [
                        {
                            'driver': driver_name_1,
                            'driver_id': driver_id_1,
                            'car': car_name_1,
                            'car_id': car_id_1,
                            'key': key1
                        },
                        {
                            'driver': driver_name_2,
                            'driver_id': driver_id_2,
                            'car': car_name_2,
                            'car_id': car_id_2,
                            'key': key2
                        }
                    ]
                })
                run_id += 1
            else:
                self.run_data.append({
                    'run_id': run_id,
                    'odd': run_obj.odd,
                    'selected': run_obj.win_id,
                    'cars': [
                        {
                            'driver': driver_name_1,
                            'driver_id': driver_id_1,
                            'car': car_name_1,
                            'car_id': car_id_1,
                            'key': key1
                        }
                    ]
                })
                run_id += 1

    def shuffle_cars(self):
        drivers = {}
        remaining_car_keys = []
        remaining_car_keys_by_driver = {}
        racer_combos = []
        heat_to_add_list = []

        LOGGER.info("        Shuffle")
        self.driver_balance = {}

        # Build up the pool of available drivers and cars
        racer_count, car_count, race_count, odd_car_count = self.build_available_drivers_and_cars(
            drivers, remaining_car_keys, remaining_car_keys_by_driver, racer_combos)

        run_id = 0
        while len(remaining_car_keys) > 1:
            random.shuffle(racer_combos)
            for combo in racer_combos:
                try:
                    if len(remaining_car_keys) < 2:
                        break

                    driver1 = combo[0]
                    driver2 = combo[1]
                    car_count_left = len(remaining_car_keys_by_driver[driver1])
                    car_count_right = len(remaining_car_keys_by_driver[driver2])

                    random.shuffle(remaining_car_keys_by_driver[driver1])
                    random.shuffle(remaining_car_keys_by_driver[driver2])
                    car1 = remaining_car_keys_by_driver[driver1][0]

                    if driver1 == driver2:
                        car2 = remaining_car_keys_by_driver[driver2][1]
                    else:
                        car2 = remaining_car_keys_by_driver[driver2][0]

                    key1 = driver1 + ':' + car1
                    key2 = driver2 + ':' + car2
                    remaining_car_keys_by_driver[driver1].remove(car1)
                    remaining_car_keys_by_driver[driver2].remove(car2)
                    remaining_car_keys.remove(key1)
                    remaining_car_keys.remove(key2)
                    run_id += 1

                    if car_count_left > 0 and car_count_right > 0:
                        odd = False
                        rand_num = random.randint(0, 1)
                        balance = [
                            self.driver_balance[driver1]['left'] - self.driver_balance[driver2]['left'],
                            self.driver_balance[driver1]['right'] - self.driver_balance[driver2]['right'],
                        ]

                        LOGGER.info("            race_id=%2d, heat_id=%2d, run_id=%2d, odd=%-5s, "
                                    "car_id_left=%3d (%-15s) %2d/%2d, "
                                    "car_id_right=%3d (%-15s) %2d/%2d, "
                                    "win_id=%d (rand=%d, bal=%d/%d)",
                                    self.race_id,
                                    self.heat_id,
                                    run_id,
                                    odd,
                                    self.car_name_to_car_id[car1]['car_id'],
                                    car1,
                                    self.driver_balance[driver1]['left'],
                                    self.driver_balance[driver1]['right'],
                                    self.car_name_to_car_id[car2]['car_id'],
                                    car2,
                                    self.driver_balance[driver2]['left'],
                                    self.driver_balance[driver2]['right'],
                                    0,
                                    rand_num,
                                    balance[0],
                                    balance[1]
                                    )

                        # Balance drivers
                        if balance[0] > 0:
                            reverse_sides = 'l'
                        elif balance[1] < 0:
                            reverse_sides = 'r'
                        # elif self.driver_balance[driver1]['left'] == self.driver_balance[driver2]['right'] and rand_num == 1:
                        #     reverse_sides = 'r'
                        else:
                            reverse_sides = ''

                        if reverse_sides != '':
                            car_tmp = car1
                            car1 = car2
                            car2 = car_tmp
                            driver_tmp = driver1
                            driver1 = driver2
                            driver2 = driver_tmp
                            LOGGER.info("                    R%s  heat_id=%2d, run_id=%2d, odd=%-5s, "
                                        "car_id_left=%3d (%-15s) %2d/%2d, "
                                        "car_id_right=%3d (%-15s) %2d/%2d, "
                                        "win_id=%d",
                                        reverse_sides,
                                        self.heat_id,
                                        run_id,
                                        odd,
                                        self.car_name_to_car_id[car1]['car_id'],
                                        car1,
                                        self.driver_balance[driver1]['left'],
                                        self.driver_balance[driver1]['right'],
                                        self.car_name_to_car_id[car2]['car_id'],
                                        car2,
                                        self.driver_balance[driver2]['left'],
                                        self.driver_balance[driver2]['right'],
                                        cd.VALUE_NO_WINNER,
                                        )

                        self.driver_balance[driver1]['left'] += 1
                        self.driver_balance[driver2]['right'] += 1

                        heat_obj = dcd.HeatDb({'race_id': self.race_id,
                                               'heat_id': self.heat_id,
                                               'run_id': run_id,
                                               'car_id_left': self.car_name_to_car_id[car1]['car_id'],
                                               'car_id_right': self.car_name_to_car_id[car2]['car_id'],
                                               'win_id': cd.VALUE_NO_WINNER,
                                               'odd': odd,
                                               })

                        heat_to_add_list.append(heat_obj)

                    if len(remaining_car_keys) > 1:
                        break

                except Exception as error_str:
                    LOGGER.error("Exception occurred %s", error_str, exc_info=True)
                    return False

            # Remove racer combos that are no longer valid
            if self.remove_empty_racer_combos(racer_combos, remaining_car_keys_by_driver) is False:
                return False

            if len(racer_combos) == 0:
                break

        if odd_car_count is True:
            driver1 = remaining_car_keys[0].split(':')[0]
            car1 = remaining_car_keys_by_driver[driver1][0]
            key1 = driver1 + ':' + car1
            remaining_car_keys_by_driver[driver1].remove(car1)
            remaining_car_keys.remove(key1)
            run_id += 1

            odd = True
            LOGGER.info("            race_id=%2d, heat_id=%2d, run_id=%2d, odd=%-5s, "
                        "car_id_left=%3d (%-15s) %2d/%2d, "
                        "                                          "
                        "win_id=%d",
                        self.race_id,
                        self.heat_id,
                        run_id,
                        odd,
                        self.car_name_to_car_id[car1]['car_id'],
                        car1,
                        self.driver_balance[driver1]['left'],
                        self.driver_balance[driver1]['right'],
                        cd.VALUE_LEFT_WINNER,
                        )

            self.driver_balance[driver1]['left'] += 1

            heat_obj = dcd.HeatDb({'race_id': self.race_id,
                                   'heat_id': self.heat_id,
                                   'run_id': run_id,
                                   'car_id_left': self.car_name_to_car_id[car1]['car_id'],
                                   'car_id_right': 0,
                                   'win_id': cd.VALUE_LEFT_WINNER,
                                   'odd': odd,
                                   })
            heat_to_add_list.append(heat_obj)

        # If the pattern did not work, try again :)
        if len(remaining_car_keys) > 1:
            return False

        # Remove this Heat's data
        dcd.HeatDb.query.filter_by(race_id=self.race_id, heat_id=self.heat_id).delete()
        dbd.DB_DATA['DB'].session.commit()
        for heat_obj in heat_to_add_list:
            dbd.DB_DATA['DB'].session.add(heat_obj)
        dbd.DB_DATA['DB'].session.commit()

        return True

    def build_available_drivers_and_cars(self, drivers, remaining_car_keys, remaining_car_keys_by_driver, racer_combos):
        # Build up the pool of available drivers and cars
        for race_obj in self.race_obj_list:
            car_name = self.car_id_to_car_name[race_obj.car_id]['car_name']
            driver_name = self.car_id_to_car_name[race_obj.car_id]['driver_name']

            if driver_name not in drivers:
                self.driver_balance[driver_name] = {'left': 0, 'right': 0}
                drivers[driver_name] = 1
                remaining_car_keys_by_driver[driver_name] = []
            else:
                drivers[driver_name] += 1

            key = driver_name + ':' + car_name
            if key not in remaining_car_keys:
                remaining_car_keys.append(key)

            if car_name not in remaining_car_keys_by_driver[driver_name]:
                remaining_car_keys_by_driver[driver_name].append(car_name)

        racer_count = len(drivers)
        car_count = len(remaining_car_keys)
        race_count = int(car_count / 2)
        if car_count % 2 == 1:
            odd_car_count = True
        else:
            odd_car_count = False

        for combo in combinations(list(drivers.keys()), 2):
            racer_combos.append(combo)

        return racer_count, car_count, race_count, odd_car_count

    def remove_empty_racer_combos(self, racer_combos, remaining_car_keys_by_driver):
        total_cars_remaining = 0
        driver_count = 0
        last_driver_name = ''
        for driver_name in remaining_car_keys_by_driver:
            cars_remaining = len(remaining_car_keys_by_driver[driver_name])
            if cars_remaining > 0:
                driver_count += 1
                total_cars_remaining += cars_remaining
                last_driver_name = driver_name

        while True:
            delete_idx = None
            for idx, value in enumerate(racer_combos):
                if len(remaining_car_keys_by_driver[value[0]]) == 0 or \
                        len(remaining_car_keys_by_driver[value[1]]) == 0:
                    delete_idx = idx
                    break

            if delete_idx is None:
                break

            del racer_combos[delete_idx]

        if driver_count == 1:
            racer_combos.append((last_driver_name, last_driver_name))

    def display_race_info(self):
        LOGGER.info("    Race Data Dump")
        for run_id, run_dict in enumerate(self.run_data):
            car_one = run_dict['cars'][0]
            if run_dict['selected'] == cd.VALUE_NO_WINNER:
                sel_data = '     '
            elif run_dict['selected'] == cd.VALUE_LEFT_WINNER:
                sel_data = '<----'
            elif run_dict['selected'] == cd.VALUE_RIGHT_WINNER:
                sel_data = '---->'
            else:
                sel_data = '?????'

            if len(run_dict['cars']) > 1:
                car_two = run_dict['cars'][1]
                run_data_str = "        | %4d (%4d) | %-5s | %-8s | %-10s (%2d) | %s | %-8s | %-10s (%2d) |" %\
                               (
                                    run_id,
                                    run_dict['run_id'],
                                    run_dict['odd'],
                                    car_one['driver'],
                                    car_one['car'],
                                    car_one['car_id'],
                                    sel_data,
                                    car_two['driver'],
                                    car_two['car'],
                                    car_two['car_id']
                                )
            else:
                run_data_str = "        | %4d (%4d) | %-5s | %-8s | %-10s (%2d) "\
                               "| %s |          |                 |" %\
                               (
                                    run_id,
                                    run_dict['run_id'],
                                    run_dict['odd'],
                                    car_one['driver'],
                                    car_one['car'],
                                    car_one['car_id'],
                                    sel_data,
                                )
            run_id += 1

            LOGGER.info(run_data_str)

    def set_race_info(self, run_id, value):
        run_obj = dcd.HeatDb.query.\
            filter_by(race_id=self.race_id).\
            filter_by(heat_id=self.heat_id).\
            filter_by(run_id=run_id + 1).\
            first()

        if run_obj is None:
            LOGGER.error("HeatDb missing - race_id=%d, heat_id=%d, run_id=%d, value=%d",
                         self.race_id, self.heat_id, run_id, value)
            return

        if value == cd.VALUE_BOTH_WINNER:
            if run_obj.win_id == cd.VALUE_LEFT_WINNER:
                run_obj.win_id = cd.VALUE_RIGHT_WINNER
            else:
                run_obj.win_id = cd.VALUE_LEFT_WINNER
        else:
            run_obj.win_id = value

        dbd.DB_DATA['DB'].session.commit()
        self.run_data[run_id]['selected'] = run_obj.win_id


def list_race():
    LOGGER.info("List Races")

    race_obj_list = dcd.RaceDb. \
        query. \
        distinct(dcd.RaceDb.race_id). \
        order_by(dcd.RaceDb.race_id). \
        all()

    last_val = -1
    for race_obj in race_obj_list:
        if race_obj.race_id == last_val:
            continue
        last_val = race_obj.race_id
        heat_obj = dbd.DB_DATA['DB'].session.query(dcd.HeatDb).\
            filter(dcd.HeatDb.race_id == race_obj.race_id).\
            order_by(dcd.HeatDb.heat_id).first()

        if heat_obj is None:
            LOGGER.info("    Race race_id=%2d heat_id=None", race_obj.race_id)
        else:
            LOGGER.info("    Race race_id=%2d heat_id=%2d", race_obj.race_id, heat_obj.heat_id)


def display_race(race_id):
    heat_obj = dbd.DB_DATA['DB'].session.query(dcd.HeatDb). \
        filter(dcd.HeatDb.race_id == race_id). \
        order_by(dcd.HeatDb.heat_id).first()

    rd_obj = RaceData()
    rd_obj.load_cars(race_id=race_id, heat_id=heat_obj.heat_id)
    rd_obj.load_run()
    rd_obj.display_race_info()


def shuffle_race(race_id):
    heat_obj = dbd.DB_DATA['DB'].session.query(dcd.HeatDb). \
        filter(dcd.HeatDb.race_id == race_id). \
        order_by(dcd.HeatDb.heat_id).first()

    if heat_obj is None:
        LOGGER.error("Race %d does not exist", race_id)
        return

    rd_obj = RaceData()
    rd_obj.load_cars(race_id=race_id, heat_id=heat_obj.heat_id)
    rd_obj.build_race()
    rd_obj.display_race_info()


def load_default_data():
    LOGGER.info("Loading default data")
    race_data_file = os.path.join(cd.ENV_VARS['DATA_DIR'], 'default_race_data.json')

    # If the file does not exist skip this step
    if os.path.exists(race_data_file) is False:
        return

    with open(race_data_file, 'r') as rd_fh:
        race_data = json.load(rd_fh)

    for driver_name in race_data['drivers']:
        driver_obj = dcd.DriverDb.query.filter_by(driver_name=driver_name).first()
        if driver_obj is None:
            driver_obj = dcd.DriverDb({'driver_name': driver_name})
            dbd.DB_DATA['DB'].session.add(driver_obj)
            dbd.DB_DATA['DB'].session.commit()

        for car_name in race_data['drivers'][driver_name]['cars']:
            car_obj = dcd.CarDb.query.filter_by(car_name=car_name).first()
            if car_obj is None:
                car_obj = dcd.CarDb({'driver_id': driver_obj.id, 'car_name': car_name})
                dbd.DB_DATA['DB'].session.add(car_obj)
                dbd.DB_DATA['DB'].session.commit()
