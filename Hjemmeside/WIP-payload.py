import uuid
import json
import requests
from flask import Flask, session, redirect, url_for, request, render_template, jsonify
from msal import ConfidentialClientApplication
from flask_session import Session
import app_config

app = Flask(__name__)
app.config.from_object(app_config.Config)


msal_app = ConfidentialClientApplication(
    app.config["CLIENT_ID"],
    authority=app.config["AUTHORITY"],
    client_credential=app.config["CLIENT_SECRET"],
)


@app.route("/deploy", methods=["POST"])
def deploy_vm():
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    sub_response = requests.get(
        "https://management.azure.com/subscriptions?api-version=2020-01-01",
        headers=headers,
    )
    if sub_response.status_code != 200:
        return jsonify({"error": "Couldn't fetch SubscriptionID"}), 400
    sub_data = sub_response.json().get("value", [])
    if not sub_data:
        return jsonify({"error": "No Subscriptions found"}), 404

    subscription_id = sub_data[0]["subscriptionId"]

    resource_group = request.form["resource_group"]
    vm_name = request.form["vm_name"]
    location = request.form["location"]
    vm_size = request.form["vm_size"]

    vnet_name = f"{vm_name}-vnet"
    subnet_name = f"{vm_name}-subnet"
    ip_name = f"{vm_name}-ip"
    nic_name = f"{vm_name}-nic"

    vnet_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}?api-version=2023-04-01"
    vnet_payload = {
        "location": location,
        "properties": {
            "addressSpace": {"addressPrefixes": ["10.0.0.0/16"]},
            "subnets": [
                {"name": subnet_name, "properties": {"addressPrefix": "10.0.0.0/24"}}
            ],
        },
    }
    vnet_resp = requests.put(vnet_url, headers=headers, json=vnet_payload)
    if vnet_resp.status_code not in [200, 201, 202]:
        return f"Failed creating VNet: {vnet_resp.text}", 400

    ip_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{ip_name}?api-version=2023-04-01"
    ip_payload = {
        "location": location,
        "sku": {"name": "Standard"},
        "properties": {"publicIPAllocationMethod": "Static"},
    }
    ip_resp = requests.put(ip_url, headers=headers, json=ip_payload)
    if ip_resp.status_code not in [200, 201, 202]:
        return f"Failed creating Public IP: {ip_resp.text}", 400

    nic_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/{nic_name}?api-version=2023-04-01"
    nic_payload = {
        "location": location,
        "properties": {
            "ipConfigurations": [
                {
                    "name": "ipconfig1",
                    "properties": {
                        "subnet": {
                            "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{subnet_name}"
                        },
                        "publicIPAddress": {
                            "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/publicIPAddresses/{ip_name}"
                        },
                    },
                }
            ]
        },
    }
    nic_resp = requests.put(nic_url, headers=headers, json=nic_payload)
    if nic_resp.status_code not in [200, 201, 202]:
        return f"Failed creating NIC: {nic_resp.text}", 400

    vm_url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}?api-version=2022-03-01"
    vm_payload = {
        "location": location,
        "identity": {"type": "SystemAssigned"},
        "properties": {
            "hardwareProfile": {"vmSize": vm_size},
            "storageProfile": {
                "imageReference": {
                    "publisher": "Canonical",
                    "offer": "UbuntuServer",
                    "sku": "18.04-LTS",
                    "version": "latest",
                },
                "osDisk": {
                    "createOption": "FromImage",
                    "deleteOption": "Delete",
                    "managedDisk": {"storageAccountType": "Standard_LRS"},
                },
                "dataDisks": [
                    {
                        "lun": 1,
                        "createOption": "Empty",
                        "diskSizeGB": 64,
                        "deleteOption": "Delete",
                    }
                ],
            },
            "osProfile": {
                "computerName": vm_name,
                "adminUsername": "azureuser",
                "adminPassword": "ChangeM3Now!",
                "linuxConfiguration": {"disablePasswordAuthentication": False},
            },
            "networkProfile": {
                "networkInterfaces": [
                    {
                        "id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/networkInterfaces/{nic_name}",
                        "properties": {"primary": True},
                    }
                ]
            },
        },
    }
    vm_resp = requests.put(vm_url, headers=headers, json=vm_payload)

    return f"<pre>{vm_resp.status_code}\n{vm_resp.text}</pre>"
