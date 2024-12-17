FROM continuumio/miniconda3:24.11.1-0

WORKDIR /server

# First copy only the environment file and install the dependencies
# This way we can cache the dependencies and only rebuild the image when the environment file changes
COPY environment.yml /server/environment.yml
RUN conda env update -f environment.yml

# Copy the rest of the files
COPY . /server

# Run the command to start uWSGI
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5000", "-w", "4", "server:connex_app"]
