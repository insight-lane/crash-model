import os
import json
from flask import Flask, render_template, send_from_directory


app = Flask(__name__)


DATA_FP = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), 'data')
CURR_FP = os.path.dirname(os.path.abspath(__file__))


def get_default_city():
    with open(os.path.join(CURR_FP, 'static', 'config.json'), 'r') as f:
        config = json.load(f)
    return config[0]['id']


@app.route('/data/<path:path>')
def static_files(path):
    return send_from_directory('data', path)


@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template(
        'index.html',
        mapbox_token=os.environ['MAPBOX_TOKEN']
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')
