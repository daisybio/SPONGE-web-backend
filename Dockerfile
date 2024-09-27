FROM python:3.12.6-bullseye

# Install required packages using apt
RUN apt-get update && apt-get install -y \
    libmariadb3 libmariadb-dev build-essential linux-headers-amd64 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

WORKDIR /server
COPY . /server

RUN pip3 --no-cache-dir install -r requirements.txt

# the mariadb plugin directory seems to be misconfigured
# bei default. In order to work properly we manually adjust
# the path.
ENV MARIADB_PLUGIN_DIR /usr/lib/mariadb/plugin

# EXPOSE 5000
# CMD ["python3", "server.py"]

#run the command to start uWSGI
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5000", "-w", "4", "server:connex_app"]

