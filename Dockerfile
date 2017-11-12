FROM continuumio/anaconda

EXPOSE 5000

# Install gcc so that conda create a virtual env
RUN apt-get update && apt-get install -y gcc

# Add the project code
ADD . /code

# Use the environment_docker.yml to create the conda environment
WORKDIR /code
RUN ["conda", "env", "create", "--file", "environment_docker.yml"]

# Conda explicitly supports bash (amongst other shells), and explicitly doesn’t support sh
# Set the ENTRYPOINT to use bash and source the new environment when executing a container
ENTRYPOINT ["/bin/bash", "-c", "source activate boston-crash-model"]
