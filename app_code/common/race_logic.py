import random
import logging
import os
import json
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
        self.run_data = []
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
        while True:
            if self.shuffle_cars() is True:
                break
            retry_count += 1

        self.load_run()

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

    def shuffle_cars(self):
        drivers = []
        remaining_car_keys = []
        remaining_car_keys_by_driver = {}

        LOGGER.info("        Shuffle")

        for race_obj in self.race_obj_list:
            car_name = self.car_id_to_car_name[race_obj.car_id]['car_name']
            driver_name = self.car_id_to_car_name[race_obj.car_id]['driver_name']
            if driver_name not in drivers:
                drivers.append(driver_name)
                remaining_car_keys_by_driver[driver_name] = []

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

        # Remove this Heat's data
        dcd.HeatDb.query.filter_by(race_id=self.race_id, heat_id=self.heat_id).delete()

        racer_combos = []
        for combo in combinations(drivers, 2):
            racer_combos.append(combo)

        run_id = 0
        while len(remaining_car_keys) > 1:
            random.shuffle(racer_combos)
            for combo in racer_combos:
                driver1 = combo[0]
                driver2 = combo[1]
                if len(remaining_car_keys_by_driver[driver1]) > 0 and \
                        len(remaining_car_keys_by_driver[driver2]) > 0:
                    random.shuffle(remaining_car_keys_by_driver[driver1])
                    random.shuffle(remaining_car_keys_by_driver[driver2])
                    car1 = remaining_car_keys_by_driver[driver1][0]
                    car2 = remaining_car_keys_by_driver[driver2][0]
                    key1 = driver1 + ':' + car1
                    key2 = driver2 + ':' + car2
                    remaining_car_keys_by_driver[driver1].remove(car1)
                    remaining_car_keys_by_driver[driver2].remove(car2)
                    remaining_car_keys.remove(key1)
                    remaining_car_keys.remove(key2)
                    run_id += 1

                    odd = False
                    heat_obj = dcd.HeatDb({'race_id': self.race_id,
                                           'heat_id': self.heat_id,
                                           'run_id': run_id,
                                           'car_id_left': self.car_name_to_car_id[car1]['car_id'],
                                           'car_id_right': self.car_name_to_car_id[car2]['car_id'],
                                           'win_id': 0,
                                           'odd': odd,
                                           })

                    LOGGER.info("            race_id=%2d, heat_id=%2d, run_id=%2d, odd=%-5s, car_id_left=%3d, "
                                "car_id_right=%3d, win_id=%d", self.race_id, self.heat_id, run_id, odd,
                                self.car_name_to_car_id[car1]['car_id'],
                                self.car_name_to_car_id[car2]['car_id'],
                                0
                                )

                    dbd.DB_DATA['DB'].session.add(heat_obj)
                    dbd.DB_DATA['DB'].session.commit()

                if len(remaining_car_keys) > 1:
                    break

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

            if len(racer_combos) == 0:
                break

        # If the pattern did not work, try again :)
        if len(remaining_car_keys) <= 1:
            return True

        return False

    def display_race_info(self):
        LOGGER.info("    Race Data Dump")
        for run_id, run_dict in enumerate(self.run_data):
            car_one = run_dict['cars'][0]
            car_two = run_dict['cars'][1]
            if run_dict['selected'] == cd.VALUE_NO_WINNER:
                sel_data = '     '
            elif run_dict['selected'] == cd.VALUE_LEFT_WINNER:
                sel_data = '<----'
            elif run_dict['selected'] == cd.VALUE_RIGHT_WINNER:
                sel_data = '---->'
            else:
                sel_data = '?????'

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


def load_default_data():
    race_data_file = os.path.join(cd.ENV_VARS['DATA_DIR'], 'race_data.json')

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
