import requests
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
from flask_session import Session
import app_config
import re
import os
import uuid
from msal import ConfidentialClientApplication
import json


######################
# Encapsulation
app = Flask(__name__)
app.config.from_object(app_config.Config)

Session(app)


msal_app = ConfidentialClientApplication(
    app.config["CLIENT_ID"],
    authority=app.config["AUTHORITY"],
    client_credential=app.config["CLIENT_SECRET"],
)

###############
# Gets - Oplysninger


def get_access_token():
    if "access_token" in session:
        return session["access_token"]
    return None


##############
# Role Assignment


def rolletildeling(subscription_id, resource_group, role, user_object_id, access_token):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Authorization/roleAssignments/{str(uuid.uuid4())}?api-version=2021-04-01"

    role_def_id = f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignments/{role}"

    payload = {
        "properties": {"roleDefinitionID": role_def_id, "principalId": user_object_id}
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.put(url, data=json.dumps(payload), headers=headers)

    if response.status_code == 201:
        return "Role assignment successful"
    else:
        return f"Error: {response.status_code}, {response.text}"


##############
# Funktioner


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


################################
# Route


@app.route("/")
def home():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("home.html", user=session["user"])


@app.route("/login")
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = msal_app.get_authorization_request_url(
        scopes=app.config["SCOPE"],
        state=session["state"],
        redirect_uri=url_for("authorized", _external=True),
    )
    return redirect(auth_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route(app.config["TOKEN_URI"])
def authorized():
    if request.args.get("state") != session.get("state"):
        return "State error", 400

    code = request.args.get("code")
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=app.config["SCOPE"],
        redirect_uri=url_for("authorized", _external=True),
    )

    if "access_token" in result:
        session["access_token"] = result["access_token"]
        session["user"] = result.get("id_token_claims", {})
        session["account"] = result.get("id_token_claims", {}).get("oid")
        return redirect(url_for("home"))
    return f"error: {result.get('error_description')}"


@app.route("/subscriptions")
def subscriptions():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://management.azure.com/subscriptions?api-version=2020-01-01",
        headers=headers,
        timeout=30,
    ).json()
    return jsonify(response)


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
    return "This page does not exist", 404


@app.route("/auth_error")
def auth_error():
    return render_template("auth_error.html", result={})


@app.route("/arm_authorized")
def arm_authorized():
    print("Request state:", request.args.get("state"))
    print("Session state:", session.get("state"))
    if request.args.get("state") != session.get("state"):
        return "State error", 400

    code = request.args.get("code")
    print(code)
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=["https://management.azure.com/.default"],
        redirect_uri=url_for("arm_authorized", _external=True),
    )
    print("Result:", result)
    if "access_token" in result:
        session["access_token"] = result["access_token"]
        session["user"] = result.get("id_token_claims", {})
        session["account"] = result.get("id_token_claims", {}).get("oid")
        return redirect(url_for("subscriptions"))
    return f"error: {result.get('error_description')}"


@app.route("/list-resource-groups")
def list_resource_groups():
    token = get_access_token()
    if not token:
        return redirect(url_for("login"))

    endpoint = "https://management.azure.com/subscriptions?api-version=2020-01-01"

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(endpoint, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching subscriptionID: {response}, {response.text}")
        return jsonify({"error": "Couldn't fetch SubscriptionID"}), 400
    sub_data = response.json().get("value", [])
    if not sub_data:
        return jsonify({"error": "No Subscriptions found"}), 404

    subscription_id = sub_data[0]["subscriptionId"]
    rg_endpoint = f"https://management.azure.com/subscriptions/{subscription_id}/resourcegroups?api-version=2021-04-01"
    rg_response = requests.get(rg_endpoint, headers=headers)

    if rg_response.status_code == 200:
        groups = rg_response.json().get("value", [])
        group_names = [group["name"] for group in groups]

        return render_template("resource_group.html", groups=group_names)
    else:
        print(
            f"Error fetching resource groups: {rg_response.status_code}, {rg_response.text}"
        )
        return jsonify({"error": "could not fetch resource groups"}), 400


@app.route("/vm_form")
def show_vm_form():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("form.html", user=session["user"])


# @app.route("/deploy", methods=["POST"])
# def deploy_vm():
#     token = get_azure_token
#     if not token:
#         return redirect(url_for("login"))

#     resource_group = request.form["resource_group"]
#     vm_name = request.form["vm_name"]
#     location = request.form["location"]
#     admin_username = request.form["admin_username"]
#     admin_password = request.form["admin_password"]
#     os_image = request.form["os_image"]
#     disk_size = request.form["disk_size"]
#     virtual_network = request.form["virtual_network"]
#     subnet = request.form["subnet"]
#     subscription_id = request.form["subscription_id"]  # extra
#     vm_size = request.form["vm_size"]
#     nic_id = request.form["nic_id"]  # extra

#     publisher, offer, sku = os_image.split(";")

#     payload = {
#         "location": location,
#         "properties": {
#             "hardwareProfile": {"vmSize": vm_size},
#             "storageProfile": {
#                 "imageReference": {
#                     "publisher": publisher,
#                     "offer": offer,
#                     "sku": sku,
#                     "version": "latest",
#                 },
#                 "osDisk": {"createOption": "FromImage", "diskSizeGB": disk_size},
#             },
#             "osProfile": {
#                 "computerName": vm_name,
#                 "adminUsername": admin_username,
#                 "adminPassword": admin_password,
#             },
#             "networkProfile": {"networkInterfaces": [{"id": nic_id}]},
#         },
#     }

#     endpoint = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}?api-version=2023-07-01"

#     response = requests.put(
#         endpoint,
#         headers={
#             "Authorization": f"Bearer {token}",
#             "Content-Type": "application/json",
#         },
#         json=payload,
#         timeout=60,
#     )

#     if response.status_code in [200, 201, 202]:
#         return jsonify(
#             {"message": "VM deployment started!", "details": response.json()}
#         )
#     else:
#         return jsonify({"error": response.text}), response.status_code


########################################
# App Run

app.run(host="localhost", debug=True, port=5000)
