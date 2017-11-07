FROM continuumio/anaconda

# Set the ENTRYPOINT to use bash
# (this is also where you'd set SHELL,
# if your version of docker supports this)
ENTRYPOINT [ "/bin/bash", "-c" ]

EXPOSE 5000

# install gcc so that conda create a virtual env
RUN apt-get update && apt-get install -y gcc

# Use the environment_docker.yml to create the conda environment.
ADD environment_docker.yml /tmp/environment_docker.yml
WORKDIR /tmp
RUN [ "conda", "env", "create", "--file", "environment_docker.yml" ]

ADD . /code

# Use bash to source our new environment for setting up
# private dependencies—note that /bin/bash is called in
# exec mode directly
WORKDIR /code
# RUN [ "/bin/bash", "-c", "source activate boston-crash-model && python setup.py develop" ]
RUN [ "/bin/bash", "-c", "source activate boston-crash-model" ]

# We set ENTRYPOINT, so while we still use exec mode, we don't
# explicitly call /bin/bash
# CMD [ "source activate your-environment && exec python application.py" ]
