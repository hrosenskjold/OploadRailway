from flask import Flask
from flask_cors import CORS

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

@app.route('/hello', methods=['GET'])
def hello_world():
    return 'Hello world', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
