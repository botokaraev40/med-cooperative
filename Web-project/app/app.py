from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import login_required, current_user
from mysql_db import MySQL
import mysql.connector as connector

# login_manager = LoginManager()

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

mysql = MySQL(app)

from auth import bp as auth_bp, init_login_manager, check_rights


init_login_manager(app)
app.register_blueprint(auth_bp)











def load_roles():
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT id, name FROM roles;')
    roles = cursor.fetchall()
    cursor.close()

    return roles


@app.route('/', methods=['GET'])
def index():

    name = request.args.get('find_name') or ''
    year = request.args.get('find_year') or ''
    author = request.args.get('find_author') or ''
    volume = request.args.get('find_volume') or ''
    genre = request.args.get('find_genre') or ''

    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT id, name, year_of_release, genre_name, AVG(estimation) AS estimation, COUNT(id) AS counters FROM list_of_books GROUP BY id, name, genre_name, year_of_release UNION SELECT id, name, year_of_release, genres_name, AVG(estimation) AS estimation, 0 FROM without_review GROUP BY id, name, genres_name, year_of_release ORDER BY year_of_release DESC;')
    books = cursor.fetchall()



    cursor.execute(('SELECT books.name AS name, genres.name AS genre, books.year_of_release AS year, books.volume AS volume, books.author AS author '
                   'FROM books, books_and_genres, genres '
                   'WHERE books.id=books_and_genres.id_books and books_and_genres.id_genres = genres.id AND '
                   'books.name=%s AND books.year_of_release=%s AND books.volume=%s AND books.author=%s;'),(name, year, volume, author))
    finds = cursor.fetchall()

    cursor.close()




    return render_template('index.html', books=books, finds=finds, author=author, year=year, name=name, volume=volume, genre=genre)


@app.route('/users')
def users():
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT users.*, roles.name AS role_name FROM users LEFT OUTER JOIN roles ON users.role_id = roles.id;')
    users = cursor.fetchall()
    cursor.close()
    return render_template('users/index.html', users=users)



@app.route('/<int:book_id>/show')

@login_required
def show(book_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT users.last_name, users.first_name, users.middle_name, reviews.estimation, reviews.letter FROM users, reviews WHERE reviews.books_id = %s AND users.id=reviews.users_id;', (book_id,))
    reviews = cursor.fetchall()

    cursor.execute('SELECT books.name, books.description, books.year_of_release, books.publishing, books.author, books.volume  FROM books, books_and_genres WHERE books.id=%s GROUP BY books.id;', (book_id,))
    book = cursor.fetchone()

    cursor.execute('SELECT genres.name FROM books, books_and_genres, genres WHERE books.id=%s AND books_and_genres.id_genres=genres.id GROUP BY genres.id;', (book_id,))
    genre = cursor.fetchall()
    cursor.close()
    return render_template('show.html', genre=genre, book=book, reviews=reviews)





@app.route('/new')
@check_rights('new')
@login_required
def new():
    return render_template('new.html', user={}, roles=load_roles())


@app.route('/<int:book_id>/edit')
# @check_rights('edit')
@login_required
def edit(book_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT * FROM books WHERE id = %s;', (book_id,))
    book = cursor.fetchone()
    cursor.close()
    return render_template('edit.html', book=book)


@app.route('/create', methods=['GET', 'POST'])
@check_rights('new')
@login_required
def create():
    name = request.form.get('name') or None
    description = request.form.get('description') or None
    year = request.form.get('year') or None
    publishing = request.form.get('publishing') or None
    author = request.form.get('author') or None
    volume = request.form.get('volume') or None
    genre = request.form.getlist('genre') or []

    query1 = '''SET @enddate = (SELECT MAX(id) FROM books); INSERT INTO books_and_genres (id_books, id_genres) VALUES (@enddate, %s);'''
    query = '''
        INSERT INTO books (name, description, year_of_release, publishing, author, volume)
        VALUES (%s, %s, %s, %s, %s, %s);
    '''



    cursor = mysql.connection.cursor(named_tuple=True)
    a = cursor.execute('SET @enddate = (SELECT MAX(id) FROM books);')

    try:
        cursor.execute(query, (name, description, year, publishing, author, volume))
        mysql.connection.commit()
        book_id = cursor.lastrowid
        for g in genre:
            cursor.execute('INSERT INTO books_and_genres (id_books, id_genres) VALUES (%s, %s);', (book_id, g))
        mysql.connection.commit()




    except connector.errors.DatabaseError as err:
        flash('Введены некорректные данные. Ошибка сохранения', 'danger')
        book = {
        'name': name or None,
        'description': description or None,
        'year': year,
        'publishing': publishing,
        'author': author,
        'volume': volume

        }
        return render_template('new.html', book=book)


    cursor.close()






    flash(f'Пользователь {name} был успешно создан', 'success')
    return redirect(url_for('index'))


# ЗАКОНЧИТЬ ФУНКЦИЮ РЕДАКТИРОВАНИЯ
@app.route('/<int:book_id>/update', methods=['POST'])
@check_rights('edit')
@login_required
def update(book_id):
    name = request.form.get('name') or None
    description = request.form.get('description') or None
    year = request.form.get('year') or None
    publishing = request.form.get('publishing') or None
    author = request.form.get('author') or None
    volume = request.form.get('volume') or None
    genre = request.form.getlist('genre') or []
    query = '''
            UPDATE books SET name=%s, description=%s, year_of_release=%s, publishing=%s, author=%s, volume=%s
            WHERE id=%s;
        '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (name, description, year, publishing, author, volume, book_id))

    except connector.errors.DatabaseError as err:
        flash('Введены некорректные данные. Ошибка сохранения', 'danger')
        book = {
            'name': name or None,
            'description': description,
            'year_of_release': year,
            'publishing': publishing,
            'author': author,
            'volume': volume


        }
        return render_template('edit.html', book=book)
    mysql.connection.commit()  # Завершение транзакции.
    cursor.close()
    flash(f'Книга {name} была успешно создана', 'success')
    return redirect(url_for('index'))


# ЗАКОНЧИТЬ ФУНКЦИЮ УДАЛЕНИЯ
@app.route('/<int:book_id>/delete', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete(book_id):
    with mysql.connection.cursor(named_tuple=True) as cursor:
        try:
            cursor.execute('DELETE FROM books WHERE id = %s;', (book_id,))
        except connector.errors.DatabaseError as err:
            flash('Не удалось удалить запись.', 'danger')
            return redirect(url_for('index'))
        mysql.connection.commit()

        flash('Запись была успешно удалена', 'success')

    return redirect(url_for('index'))