FROM python:3.9-alpine3.13
LABEL maintainer="daniel arakcheev"

# run python and dont buffer the outputs so they appear on the screen
ENV PYTHONUNBUFFERED 1

# copy local files into the docker container
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# DEPLOY
COPY ./scripts /scripts 

COPY ./app /app
# use /app as the dir to run commands in
WORKDIR /app

# define container port to access the container
EXPOSE 8000

ARG DEV=false

# keep images lightweight by making one RUN command that contains all commands.
# This is because each run command creates a layer on the system
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts


# shell script installs dev deps conditionally
# we remove /tmp dir so that we dont install any other requirements so that docker image is as lightweight as possible
# adduser block adds new user inside our image
# not good to use the root user. if app gets comprimized then attacker gets full access to the entire application (db,code,etc)

# update PATH env var, prepends /py/bin to existing PATH variable
ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

# DEPLOY
CMD ["run.sh"]

# DEPLOY
# linux-headers
# chmod -R +x /scripts
# ENV PATH="/scripts:/py/bin:$PATH"