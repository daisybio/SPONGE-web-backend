FROM community.wave.seqera.io/library/bioconductor-gsva_bioconductor-sponge_gunicorn_python_pruned:e9c5176f69f5398d

# Install required system dependencies for MySQL, R, and Conda
RUN apt-get update && apt-get install -y \
    default-mysql-client pkg-config default-libmysqlclient-dev build-essential \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
WORKDIR /server
COPY requirements.txt /server/requirements.txt
RUN micromamba run pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /server

# Start the application using gunicorn with UvicornWorker
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5000", "-w", "4", "server:connex_app"]

