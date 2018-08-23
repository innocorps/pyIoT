FROM nginx:1.15
RUN apt-get update && apt-get install -y \
  coreutils \
  vim \
  openssl \ 
  dos2unix
# Remove the default nginx configuration file
RUN rm /etc/nginx/nginx.conf
# Copy over the new default configuration
COPY nginx.conf /etc/nginx/
RUN dos2unix /etc/nginx/nginx.conf

RUN rm /etc/nginx/conf.d/default.conf
COPY backend.conf /etc/nginx/conf.d/
RUN dos2unix /etc/nginx/conf.d/backend.conf

COPY wait-for-it.sh /opt/wait-for-it.sh
RUN dos2unix /opt/wait-for-it.sh
