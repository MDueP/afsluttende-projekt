

### Simpel Docker-setup med Postgres, Gunicorn og Nginx

    Inspiration og hjælp fra: https://github.com/testdrivenio/flask-on-docker/tree/main





### Ved ændringer eller første setup husk --build
    docker-compose --profile prod up -d --build
    
    docker-compose --profile prod down -v



### Syntaxer:
    Prod for produktion (med Nginx og Gunicorn)

    dev for development (uden nginx og Gunicorn)

### Ændringer i filer og deres funktioner

    requirements.txt - Anvende Python moduler og andre dependencies

    manage.py - implementation af CLI CMD der skal køre ved opstart af Docker build.

    config.py - Path variabler for class objektet Config

    __init__.py - Selveste Flask Applikationen bruger config.py og dets object for Path variabler

    entrypoint.sh - Bash script der sørgere for at Postgres bliver kørt ordentligt. Ved $FLASK_DEBUG = 1 kører dev version af bash script

    .env.* - Består af forskellige variabler der bliver brugt i docker-compose.yml

    nginx.conf - Configuration fil der erstatter den originale

### .env filer - Standard (Ændre dem ellers kan der være sikkerhedsrisiko)
    F.eks. .env.dev: 
        FLASK_APP=project/__init__.py
        FLASK_DEBUG=1
        DATABASE_URL=postgresql://flask_nginx:flask_nginx@db:5432/flask_nginx_dev
        SQL_HOST=db
        SQL_PORT=5432
        DATABASE=postgres
        APP_FOLDER=/usr/src/app

    F.eks. .env.dev.db:
        POSTGRES_USER=flask_nginx
        POSTGRES_PASSWORD=flask_nginx
        POSTGRES_DB=flask_nginx_dev
