import flask
from sqlitis.convert import to_sqla

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('index.html')


@app.route('/to-sqla', methods=['POST'])
def to_sqlalchemy():
    data = flask.request.get_json(force=True)
    try:
        sql = data.get('sql')
    except Exception as e:
        response = {
            'error': str(e),
        }
        return flask.jsonify(response), 400

    try:
        response = {
            'sql': sql,
            'sqla': to_sqla(sql),
        }
        return flask.jsonify(response), 200
    except Exception as e:
        response = {
            'sql': sql,
            'error': str(e),
        }
        return flask.jsonify(response), 400


if __name__ == '__main__':
    app.run(debug=True, port=7070)
