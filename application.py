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

good_reads = os.getenv('GOOD_READS')

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
    """
    This is the main page
    Initially we check to see if a user id exists. This means that the user clicked the log out button.
    """
    user_exists = session.get('user_id')
    if user_exists:
        del session['user_id']

    return render_template('index.html', user_exists=user_exists)


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register_account', methods=['POST'])
def register_account():
    """
    Register an account for a user based on username and password
    If username and password are not provided, we raise an error and give a link back to the register page
    If the given username already exists, we raise an erro and give a link back to the register page
    Inserts account information into the users table
    """
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
    """
    Validates the given account information
    If the username or password are incorrect, we raise an error and provide a link back to the login page
    """
    username = request.form.get('name')
    password = request.form.get('password')

    if username and password:
        user = db.execute('SELECT * FROM users WHERE username = :username AND password = :password', {'username': username, 'password': password}).fetchone()
        if user:
            session['user_id'] = user[0]
            return render_template('success.html', username=username)
        return render_template('error_login.html', message='username or password is incorrect.')
    else:
        return render_template('error_login.html', message='Enter a username and password.')


@app.route('/books')
def books():
    """
    Lists all books in the database
    """
    books = db.execute('SELECT * FROM books').fetchall()
    return render_template('books.html', books=books)


@app.route('/books/search', methods=['POST'])
def search():
    """
    Returns results based on the given information from the search bar
    """
    book_info = request.form.get('book_info')
    if not book_info:
        return render_template('error_search.html', message='No results matching your search. Try again.')

    books = db.execute(f"SELECT * FROM books WHERE isbn LIKE '%{book_info}%' "
                       f"OR LOWER(title) LIKE '%{book_info.lower()}%' "
                       f"OR LOWER(author) LIKE '%{book_info.lower()}%' "
                       f"OR year::text LIKE '%{book_info}%'").fetchall()

    if not books:
        return render_template('error_search.html', message='No results matching your search. Try again.')
    
    return render_template('results.html', books=books)


@app.route('/books/<string:book_isbn>')
def book(book_isbn):
    """
    List information of the specified book including the number of reviews and the average rating score from goodreads if available
    """
    book_info = db.execute("SELECT books.id, isbn, title, author, year, username, review, rating FROM books "
                           "INNER JOIN reviews ON reviews.book_id = books.id "
                           "INNER JOIN users ON reviews.user_id = users.id WHERE isbn = :isbn", {'isbn': book_isbn}).fetchall()
   
    if len(book_info) == 0:
        book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': book_isbn}).fetchall()

    session['book_id'] = book_info[0][0]

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": good_reads, "isbns": book_isbn})
    if res.status_code != 200:
        return render_template('review.html', book=book_info)

    res = res.json()
    review_count = res['books'][0].get('reviews_count')
    avg_score = res['books'][0].get('average_rating')

    return render_template('review.html', book=book_info, good_reads={'review_count': review_count, 'avg_score': avg_score})


@app.route("/submit_review", methods=['POST'])
def submit_review():
    """
    Validates that a user has not left a review or rating for the same book before
    Inserts the review and rating information into the database
    """
    review = request.form.get('review')
    rating = request.form.get('rating')
    
    book_id = session['book_id']
    user_id = session['user_id']

    user_ids = db.execute("SELECT user_id FROM reviews WHERE book_id = :book_id", {'book_id': book_id}).fetchall()

    for id_ in user_ids:
        if user_id == id_[0]:
            return render_template('error_search.html', message='You have already submitted a review. Return back to book list')

    if not review and not rating:
        return render_template('error_search.html', message='Enter a rating or a text submission. Try again.')

    db.execute("INSERT INTO reviews (book_id, user_id, review, rating) VALUES (:book_id, :user_id, :review, :rating)",
               {'book_id': book_id, 'user_id': user_id, 'review': review, 'rating': rating})

    db.commit()

    return render_template('submit.html')


@app.route('/api/<string:isbn>')
def api(isbn):
    """
    Display a JSON like object of the details for the specified book
    """
    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn}).fetchone()
    if not book_info:
        return render_template('404.html')

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": good_reads, "isbns": isbn})
    if res.status_code != 200:
        return render_template('review.html', book=book_info)

    res = res.json()
    review_count = res['books'][0].get('reviews_count')
    avg_score = res['books'][0].get('average_rating')

    if review_count and avg_score:
        return {'isbn': isbn, 'title': book_info[2], 'author': book_info[3], 'year': book_info[4], 'review_count': review_count, 'average_score': avg_score}

    return {'isbn': isbn, 'title': book_info[2], 'author': book_info[3], 'year': book_info[4]}

