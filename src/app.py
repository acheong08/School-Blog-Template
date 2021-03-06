#Flask
from flask import *
#Production
from werkzeug.exceptions import abort #abort processes when rasied exception
from werkzeug.utils import secure_filename #uploading - encoding
#Utilities
from hashlib import pbkdf2_hmac, md5, sha256 #hashing encoding/password/image
from binascii import hexlify #required for hashing
from os import urandom
import sqlite3
from random import randint
#import markdown
import markdown
#JSON
import json

#Configs
app = Flask(__name__)
app.config['SECRET_KEY'] = 'c40a650584b50cb7d928f44d58dcaffc'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = "0de03e1a949f142951868617004aa54b"
ALLOWED_IMG_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

config = str(open('config.json', 'r').read())
available_departments = json.loads(config)['departments']

#Utility functions
def getHash(plaintext, salt):
    m = pbkdf2_hmac('sha256', bytes(plaintext, 'utf-8'), salt, 200000)
    hash = hexlify(m)
    return (salt + hash).decode('utf-8')
def getMD5(plaintext):
    m = md5()
    m.update(plaintext.encode('utf-8'))
    hash = str(m.hexdigest())
    return hash
def saveFile(preview, md):
    if preview.filename != '':
        preview_filename = secure_filename(preview.filename)
        preview_file_ext = preview_filename.rsplit('.', 1)[1].lower()
        if preview_file_ext in ALLOWED_IMG_EXTENSIONS:
            preview_filePath = 'static/img/preview_imgs/' + getMD5(preview_filename) + str(randint(0,999)) + '.' + preview_file_ext
            preview.save(preview_filePath)
        else:
            flash("Not an image...")
            preview_filePath = "static/img/404/404.png"
    else:
        preview_filePath = "static/img/404/404.png"
    #Required
    markdown_filePath = 'uploads/markdown_files/' + getMD5(md) + str(randint(0,9999)) + '.md'
    f = open(markdown_filePath, 'w')
    f.write(md)
    f.close()
    return preview_filePath, markdown_filePath
def authenticate(username, password, type):
    #Connect to sql database and get username and password
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if type == 'admin':
        dbhash = cur.execute('SELECT password_hash FROM admin_accounts WHERE username = ?', (username,)).fetchone()
        admin_department = cur.execute('SELECT department FROM admin_accounts WHERE username = ?', (username,)).fetchone()
        conn.close()
        if dbhash != None:
            dbhash_components = dbhash[0].split('endofsalt')
            salt = str(dbhash_components[0] + 'endofsalt').encode('utf-8')
            dbhash = dbhash_components[1]
            hashpass = getHash(password, salt).split('endofsalt')[1]
            if hashpass == dbhash:
                return True, admin_department[0]
            else:
                return False, None
        else:
            return False, None
    elif type == 'client':
        dbhash = cur.execute('SELECT password_hash FROM client_accounts WHERE username = ?', (username,)).fetchone()
        conn.close()
        if dbhash != None:
            dbhash_components = dbhash[0].split('endofsalt')
            salt = str(dbhash_components[0] + 'endofsalt').encode('utf-8')
            dbhash = dbhash_components[1]
            hashpass = getHash(password, salt).split('endofsalt')[1]
            if hashpass == dbhash:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
def post_to_db(post_title, post_description, post_preview, post_content, department):
    try:
        preview_filePath, markdown_filePath = saveFile(post_preview, post_content)
    except Exception as e:
        preview_filePath = None
        markdown_filePath = None
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('INSERT INTO posts (title, description, preview, content, department) VALUES (?,?,?,?,?)',
     (post_title, post_description, preview_filePath, markdown_filePath, department))
    conn.commit()
    conn.close()
