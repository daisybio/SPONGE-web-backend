FROM community.wave.seqera.io/library/bioconductor-gsva_bioconductor-sponge_gunicorn_python_pruned:e9c5176f69f5398d

# System build deps (DuckDB Python wheels are usually prebuilt; build-essential kept for any native compiles).
# The DuckDB database file is mounted read-only at runtime and supplied via SPONGE_DB_URI
# (e.g. duckdb:////data/sponge.duckdb).
RUN apt-get update && apt-get install -y \
    pkg-config build-essential \
    && rm -rf /var/lib/apt/lists/*


# Install Python dependencies
WORKDIR /server
COPY requirements.txt /server/requirements.txt
RUN micromamba run pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /server

# Start the application using gunicorn with UvicornWorker
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5000", "-w", "4", "server:connex_app"]
