import identity
import identity.web
import requests
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
import app_config
import re
import os
__version__ = "0.9.0"  # The version of this sample, for troubleshooting purpose

app = Flask(__name__)
app.config.from_object(app_config.Config)

Session(app)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],

)
print("CLIENT_ID:", app.config["CLIENT_ID"])


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

@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app.config["SCOPE"],
        redirect_uri=url_for("auth_response", _external=True),
    ))


@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))


@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index.html', user=auth.get_user(), version=identity.__version__)

@app.route(app.config["REDIRECT_PATH"])
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))

@app.route("/call_downstream_api")
def call_downstream_api():
    token = auth.get_token_for_user(app.config["SCOPE"])
    if "error" in token:
        return redirect(url_for("login"))
    # Use access token to call downstream api
    api_result = requests.get(
        app.config["ENDPOINT"],
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    ).json()
    return render_template('display.html', result=api_result)

@app.route('/form', methods=['POST', 'GET'])
def form():
    if auth.get_user():
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
        return render_template('form.html')
    return redirect(url_for('login'))

@app.route("/mass_vm")
def mass_vm():
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('mass_vm.html', user=auth.get_user(), version=identity.__version__)

if __name__ == "__main__":
    app.run(host='localhost', debug=True, port=5000)