def update_post_db(id, post_title, post_description, post_content, department):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    markdown_filePath = cur.execute('SELECT content FROM posts WHERE id = ?', (id,)).fetchone()
    cur.execute('UPDATE posts SET title = ?, description = ?, department = ? WHERE id = ?', (post_title, post_description, department, id))
    conn.commit()
    conn.close()
    if markdown_filePath != None:
        f = open(markdown_filePath[0], 'w')
        f.write(post_content)
        f.close()
    else:
        flash('Hey hacker. GO AWAY')
def delete_post(id):
    conn, cur = dbConnCur()
    cur.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
def dbConnect():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
def dbConnCur():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    return conn, cur
def userExists(email, username):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    existingEmail = cur.execute('SELECT * FROM client_accounts WHERE email = ?', (email,)).fetchone()
    existingUsername = cur.execute('SELECT * FROM client_accounts WHERE username = ?', (username,)).fetchone()
    conn.close()
    if existingEmail == None and existingUsername == None:
        return False
    else:
        return True
def addAccount(email, username, password):
    conn, cur = dbConnCur()
    salt = str(sha256(urandom(60)).hexdigest() + "endofsalt").encode('utf-8')
    hashedPassword = getHash(password, salt)
    cur.execute('INSERT INTO client_accounts (email, username, password_hash) VALUES (?, ?, ?)', (email, username, hashedPassword))
    conn.commit()
    conn.close()


#App routes
@app.route('/logout')
def logout():
    try:
        if 'admin_id' in session:
            session.pop('admin_id')
            session.pop('admin_department')
        if 'client_id' in session:
            session.pop('client_id')
        flash("Logged out")
    except Exception as e:
        flash("Not signed in")
    return redirect(url_for('index'))

#Client
@app.route('/')
def index():
    markdown_content = markdown.markdown(open('templates/markdown_files/index.md', 'r').read())
    return render_template('defaults/index.html', markdown_content = markdown_content)

@app.route('/about')
def about():
    markdown_content = markdown.markdown(open('templates/markdown_files/about.md', 'r').read())
    return render_template('defaults/about.html', markdown_content = markdown_content)

@app.route('/signup', methods=('GET','POST'))
def signup():
    if 'client_id' not in session:
        if request.method == 'GET':
            return render_template('defaults/signup.html')
        elif request.method == 'POST':
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']
            verify = request.form['verify']
            if password != verify:
                flash('Passwords do not match')
                return redirect(url_for('signup'))
            else:
                if userExists(email, username) == True:
                    flash('User already exists')
                    return redirect(url_for('signup'))
                else:
                    addAccount(email, username, password)
                    session['client_id'] = username
                    flash(str('Successfully signed up as ' + username))
                    return redirect(url_for('index'))
        else:
            return render_template('defaults/404.html')
    else:
        flash('Already logged in')
        return redirect(url_for('index'))

@app.route('/login', methods=('GET','POST'))
def login():
    if 'client_id' not in session:
        if request.method == 'GET':
            return render_template('defaults/login.html')
        elif request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            type = 'client'
            correct = authenticate(username, password, type)
            if correct == True:
                session['client_id'] = username
                flash(str('Logged in as ' + username ))
                return redirect(url_for('index'))
            elif correct == False:
                flash('Incorrect username or password')
                return redirect(url_for('login'))
            else:
                flash('Error')
                return redirect(url_for('login'))
    else:
        flash("Already logged in")
        return redirect(url_for('index'))

#Posts
@app.route('/posts')
def post_index():
    conn = dbConnect()
    posts_data = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
    conn.close()
    return render_template('posts/index.html', posts_data = posts_data)
@app.route('/posts/<int:post_id>')
def post_page(post_id):
    conn = dbConnect()
    post_data = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    if post_data == None:
        return render_template('defaults/404.html')
    else:
        filePath = post_data['content']
        if filePath != None:
            try:
                f = open(filePath, 'r')
                content = f.read()
                markdown_content = markdown.markdown(content)
            except Exception as e:
                markdown_content = 'Error'
        else:
            markdown_content = 'Error'
        return render_template('posts/post_page.html', post_data = post_data , markdown_content = markdown_content)

