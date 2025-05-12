import os
import dotenv

dotenv.load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    AUTHORITY = "https://login.microsoftonline.com/common"
    TOKEN_URI = "/getAToken"
    SCOPE = ["https://management.azure.com/user_impersonation"]
    SESSION_TYPE = "filesystem"
    ENDPOINT = "https://graph.microsoft.com/v1.0/users"
