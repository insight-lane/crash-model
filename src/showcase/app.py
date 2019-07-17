import os
from flask import Flask, render_template, send_from_directory


app = Flask(__name__)


CONFIG_FILE = os.path.join('static', 'config.js')


@app.route('/data/<path:path>')
def static_files(path):
    return send_from_directory('data', path)


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'CONFIG_FILE' in os.environ:
        global CONFIG_FILE
        CONFIG_FILE = os.environ['CONFIG_FILE']
    return render_template(
        'index.html',
        mapbox_token=os.environ['MAPBOX_TOKEN'],
        config_file=CONFIG_FILE
    )


if __name__ == '__main__':

    app.run(host='0.0.0.0')
