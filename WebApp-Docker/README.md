

# Simpel Docker-setup med Postgres, Gunicorn og Nginx



    
### Ved ændringer eller første setup husk
    
    docker-compose build

    docker-compose up -d

    docker-compose down (-v)

### Ændringer i filer og deres funktioner

    requirements.txt - Anvende Python moduler og andre dependencies

    config.py - Path variabler for class objektet Config

    __init__.py - Selveste Flask Applikationen bruger config.py og dets object for Path variabler

    .env.* - Består af forskellige variabler der bliver brugt i docker-compose.yml

### .env filer - Standard (Ændre dem ellers kan der være sikkerhedsrisiko)
    CLIENT_ID="xxxxxxxxxxxxxxxxxxx"
    CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxx"
    AUTHORITY = "https://login.microsoftonline.com/common"
    TOKEN_URI = "/getAToken"
    SCOPE =https://management.azure.com/user_impersonation
    SESSION_TYPE = "filesystem"
    ENDPOINT = "https://management.azure.com/subscriptions?api-version=2020-01-01"
