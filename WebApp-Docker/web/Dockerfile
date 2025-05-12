FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

RUN apt update && apt-get install -y --no-install-recommends gcc

RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

FROM base

RUN mkdir -p /home/app
RUN addgroup --system app && adduser --system --group app

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN apt update && apt-get install -y --no-install-recommends netcat-openbsd

COPY --from=base /usr/src/app/wheels /wheels
COPY --from=base /app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY . $APP_HOME

RUN chown -R app:app $APP_HOME
RUN mkdir -p $APP_HOME/flask_session && \
chmod -R 777 $APP_HOME/flask_session && \
chown -R app:app $APP_HOME/flask_session
USER app

EXPOSE 5000
