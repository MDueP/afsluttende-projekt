from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from msal import PublicClientApplication

app = PublicClientApplication("your_client_id", authority="https://login.microsoftonline.com/common")


def main():
    client = ComputeManagementClient(
        credential = DefaultAzureCredential(),
        subscription_id = "{subscription-id}",)
    
result = None

accounts = app.get_accounts()
if accounts:
    print("Pick an account to use to proceed:")
    for a in accounts:
        print(a["username"])
    chosen = accounts[0]
    result = app.acquire_token_silent(["User.Read"], account=chosen)
if not result:

    result = app.acquire_token_interactive(scopes=["User.Read"])
if "access_token" in result:
    print(result["access_token"])  
else:
    print(result.get("error"))
    print(result.get("error_description"))
    print(result.get("correlation_id")) 