#Admin
@app.route('/admin/login', methods=('GET','POST'))
def admin_login():
    if 'admin_id' not in session:
        if request.method == 'GET':
            return render_template('admin/login.html')
        elif request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            type = 'admin'
            correct, department = authenticate(username, password, type)
            if correct == True:
                session['admin_id'] = username
                session['admin_department'] = department
                flash(str('Logged in as ' + username + ' in the ' + department + ' department'))
                return redirect(url_for('admin_index'))
            elif correct == False:
                flash('Incorrect username or password')
                return redirect(url_for('admin_login'))
            else:
                flash('Error')
                return redirect(url_for('admin_login'))
    else:
        flash("Already logged in")
        return redirect(url_for('admin_index'))

    #Admin index
@app.route('/admin', methods=('GET', 'POST'))
def admin_index():
    if 'admin_id' not in session:
        flash('Access Denied')
        return redirect(url_for('admin_login'))
    elif 'admin_id' in session:
        if request.method == 'GET':
            markdown_content = markdown.markdown(open('templates/markdown_files/admin_index.md', 'r').read())
            return render_template('admin/index.html', markdown_content = markdown_content)
        #Administrative actions
        elif request.method == 'POST':
            action = request.form['action']
            #Deleting comments, banning users from commenting, etc
        return redirect(url_for('admin_index'))
    else:
        flash('Error')
        redirect(url_for('admin_index'))

@app.route('/admin/new_post', methods=('GET', 'POST'))
def new_post():
    if 'admin_id' in session:
        if request.method == 'GET':
            return render_template('admin/new_post.html', department = session['admin_department'], available_departments = available_departments)
        elif request.method == 'POST':
            post_title = request.form['post_title']
            post_description = request.form['post_description']
            post_preview = request.files['post_preview']
            post_content = request.form['post_content']
            department = request.form['post_department']
            post_to_db(post_title, post_description, post_preview, post_content, department)
            flash("Success")
            return redirect(url_for('new_post'))
    else:
        return redirect(url_for('admin_login'))

@app.route('/admin/posts/edit/<int:post_id>', methods=('GET', 'POST'))
def edit_post(post_id):
    if session['admin_id'] == 'root':
        if request.method == 'GET':
            conn = dbConnect()
            post_data = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
            conn.close()
            content = open(str(post_data['content']), 'r').read()
            return render_template('admin/edit.html', post_data = post_data, markdown_content = content, available_departments = available_departments)
        elif request.method == 'POST':
            if request.form['action'] == 'edit':
                post_title = request.form['post_title']
                post_description = request.form['post_description']
                post_content = request.form['post_content']
                department = request.form['post_department']
                update_post_db(post_id, post_title, post_description, post_content, department)
            elif request.form['action'] == 'delete':
                delete_post(post_id)
            else:
                flash("GO AWAY HACKER")
            flash('Done')
            return redirect(url_for('post_index'))
    else:
        flash('Permission Denied')
        return redirect(url_for('index'))

@app.route('/admin/webpage_edit/<string:page>', methods=('GET', 'POST'))
def webpage_edit(page):
    if session['admin_department'] == 'root':
        if request.method == 'GET':
            markdown_content = open(str('templates/markdown_files/' + page + '.md'), 'r').read()
            return render_template('admin/webpage_edit.html', markdown_content = markdown_content, page = page)
        elif request.method == 'POST':
            markdown_content = request.form['markdown_content']
            markdown_file = open(str('templates/markdown_files/' + page + '.md'), 'w').write(markdown_content)
            flash('Success')
            return redirect(url_for(str(page)))
    else:
        flash('Permission Denied')
        return redirect(url_for('index'))
#Run app
if __name__=="__main__":
    app.run(debug=True, port=8000, host="127.0.0.1")
