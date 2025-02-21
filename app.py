from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from db_config import init_mysql

app = Flask(__name__)
app.secret_key = "rahasia_super_secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

mysql = init_mysql(app)
bcrypt = Bcrypt(app)

@app.route('/')
def main():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, author, isbn, genre, language, total_copies, available_copies, shelf, status FROM books")
    books = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', books=books)

if __name__ == '__main__':
    app.run(debug=True)
