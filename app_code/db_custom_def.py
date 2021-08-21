import logging
from app_code import db_data as dbd
from app_code import app_logging as al

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


class DummyDb(DB_BASE):
    __tablename__ = 'dummy_table'
    __table_args__ = {'extend_existing': True}
    __bind_key__ = dbd.APP_DB

    entity_key = DB_COLUMN(DB_INTEGER, primary_key=True, autoincrement=True)
    field_str1 = DB_COLUMN(DB_STRING, nullable=False)
    field_str2 = DB_COLUMN(DB_STRING, nullable=False)
    field_int1 = DB_COLUMN(DB_INTEGER, nullable=False)
    field_int2 = DB_COLUMN(DB_INTEGER, nullable=False)
    UNIQUE_CONSTRAINT(field_str1, field_str2)

    def __repr__(self):
        return f"{self.classname}-{self.entity_key}"

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __init__(self, job_dict):
        for key in job_dict:
            setattr(self, key, job_dict[key])


def create_db():
    dbd.DB_DATA['DB'].create_all()

