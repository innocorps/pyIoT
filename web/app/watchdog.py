"""
Creates a thread safe timer for watchdog applications
"""
import strict_rfc3339
from redis import RedisError
from flask import current_app


class Watchdog():
    """
    Originally a thearding.Timer, reimplemented writing to a shared
    Redis cache so that replicas can check to see when the last heartbeat
    or POST of data was received. Compares the stored value of datetime to
    the current datetime.

    Attributes:
        timeout: Timer timemout parameter in seconds
        cache: cache object that is used by the main app

    """

    def __init__(self, timeout, cache):  # timeout in seconds
        self.timeout = timeout
        self.cache = cache

    def get_current_utc(self):
        return strict_rfc3339.now_to_rfc3339_utcoffset()

    def get_last_pet(self):
        last_pet = self.cache.get('watchdog_datetime')
        if last_pet is None:
            return strict_rfc3339.timestamp_to_rfc3339_utcoffset(0)
        else:
            return last_pet

    def is_alive(self):
        current_epoch = strict_rfc3339.rfc3339_to_timestamp(
            self.get_current_utc())
        last_pet_epoch = strict_rfc3339.rfc3339_to_timestamp(
            self.get_last_pet())
        delta_t = current_epoch - last_pet_epoch
        if delta_t > self.timeout:
            return False
        else:
            return True

    def pet(self):
        try:
            self.cache.set('watchdog_datetime', self.get_current_utc(),
                           timeout=current_app.config['REDIS_CACHE_TIMEOUT'])
        except RedisError as e:
            print(e)
            print('watchdog: Redis port may be closed. '
                  'Redis does not appear to be running.')
