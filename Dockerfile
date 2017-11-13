FROM continuumio/anaconda

# Set package installer as non-interactive
ENV DEBIAN_FRONTEND noninteractive

# Set a terminal type
ENV TERM xterm-256color

# Use bash for the entrypoint rather than sh, for 'conda activate' compatibility
ENTRYPOINT ["/bin/bash", "-c"]

WORKDIR /app

# Install packges
# (gcc) installed to enable conda to create virtual environments
RUN apt-get update -qq && apt-get install -y \
	gcc \
	apache2 \
	supervisor \
	vim

# Setup apache & supervisor
RUN rm -rf /var/www/html && ln -s /app /var/www/html
ADD conf/bcm.conf /etc/apache2/sites-available/bcm.conf
RUN ln -s /etc/apache2/sites-available/bcm.conf /etc/apache2/sites-enabled/bcm.conf
RUN a2enmod rewrite
ADD conf/supervisord.conf /etc/supervisord.conf

# Make sure processes are stopped
RUN service apache2 stop && service supervisor stop

# Entrypoint script that will kick off supervisor (which in turn starts apache)
ADD conf/start.sh /start.sh
RUN chmod +x /start.sh

# Setup the app's virtual environment
COPY environment_docker.yml /app/environment_docker.yml
RUN ["conda", "env", "create", "--file", "environment_docker.yml"]

# Copy over the app
COPY . /app

# Activate the virtual environment (fulfils the work of 'source activate boston-crash-model' without the overhead)
ENV PATH /opt/conda/envs/boston-crash-model/bin:$PATH

# On startup:
# call the script to generate historical crash map
# hand off to entrypoint script
# CMD ["python historical_crash_map.py && /start.sh"]
CMD ["/start.sh"]

# Make the apache port available
EXPOSE 8080
