from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_session import Session
from db_config import init_mysql
from decorators import login_required  # Import the login_required decorator

app = Flask(__name__)
app.secret_key = "rahasia_super_secret"
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

mysql = init_mysql(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM user WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and user[1] == password:
            session['user_id'] = user[0]
            return redirect(url_for('main'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cur.close()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def main():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, author, isbn, genre, language, total_copies, available_copies, shelf, status FROM books")
    books = cur.fetchall()

    # Menghitung total buku
    cur.execute("SELECT SUM(total_copies) FROM books")
    total_books = cur.fetchone()[0]

    # Menghitung buku yang tersedia
    cur.execute("SELECT SUM(available_copies) FROM books WHERE status = 'available'")
    available_books = cur.fetchone()[0]

    # Menghitung buku yang dipinjam
    cur.execute("SELECT COUNT(*) FROM lend")
    lended_books = cur.fetchone()[0]

    # Menghitung total membership
    cur.execute("SELECT COUNT(*) FROM member")
    total_members = cur.fetchone()[0]

    cur.close()
    return render_template('dashboard.html', books=books, total_books=total_books, available_books=available_books, lended_books=lended_books, total_members=total_members)

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        genre = request.form['genre']
        language = request.form['language']
        total_copies = request.form['total_copies']
        available_copies = request.form['available_copies']
        shelf = request.form['shelf']
        status = request.form['status']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO books (title, author, isbn, genre, language, total_copies, available_copies, shelf, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (title, author, isbn, genre, language, total_copies, available_copies, shelf, status))
        mysql.connection.commit()
        cur.close()

        flash('Buku berhasil ditambahkan!', 'success')
        return redirect('/')

    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (book_id,))
    book = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        genre = request.form['genre']
        language = request.form['language']
        total_copies = request.form['total_copies']
        available_copies = request.form['available_copies']
        shelf = request.form['shelf']
        status = request.form['status']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE books
            SET title = %s, author = %s, isbn = %s, genre = %s, language = %s, total_copies = %s, available_copies = %s, shelf = %s, status = %s
            WHERE id = %s
        """, (title, author, isbn, genre, language, total_copies, available_copies, shelf, status, book_id))
        mysql.connection.commit()
        cur.close()

        flash('Buku berhasil diperbarui!', 'success')
        return redirect('/')

    return render_template('edit_book.html', book=book, book_id=book_id)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
    mysql.connection.commit()
    cur.close()

    flash('Buku berhasil dihapus!', 'success')
    return redirect('/')

@app.route('/membership')
@login_required
def membership():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, joined_date, email FROM member")  
    members = cur.fetchall()
    cur.close()
    return render_template('membership.html', members=members)

@app.route('/add_member', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        id = request.form['Id']
        name = request.form['Name']
        join_date = request.form['join_date']
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO member (id, name, joined_date, email) VALUES (%s, %s, %s, %s)",
                    (id, name, join_date, email))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('membership'))  # Redirect to membership page after adding

    return render_template('add_member.html')

@app.route('/lend_book', methods=['GET', 'POST'])
@login_required
def lend_book():
    if request.method == 'POST':
        title = request.form['title']
        member_name = request.form['member_name']
        date = request.form['date']

        cur = mysql.connection.cursor()
        cur.execute("SELECT available_copies FROM books WHERE title = %s", (title,))
        available_copies = cur.fetchone()[0]

        if available_copies > 0:
            cur.execute("INSERT INTO lend (title, mem_name, date) VALUES (%s, %s, %s)", 
                        (title, member_name, date))
            cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE title = %s", (title,))
            
            # Memeriksa apakah available_copies menyentuh angka 0
            cur.execute("SELECT available_copies FROM books WHERE title = %s", (title,))
            updated_available_copies = cur.fetchone()[0]
            if updated_available_copies == 0:
                cur.execute("UPDATE books SET status = 'out of stock' WHERE title = %s", (title,))
            
            mysql.connection.commit()
            flash('Buku berhasil dipinjam!', 'success')
        else:
            flash('Buku tidak tersedia untuk dipinjam.', 'danger')
        
        cur.close()
        return redirect(url_for('lend_book'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT title, available_copies FROM books")
    books = cur.fetchall()
    cur.execute("SELECT name FROM member")
    members = cur.fetchall()
    cur.execute("SELECT id, title, mem_name, date FROM lend")
    lendings = cur.fetchall()
    cur.close()

    return render_template('lending.html', books=books, members=members, lendings=lendings)

    cur = mysql.connection.cursor()
    cur.execute("SELECT title FROM books")
    books = cur.fetchall()
    cur.execute("SELECT name FROM member")
    members = cur.fetchall()
    cur.execute("SELECT id, title, mem_name, date FROM lend")
    lendings = cur.fetchall()
    cur.close()

    return render_template('lending.html', books=books, members=members, lendings=lendings)

@app.route('/help')
@login_required
def help():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)