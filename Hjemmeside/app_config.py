import os
import dotenv
dotenv.load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static/"
    
    AUTHORITY = os.getenv("AUTHORITY", "https://login.microsoftonline.com/common")
    CLIENT_ID=os.getenv("CLIENT_ID")
    CLIENT_SECRET=os.getenv("CLIENT_SECRET")
    
    REDIRECT_PATH = "/getAToken"
    ENDPOINT = 'https://graph.microsoft.com/v1.0/users'
    SCOPE = ["Files.Read"]
    SESSION_TYPE = "filesystem"
    