import flask
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


# EXTERNAL_STYLE_SHEETS = [dbc.themes.BOOTSTRAP]
EXTERNAL_STYLE_SHEETS = [
    dbc.themes.SLATE,
    # 'https://codepen.io/chriddyp/pen/bWLwgP.css'
]


def init_flask():
    flask_app = flask.Flask(__name__)
    # flask_app.secret_key =
    return flask_app


def init_dash(flask_app):
    dash_app = dash.Dash('dash_app', server=flask_app, suppress_callback_exceptions=False,
                         external_stylesheets=EXTERNAL_STYLE_SHEETS)
    dash_app.title = 'Race Entry'
    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])

    return dash_app


FLASK_APP = init_flask()
DASH_APP = init_dash(FLASK_APP)


@FLASK_APP.route('/heartbeat', methods=['GET'])
def heartbeat():
    response_data = {'success': True
                     }
    return flask.jsonify(response_data)
