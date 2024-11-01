from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random  # Import random module

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('freedom_wall.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

@app.route('/')
def public():
    conn = sqlite3.connect('freedom_wall.db')
    cur = conn.cursor()
    cur.execute('SELECT posts.id, users.username, posts.content FROM posts JOIN users ON posts.user_id = users.id')
    posts = cur.fetchall()
    conn.close()
    
    # Shuffle the posts to randomize their order
    random.shuffle(posts)
    
    return render_template('public.html', posts=posts)


@app.route('/home')
@login_required
def home():
    conn = sqlite3.connect('freedom_wall.db')
    cur = conn.cursor()
    cur.execute('SELECT posts.id, users.username, posts.content FROM posts JOIN users ON posts.user_id = users.id')
    posts = cur.fetchall()
    conn.close()
    
    # Shuffle the posts to randomize their order
    random.shuffle(posts)
    
    return render_template('home.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('freedom_wall.db')
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose a different one.', 'error')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('freedom_wall.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1])
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and/or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public'))

@app.route('/post', methods=['POST'])
@login_required
def post():
    content = request.form['content']
    conn = sqlite3.connect('freedom_wall.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (user_id, content) VALUES (?, ?)', (current_user.id, content))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    conn = sqlite3.connect('freedom_wall.db')
    cur = conn.cursor()
    # Fetch the post to check ownership
    cur.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
    post = cur.fetchone()

    if post and post[0] == current_user.id:
        # Delete the post if the current user is the owner
        cur.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        flash('Post deleted successfully.', 'success')
    else:
        flash('You do not have permission to delete this post.', 'error')

    conn.close()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
