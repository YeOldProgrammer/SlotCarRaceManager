import logging
from app_code.common import app_logging as al, db_data as dbd

LOGGER = logging.getLogger(al.LOGGER_NAME)

DB_BASE = dbd.DB_DATA['DB'].Model
DB_BOOL = dbd.DB_DATA['DB'].Boolean
DB_COLUMN = dbd.DB_DATA['DB'].Column
DB_INTEGER = dbd.DB_DATA['DB'].Integer
DB_STRING = dbd.DB_DATA['DB'].String
DB_DATETIME = dbd.DB_DATA['DB'].DateTime
UNIQUE_CONSTRAINT = dbd.DB_DATA['DB'].UniqueConstraint
RELATIONSHIP = dbd.DB_DATA['DB'].relationship
FOREIGN_KEY = dbd.DB_DATA['DB'].ForeignKey


class DriverDb(DB_BASE):
    __tablename__ = 'driver_table'
    __table_args__ = {'extend_existing': True}
    __bind_key__ = dbd.APP_DB

    id = DB_COLUMN(DB_INTEGER, primary_key=True, autoincrement=True)
    driver_name = DB_COLUMN(DB_STRING, nullable=False)
    email = DB_COLUMN(DB_STRING, nullable=True)
    UNIQUE_CONSTRAINT(driver_name)
    car_data = RELATIONSHIP('CarDb', backref='CarDb.driver_id',
                            primaryjoin='DriverDb.id==CarDb.driver_id', lazy='joined')

    def __repr__(self):
        return f"{self.__class__}-{self.entity_key}-{self.racer_name}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, job_dict):
        for key in job_dict:
            setattr(self, key, job_dict[key])


class CarDb(DB_BASE):
    __tablename__ = 'car_table'
    __table_args__ = {'extend_existing': True}
    __bind_key__ = dbd.APP_DB

    id = DB_COLUMN(DB_INTEGER, primary_key=True, autoincrement=True)
    car_name = DB_COLUMN(DB_STRING, nullable=False)
    driver_id = DB_COLUMN(DB_INTEGER, FOREIGN_KEY(DriverDb.id), nullable=False)
    race_data = RELATIONSHIP('RaceDb', backref='RaceDb.car_id',
                             primaryjoin='CarDb.id==RaceDb.car_id', lazy='joined')
    UNIQUE_CONSTRAINT(car_name)

    def __repr__(self):
        return f"{self.__class__}-{self.driver_id}-{self.car_name}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, job_dict):
        for key in job_dict:
            setattr(self, key, job_dict[key])


class RaceDb(DB_BASE):
    __tablename__ = 'race_table'
    __table_args__ = {'extend_existing': True}
    __bind_key__ = dbd.APP_DB

    id = DB_COLUMN(DB_INTEGER, primary_key=True, autoincrement=True)
    race_id = DB_COLUMN(DB_INTEGER, nullable=False)
    car_id = DB_COLUMN(DB_INTEGER, FOREIGN_KEY(CarDb.id), nullable=False)
    in_race = DB_COLUMN(DB_BOOL, nullable=False)
    buy_ins = DB_COLUMN(DB_INTEGER, nullable=False)
    track_left_count = DB_COLUMN(DB_INTEGER, nullable=False)
    track_right_count = DB_COLUMN(DB_INTEGER, nullable=False)

    UNIQUE_CONSTRAINT(race_id, car_id)

    def __repr__(self):
        return f"{self.__class__}-race_id_{self.race_id}-car_id_{self.car_id}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, job_dict):
        for key in job_dict:
            setattr(self, key, job_dict[key])


class HeatDb(DB_BASE):
    __tablename__ = 'heat_table'
    __table_args__ = {'extend_existing': True}
    __bind_key__ = dbd.APP_DB

    id = DB_COLUMN(DB_INTEGER, primary_key=True, autoincrement=True)
    run_id = DB_COLUMN(DB_INTEGER, nullable=False)
    heat_id = DB_COLUMN(DB_INTEGER, nullable=False)
    race_id = DB_COLUMN(DB_INTEGER, FOREIGN_KEY(RaceDb.id), nullable=False)
    car_id_left = DB_COLUMN(DB_INTEGER, FOREIGN_KEY(CarDb.id), nullable=False)
    car_id_right = DB_COLUMN(DB_INTEGER, FOREIGN_KEY(CarDb.id), nullable=False)
    win_id = DB_COLUMN(DB_INTEGER, nullable=False)
    odd = DB_COLUMN(DB_BOOL, nullable=False)

    UNIQUE_CONSTRAINT(race_id, car_id_left, car_id_right)

    def __repr__(self):
        return f"{self.__class__}-race_id_{self.race_id}-heat_id_{self.heat_id}-run_id_{self.id}" + \
               f"-car_id_left{self.car_id_left}-car_id_right{self.car_id_right}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, job_dict):
        for key in job_dict:
            setattr(self, key, job_dict[key])


def create_db():
    dbd.DB_DATA['DB'].create_all()


create_db()
