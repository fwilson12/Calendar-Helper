from flask import Flask, url_for, request
from markupsafe import escape

app = Flask(__name__)

@app.route("/")
def index():
    return 'home page'

@app.route("/greeting/<name>")
def greeting(name):
    return f'Hello, {escape(name)}!'

if __name__ == "__main__":
    app.run(debug=True)

