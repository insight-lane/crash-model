FROM continuumio/miniconda
# update
RUN conda update -n base conda

# Set package installer as non-interactive
ENV DEBIAN_FRONTEND noninteractive

# Set a terminal type
ENV TERM xterm-256color

WORKDIR /app

# Install packges
# (gcc) installed to enable conda to create virtual environments
RUN apt-get update -qq && apt-get install -y \
	gcc \
	g++ \
	# apache for serving the visualisation
	apache2 \
	# easier management of services via supervisor
	supervisor \
	# base anaconda image seems to lack libgl support required for our virtual environment
	libgl1-mesa-glx \
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

# Use bash for the entrypoint rather than sh, for 'conda activate' compatibility
ENTRYPOINT ["/bin/bash", "-c"]

# RUN ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

# Activate the virtual environment (fulfils the work of 'source activate boston-crash-model' without the overhead)
# ENV PATH /opt/conda/envs/boston-crash-model/bin:$PATH
# RUN ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh
# RUN echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc
# RUN conda activate boston-crash-model
RUN echo "conda activate boston-crash-model" >> ~/.bashrc

# the default PS1 has issues with long outputs, replace it
# RUN echo "swapping to a PS1 that better handles long outputs" >> /etc/bash.bashrc
# RUN echo "PS1='\h:\W \u\$ '" >> /etc/bash.bashrc
# RUN echo "PS1='\h:\W \u\$ '" >> ~/.bashrc

# this startup script runs supervisor in foreground (which in turn starts apache) to keep container running
CMD ["/start.sh"]

# Make the apache port available
EXPOSE 8080
