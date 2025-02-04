from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os
from flask_bcrypt import Bcrypt
import dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
dotenv.load_dotenv()

key_secret = os.getenv('FLASK_APP_KEY')
host_var = os.getenv('MYSQL_HOST')
user_var = os.getenv('MYSQL_USER')
pswd_var = os.getenv('MYSQL_PASSWORD')
db_var = os.getenv('MYSQL_DB')

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = key_secret
app.config['MYSQL_HOST'] = host_var
app.config['MYSQL_USER'] = user_var
app.config['MYSQL_PASSWORD'] = pswd_var
app.config['MYSQL_DB'] = db_var

mysql = MySQL(app)


cert_file = os.path.abspath('cert.pem')
pkey_file = os.path.abspath('key.pem')

restricted_usernames = {"administrator", "admin", "user", "user1", "test", "user2", "test1", "user3", "admin1",
                        "1", "123", "a", "actuser", "adm", "admin2", "aspnet", "backup", "console", "david",
                        "guest", "john", "owner", "root", "server", "sql", "support", "support_388945a0",
                        "sys", "test2", "test3", "user4", "user5"}


def valid_username(username):
    windows_invalid = re.compile(r'[/"\[\]:|<>+=;,?*@&]')
    linux_invalid = re.compile(r'^[a-zA-Z0-9]+$')
    if username.lower() in restricted_usernames:
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
                if image_offer == "Debian-11" or image_offer == "0001-com-ubuntu-server-jammy":
                    linux = "-Linux"
                else:
                    linux = ""

                shell_script = f"""
Connect-AzAccount

#Azure Account - Info
$resourcegroup = '{resource_group}'
$location = 'westeurope'

#VM Account - Info
$adminUsername = "{admin_username}"
$adminPassword = ConvertTo-SecureString "{admin_password}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($adminUsername, $adminPassword)

#VM - Info
$vmName = "{vm_name}"

$imagepub = "{image_publisher}"
$imageoffer = "{image_offer}"
$imagesku = "{image_sku}"

#Networking
$subnet_name = '{subnet}'
$vnet_name = '{virtual_network}'

#Resource Group
New-AzResourceGroup -Name $resourcegroup -Location $location

#Vnet
$subnet = New-AzVirtualNetworkSubnetConfig `
    -Name $subnet_name `
    -AddressPrefix "10.0.0.0/24"

New-AzVirtualNetwork -Name $vnet_name `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -AddressPrefix "10.0.0.0/16" `
    -Subnet $subnet

$Subnet = Get-AzVirtualNetwork -Name $vnet_name -ResourceGroupName $resourcegroup

$publicIP = New-AzPublicIPAddress `
    -Name "$vmName-ip" `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -AllocationMethod Static `
    -Sku Standard

$nic = New-AzNetworkInterface `
    -Name "$vmName-nic" `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -SubnetId $Subnet.Subnets[0].Id `
    -PublicIpAddressId $publicIp.Id

#Config of the virtual machine -VMSize has to be changed to v5. We only have access to deploy up to v4
$vm_config = New-AzVMConfig `
    -VMName $vmName `
    -VMSize "Standard_D2ds_v4" `
    -SecurityType "Standard" `
    -IdentityType "SystemAssigned"

$vm_config = Set-AzVMOperatingSystem `
    -VM $vm_config `
    -ComputerName $vmName `
    -Credential $credential `
    {linux}

$vm_config = Set-AzVMSourceImage `
    -VM $vm_config `
    -PublisherName "$imagepub" `
    -Offer "$imageoffer" `
    -Skus "$imagesku" `
    -Version "latest"


#Adds the networkinterface to the VM
$vm_config = Add-AzVMNetworkInterface `
    -VM $vm_config `
    -Id $nic.Id

$vm_config = Add-AzVMDataDisk `
    -VM $vm_config `
    -Name "disk1" `
    -DiskSizeInGB {disk_size} `
    -CreateOption "Empty" `
    -DeleteOption "Delete" `
    -Lun 1

New-AzVM `
    -ResourceGroupName $resourcegroup `
    -Location $location `
    -VM $vm_config
"""
                powershell_path = os.path.abspath('vm_create.ps1')
                with open(powershell_path, 'w') as ps_file:
                    ps_file.write(shell_script)
                msg = "Form submitted successfully"
                return send_file(powershell_path, as_attachment=True, download_name='vm_create.ps1')
        return render_template('form.html', username=session['username'], msg=msg)
    return redirect(url_for('login'))


app.run(host=('0.0.0.0'), ssl_context=(cert_file, pkey_file))
