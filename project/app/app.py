from flask import Flask, render_template, url_for
from faker import Faker
from random import randint

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['img-1', 'img-2', 'img-3', 'img-4', 'img-5']
url_ids = ['0', '1', '2', '3', '4']

def generate_comments(replies=True):
    comments = {}

    comments = {f'comment{1}': {'auth': fake.name(), 'text': fake.text()},
                f'comment{2}': {'auth': fake.name(), 'text': fake.text()},
                f'comment{3}': {'auth': fake.name(), 'text': fake.text()}}


    return comments



def generate_post(i):
    return {
        'title': 'Заголовок поста',
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_filename': f'{images_ids[i]}.jpg',
        'comments': generate_comments(),
        'url': url_ids[i]
    }

posts_list = [generate_post(i) for i in range(5)]

@app.route('/')
def index():
    msg = "Hello"
    return render_template('index.html')


@app.route('/posts')
def posts():
    title = "Посты"
    return render_template('posts.html', title=title, posts=posts_list)


@app.route('/post/<int:index>')
def post(index):
    p = posts_list[index]
    return render_template('post.html', title=p['title'], post=p)


@app.route('/about')
def about():
    title = "Об авторе"
    return render_template('about.html', title=title)