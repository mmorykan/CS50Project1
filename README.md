# Project 1

Web Programming with Python and JavaScript

For this project, all python and flask functions are inside application.py.
Also, import.py creates the books table in my database and adds all books contained in books.csv to the table accordingly

All html files extend layout.html.
A user can login or register and will be taken to a page that lists all the books as well as a text bar where they can input for results.
Once they choose the book they want, they can leave a review and/or a rating but they can't do this more than once per book.
After submitting their review, they will see a success page and then a button taking them back to the books page.
lastly, they can choose to logout on the books page, the review page, and the review success page via the log out button.

The main pages are the index.html, login.html, books.html, and review.html.
The pages 404.html, error_login.html, and error_search.html are all error pages for invalid login information, search information, or review information.

The get_access.html page is the parent html file for login.html and register.html since these two files contain very similar information.

The results.html page lists links to the books that were related to the search information provided by the user and the submit.html page is the success page for successfully posting a review and/or rating with a button taking the user back to the books page.

I have 4 jpg files in the static folder along with my scss and css file.

I used 4 tables for this project, 1 for users, 1 for books and book information, 1 for book reviews, and 1 for the 


One thing to note is that in order for the existing code that I downloaded to work, I had to install werkzeug 0.16.0.
