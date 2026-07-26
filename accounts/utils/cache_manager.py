import logging
from typing import Any

from django.core.cache import cache
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

logger = logging.getLogger("accounts")

_MISSING = object()


class CacheError(Exception):
    pass


class CacheConnectionError(CacheError):
    pass


class CacheTimeoutError(CacheError):
    pass


class CacheManager:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def _build_key(self, key: Any) -> str:
        return f"user:{self.user_id}:{key}"

    def _execute(self, operation, *args, **kwargs):
        op_name = getattr(operation, "__name__", repr(operation))
        log_message = f"[CACHE] user_id={self.user_id}; operation={op_name}"
        try:
            return operation(*args, **kwargs)
        except RedisConnectionError as err:
            logger.error(log_message, exc_info=True)
            raise CacheConnectionError("Отсутствует подключение к Redis") from err
        except RedisTimeoutError as err:
            logger.error(log_message, exc_info=True)
            raise CacheTimeoutError("Тайм-аут подключения к Redis") from err
        except RedisError as err:
            logger.error(log_message, exc_info=True)
            raise CacheError("Ошибка кэша") from err

    def cache_get(self, key: str, default=None) -> Any:
        """Retrieve a value from the cache by key.

        The key is namespaced automatically as 'user:{user_id}:{key}'

        Args:
            key (str): The key to look up.
            default: Value to return if the key is not found. Defaults to None.

        Returns:
            Cached value or default if the key is missing.
        """
        data = self._execute(cache.get, self._build_key(key), _MISSING)
        if data is _MISSING:
            logger.debug(f"[CACHE] Missing cache; user_id={self.user_id}")
            return default
        else:
            return data

    def cache_set(self, key: str, data: Any, timeout: int) -> bool:
        """Set a value in the cache by key.

        The key is namespaced automatically as 'user:{user_id}:{key}'

        Args:
            key (str): The key to store the value under.
            data (Any): The value to write to the cache.
            timeout (int): Time-to-live (TTL) for the cache entry in seconds.

        Returns:
            bool: True if the value was stored successfully, False otherwise.
        """
        if timeout <= 0:
            raise ValueError(
                f"[CACHE] user_id={self.user_id}; "
                f"timeout must be postive, timeout={timeout}"
            )
        return self._execute(cache.set, self._build_key(key), data, timeout=timeout)

    def cache_del(self, key: str) -> bool:
        """Delete a value in the cache by key

        Args:
            key (str): the key to delete the value under.

        Returns:
            bool: True if the value was deleted successfully, False otherwise
        """
        return self._execute(cache.delete, self._build_key(key))
