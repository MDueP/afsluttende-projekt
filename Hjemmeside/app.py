import requests
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_file,
    jsonify,
)
from flask_session import Session
import app_config
import re
import os
import uuid
from msal import ConfidentialClientApplication

app = Flask(__name__)
app.config.from_object(app_config.Config)

Session(app)


msal_app = ConfidentialClientApplication(
    app.config["CLIENT_ID"],
    authority=app.config["AUTHORITY"],
    client_credential=app.config["CLIENT_SECRET"],
)


def valid_username(username):
    windows_invalid = re.compile(r'[/"\[\]:|<>+=;,?*@&]')
    linux_invalid = re.compile(r"^[a-zA-Z0-9]+$")
    if username.lower() in os.getenv("restricted_usernames"):
        return False, "That username is too generic and is not allowed"
    if windows_invalid.search(username) or username.endswith("."):
        return False, "Username cannot contain special characters /" "[]:|<>+=;,?*@&"
    if not linux_invalid.match(username):
        return (
            False,
            "Username must only contain letters, numbers, hyphens, and underscores",
        )
    if len(username) > 20:
        return False, "Username exceeds maximum length"
    return True, ""


def valid_password(password):
    password_contains = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{12,123}$"
    )
    return password_contains.match(password)


def gen_shell_script(template_path, **kwargs):
    with open(template_path, "r") as template_file:
        template = template_file.read()
    return template.format(**kwargs)


@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = msal_app.get_authorization_request_url(
        app.config["SCOPE"],
        state=session["state"],
        redirect_uri=url_for("auth_response", _external=True),
    )
    return redirect(auth_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route(app.config["REDIRECT_PATH"])
def auth_response():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("auth_error"))

    code = request.args.get("code")
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=app.config["SCOPE"],
        redirect_uri=url_for("auth_response", _external=True),
    )

    if "access_token" in result:
        session["user"] = result.get("id_token_claims")
        session["access_token"] = result["access_token"]
        return redirect(url_for("home"))
    else:
        return redirect(url_for("auth_error"))


@app.route("/call_downstream_api")
def call_downstream_api():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401
    api_result = requests.get(
        app.config["ENDPOINT"],
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ).json()
    return jsonify(api_result)


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.route("/auth_error")
def auth_error():
    return render_template("auth_error.html", result={})


@app.route("/api/list-resource-groups")
def list_resource_groups():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    subscription_id = request.args.get("subscription_id")
    if not subscription_id:
        return jsonify({"error": "Missing subscription_id"}), 400

    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourcegroups?api-version=2021-04-01"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        groups = response.json().get("value", [])
        result = [group["name"] for group in groups]
        return jsonify(result)
    else:
        return jsonify({"error": response.text}), response.status_code


@app.route("/")
def home():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("home.html", user=session["user"])


@app.route("/vm_form")
def show_vm_form():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template(
        "form.html", username=session.get("user", {}).get("name"), msg=""
    )


@app.route("/deploy", methods=["POST"])
def deploy_vm():
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))

    resource_group = request.form["resource_group"]
    vm_name = request.form["vm_name"]
    location = request.form["location"]
    admin_username = request.form["admin_username"]
    admin_password = request.form["admin_password"]
    os_image = request.form["os_image"]
    disk_size = request.form["disk_size"]
    virtual_network = request.form["virtual_network"]  # extra
    subnet = request.form["subnet"]  # extra
    subscription_id = request.form["subscription_id"]  # extra
    vm_size = request.form["vm_size"]
    nic_id = request.form["nic_id"]  # extra

    publisher, offer, sku = os_image.split(";")

    bicep_template = f"""
param adminUsername string = '{admin_username}'
param adminPassword string = '{admin_password}'
param vmName string = '{vm_name}'
param location string = '{location}'
param subnetId string =

resource vm 'Microsoft.Compute/virtualMachines@2021-03-01' = {{
    name: vmName
    location: location
    properties: {{
        hardwareProfile: {{
            vmSize: '{vm_size}'
        }}
        osProfile: {{
            computerName: vmName
            adminUsername: adminUsername
            adminPassword: adminPassword
        }}
        storageProfile: {{
            imageReference: {{
                publisher: '{publisher}'
                offer: '{offer}'
                sku: '{sku}'
                version: 'latest'
            }}
            osDisk: {{
                createOption: 'FromImage'
                diskSizeGB: {disk_size}
            }}
        }}
        networkProfile: {{
             networkInterfaces: [
        {{
          id: '/subscriptions/<subscription-id>/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/${{vmName}}NIC'
        }}
      ]
    }}
  }}
}}
"""

    session["bicep_template"] = bicep_template

    return render_template("bicep_preview.html", bicep_code=bicep_template)
