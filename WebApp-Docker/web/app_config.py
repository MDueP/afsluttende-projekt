import os
import dotenv

dotenv.load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    AUTHORITY = os.getenv("AUTHORITY")
    TOKEN_URI = os.getenv("TOKEN_URI")
    SCOPE = os.getenv("SCOPE", "").split(",")
    SESSION_TYPE = os.getenv("SESSION_TYPE")
    ENDPOINT = os.getenv("ENDPOINT")
    SECRETKEY = os.getenv("SECRETKEY")
