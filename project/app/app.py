from flask import Flask, render_template, url_for

from random import randint


app = Flask(__name__)
application = app


@app.route('/')
def index():
    msg = "Hello"
    return render_template('index.html')


@app.route('/hello')
def hello():
    return render_template("hello.html")

@app.route('/about')
def about():
    title = "Об авторе"
    return render_template('about.html', title=title)
