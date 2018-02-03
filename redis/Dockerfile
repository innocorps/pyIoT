FROM redis:4.0
RUN apt-get update && apt-get install -y \
  coreutils \
  vim \
  dos2unix
COPY redis.conf /usr/local/etc/redis/redis.conf
RUN dos2unix /usr/local/etc/redis/redis.conf
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
