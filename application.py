import os
import requests
from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


# @app.route('/success')
# def success():
#     return render_template('success.html')


# @app.route('/error')
# def error():
#     return render_template('error.html')


@app.route('/register_account', methods=['POST'])
def register_account():
    username = request.form.get('name')
    password = request.form.get('password')

    if username and password:
        user = db.execute('SELECT * FROM users WHERE username = :username', {'username': username}).fetchone()
        if user:
            return render_template('error_login.html', message='Username already exists! Try again.')

        db.execute('INSERT INTO users (username, password) VALUES (:username, :password)', {'username': username, 'password': password})
        db.commit()
        return render_template('success.html')

    else:
        return render_template('error_login.html', message='Enter a username and password.')


@app.route('/login_account', methods=['POST'])
def login_account():
    username = request.form.get('name')
    password = request.form.get('password')

    if username and password:
        user = db.execute('SELECT * FROM users WHERE username = :username AND password = :password', {'username': username, 'password': password}).fetchone()
        if user:
            return render_template('success.html', username=username)
        return render_template('error_login.html', message='username or password is incorrect.')
    else:
        return render_template('error_login.html', message='Enter a username and password.')


@app.route('/books')
def books():
    books = db.execute('SELECT * FROM books').fetchall()
    return render_template('books.html', books=books)


@app.route('/books/search', methods=['POST'])
def search():

    book_info = request.form.get('book_info')
    if not book_info:
        return render_template('error_search.html', message='No results matching your search. Try again.')

    if book_info.isnumeric() and len(book_info) < 5:
        books = db.execute(f"SELECT * FROM books WHERE year LIKE '%{int(book_info)}%'").fetchall()
    else:
        books = db.execute(f"SELECT * FROM books WHERE isbn LIKE '%{book_info}%' OR title LIKE '%{book_info}%' OR author LIKE '%{book_info}%'").fetchall()

    if not books:
        return render_template('error_search.html', message='No results matching your search. Try again.')
    
    return render_template('results.html', books=books)


@app.route('/books/<string:book_isbn>')
def book(book_isbn):
    print('made it here')

    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': book_isbn}).fetchone()
    reviews = db.execute("SELECT username, review FROM books "
                           "INNER JOIN reviews ON reviews.book_id = books.id "
                           "INNER JOIN users ON reviews.user_id = users.id WHERE isbn = :isbn", {'isbn': book_isbn}).fetchall()
    
    print(book_info)
    print(reviews)
    return render_template('review.html', book=book_info, reviews=reviews)

