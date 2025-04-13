FROM python:3.12-slim AS base
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

FROM base AS dev
WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

COPY . /usr/src/app/

RUN chmod +x /usr/src/app/entrypoint.sh  # Ensure script is executable

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

FROM dev AS lint
RUN pip install flake8==6.0.0 && flake8 --ignore=E501,F401 .

FROM base AS prod

RUN mkdir -p /home/app

RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd

COPY --from=base /usr/src/app/wheels /wheels
COPY --from=base /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY ./entrypoint.sh $APP_HOME
COPY . $APP_HOME
RUN chmod +x $APP_HOME/entrypoint.sh
RUN chown -R app:app $APP_HOME
USER app
ENTRYPOINT ["/home/app/web/entrypoint.sh"]