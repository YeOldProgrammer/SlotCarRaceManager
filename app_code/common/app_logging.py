import os
import logging
from logging import config
import time
from app_code.common import config_data as cd

LOG_FORMAT = '%(asctime)s %(levelname)-7s [%(filename)-28s:%(lineno)4d] %(message)s'
LOGGER_NAME = 'default'
LOGGER = logging.getLogger(LOGGER_NAME)


def init_logging():
    if os.path.isdir(cd.ENV_VARS['LOG_DIR']) is False:
        os.makedirs(cd.ENV_VARS['LOG_DIR'])

    logging_conf_dict = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default_formatter': {
                'format': LOG_FORMAT
            }
        },
        'handlers': {
            'consoleHandler': {
                'class': 'logging.StreamHandler',
                'formatter': 'default_formatter',
                'stream': 'ext://sys.stdout',
            },
            'logFileHandler': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'default_formatter',
                'filename': cd.ENV_VARS['LOG_FILE'],
                'when': 'W5',
                'interval': 1,
                'backupCount': 5,
            }
        },
        'loggers': {
            LOGGER_NAME: {
                'handlers': ['consoleHandler', 'logFileHandler'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(logging_conf_dict)
    logging.Formatter.converter = time.localtime
