# Description: This file contains the main code for the web application
############################################################
from flask import (
    Flask,
    send_from_directory,
    redirect,
    request,
    url_for,
    render_template,
    session,
)
from flask_sqlalchemy import SQLAlchemy
import re
from flask_bcrypt import Bcrypt
from identity.flask import Auth
from msal import PublicClientApplication

# Objects & Variables
############################################################
app = Flask(__name__)
app.config.from_object("config.Config")
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
restricted_emails = {
    "administrator",
    "admin",
    "user",
    "user1",
    "test",
    "user2",
    "test1",
    "user3",
    "admin1",
    "1",
    "123",
    "a",
    "actuser",
    "adm",
    "admin2",
    "aspnet",
    "backup",
    "console",
    "david",
    "guest",
    "john",
    "owner",
    "root",
    "server",
    "sql",
    "support",
    "support_388945a0",
    "sys",
    "test2",
    "test3",
    "user4",
    "user5",
}
auth = Auth(
    app,
    authority=("AUTHORITY"),
    client_id=("CLIENT_ID"),
    client_credential=("CLIENT_SECRET"),
    redirect_uri=("REDIRECT_URI"),
    oidc_authority=("OIDC_AUTHORITY"),
)


# Class & Functions
############################################################
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer, db.Sequence("user_id_seq", increment=1), primary_key=True
    )
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    def __init__(self, email):
        self.email = email
        self.password = bcrypt.generate_password_hash("password").decode("utf-8")


def valid_email(email):
    windows_invalid = re.compile(r'[/"\[\]:|<>+=;,?*&]')
    linux_invalid = re.compile(r"^[a-zA-Z0-9_]+$")
    if email.lower() in restricted_emails:
        return False, "That email is too generic and is not allowed"
    if windows_invalid.search(email) or email.endswith("."):
        return False, "email cannot contain special characters /" "[]:|<>+=;,?*@&"
    if not linux_invalid.match(email):
        return (
            False,
            "email must only contain letters, numbers, hyphens, and underscores",
        )
    if len(email) > 20:
        return False, "email exceeds maximum length"
    return True, ""


def valid_password(password):
    password_contains = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{12,123}$"
    )
    return password_contains.match(password)


# Routing
############################################################
@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""
    if (
        request.method == "POST"
        and "email" in request.form
        and "password" in request.form
    ):
        email = request.form["email"]
        password = request.form["password"]
        db.session.execute("SELECT * FROM users WHERE email = %s", (email,))
        account = User.email
        if account and bcrypt.check_password_hash(account["password"], password):
            session["loggedin"] = True
            session["id"] = account["id"]
            session["email"] = account["email"]
            return redirect(url_for("home"))
        else:
            msg = "Incorrect email or Password"
    return render_template("index.html", msg=msg)


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if (
        request.method == "POST"
        and "email" in request.form
        and "password" in request.form
    ):
        email = request.form["email"]
        password = request.form["password"]

        db.session.execute("SELECT * FROM users WHERE email = %s", (email,))
        account = db.session.get_one()

        if account:
            msg = "Account already exists"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email"
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$+", email):
            msg = "email must contain only characters and numbers"
        elif not email or not password:
            msg = "Please fill out all the fields"
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.execute(
                "INSERT INTO users VALUES (NULL, %s, %s, %s)",
                (
                    email,
                    hashed_password,
                ),
            )
            db.session.commit()
            msg = "Successfully registered"
    elif request.method == "POST":
        msg = "Please fill out all the fields "
    return render_template("register.html", msg=msg)


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)
