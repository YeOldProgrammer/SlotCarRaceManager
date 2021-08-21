import logging
from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher
from app_code import app_logging as al

WEB_DATA = {'wsgi_server': None}
LOGGER = logging.getLogger(al.LOGGER_NAME)


def run_web_server(server, default_host='0.0.0.0', default_port='8080'):
    web_server_port = int(default_port)
    dispatcher = PathInfoDispatcher({'/': server})
    WEB_DATA['wsgi_server'] = WSGIServer((default_host, web_server_port), dispatcher)

    display_host = default_host
    if display_host == '0.0.0.0':
        display_host = '127.0.0.1'

    LOGGER.info("Starting web server on port http://%s:%d", display_host, web_server_port)

    try:
        WEB_DATA['wsgi_server'].start()
    except KeyboardInterrupt:
        LOGGER.info("Keyboard Interrupt")
    except OSError as error_text:
        if 'Address already in use' in str(error_text):
            LOGGER.warning("Unable to start webserver - port %d already in use", web_server_port)
        else:
            LOGGER.warning("OS Error other than port in use")
            raise OSError(error_text) from error_text

    if WEB_DATA['wsgi_server'] is not None:
        LOGGER.info("Ending web server")
