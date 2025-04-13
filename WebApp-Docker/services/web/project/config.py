import os 

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static/"
    authority=os.getenv("AUTHORITY"),
    client_id=os.getenv("CLIENT_ID"),
    client_credential=os.getenv("CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI"),
    oidc_authority=os.getenv("OIDC_AUTHORITY"),
    b2c_tenant_name=os.getenv('B2C_TENANT_NAME'),
    b2c_signup_signin_user_flow=os.getenv('SIGNUPSIGNIN_USER_FLOW'),
    b2c_edit_profile_user_flow=os.getenv('EDITPROFILE_USER_FLOW'),
    b2c_reset_password_user_flow=os.getenv('RESETPASSWORD_USER_FLOW'),