import flask
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello')
def hello():
    return jsonify(message="Hallo World!")

if __name__ == '__main__':
    app.run()
