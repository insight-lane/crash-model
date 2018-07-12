FROM continuumio/miniconda3
# update
RUN conda update -n base conda

# Set package installer as non-interactive
ENV DEBIAN_FRONTEND noninteractive

# Set a terminal type
ENV TERM xterm-256color

WORKDIR /app

# Install packges
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
	# apache for serving the visualisation
	apache2 \
	# easier management of services via supervisor
	supervisor \
	# base anaconda image seems to lack libgl support required for our virtual environment
	libgl1-mesa-glx \
	# handy text editor
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

# Setup the project's virtual environment
COPY environment.yml /app/environment.yml
RUN ["conda", "env", "create", "--file", "environment.yml"]

# Use bash for the entrypoint rather than sh, for 'conda activate' compatibility
ENTRYPOINT ["/bin/bash", "-c"]

# Activate the project's virtual environment
RUN echo "conda activate crash-model" >> ~/.bashrc

# this startup script runs supervisor in foreground (which in turn starts apache) to keep container running
CMD ["/start.sh"]

# Make the apache port available
EXPOSE 8080
