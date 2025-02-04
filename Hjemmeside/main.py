from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from flask_bcrypt import Bcrypt
import dotenv

#   Objects
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
dotenv.load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('FLASK_APP_KEY')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
mysql = MySQL(app)

# SSL - Pathing
cert_file = os.path.abspath('cert.pem')
pkey_file = os.path.abspath('key.pem')

#  Functions
def valid_username(username):
    windows_invalid = re.compile(r'[/"\[\]:|<>+=;,?*@&]')
    linux_invalid = re.compile(r'^[a-zA-Z0-9]+$')
    if username.lower() in os.getenv('restricted_usernames'):
        return False, "That username is too generic and is not allowed"
    if windows_invalid.search(username) or username.endswith('.'):
        return False, "Username cannot contain special characters /""[]:|<>+=;,?*@&"
    if not linux_invalid.match(username):
        return False, "Username must only contain letters, numbers, hyphens, and underscores"
    if len(username) > 20:
        return False, "Username exceeds maximum length"
    return True, ""


def valid_password(password):
    password_contains = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{12,123}$')
    return password_contains.match(password)

def gen_shell_script(template_path, **kwargs):
    with open(template_path, 'r') as template_file:
        template = template_file.read()
    return template.format(**kwargs)

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM pythonlogin.accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account and bcrypt.check_password_hash(account['password'], password):
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect Username or Password'
    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT * FROM pythonlogin.accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = 'Account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = "Invalid email"
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers'
        elif not username or not password or not email:
            msg = 'Please fill out all the fields'
        else:
            hashed_password = bcrypt.generate_password_hash(
                password).decode('utf-8')
            cursor.execute('INSERT INTO pythonlogin.accounts VALUES (NULL, %s, %s, %s)',
                           (username, hashed_password, email,))
            mysql.connection.commit()
            msg = 'Successfully registered'
    elif request.method == 'POST':
        msg = 'Please fill out all the fields '
    return render_template('register.html', msg=msg)


@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/form', methods=['POST', 'GET'])
def form():
    if 'loggedin' in session:
        msg = ''
        if request.method == 'POST':
            resource_group = request.form.get("resource_group")
            vm_name = request.form.get("vm_name")
            os_image = request.form.get("OSImage")
            admin_username = request.form.get("admin_username")
            admin_password = request.form.get("admin_password")
            confirm_password = request.form.get("confirm_password")
            disk_size = request.form.get("disk_size")
            virtual_network = request.form.get("virtual_network")
            subnet = request.form.get("subnet")

            is_valid, error_msg = valid_username(admin_username)
            if not is_valid:
                msg = error_msg

            elif not valid_password(admin_password):
                msg = "Password is not complex enough"

            elif admin_password != confirm_password:
                msg = "Passwords do not match"
            else:
                image_offer, image_publisher, image_sku = os_image.split(';')
                linux = "-Linux" if image_offer in ["Debian-11", "0001-com-ubuntu-server-jammy"] else ""

                shell_script = gen_shell_script(
                    'vm_template.ps1',
                    resource_group=resource_group,
                    vm_name=vm_name,
                    admin_username=admin_username,
                    admin_password=admin_password,
                    image_publisher=image_publisher,
                    image_offer=image_offer,
                    image_sku=image_sku,
                    virtual_network=virtual_network,
                    subnet=subnet,
                    disk_size=disk_size,
                    linux=linux
                )
                powershell_path = os.path.abspath('vm_create.ps1')
                with open(powershell_path, 'w') as ps_file:
                    ps_file.write(shell_script)
                msg = "Form submitted successfully"
                return send_file(powershell_path, as_attachment=True, download_name='vm_create.ps1')
        return render_template('form.html', username=session['username'], msg=msg)
    return redirect(url_for('login'))


app.run(host=('0.0.0.0'), ssl_context=(cert_file, pkey_file))
