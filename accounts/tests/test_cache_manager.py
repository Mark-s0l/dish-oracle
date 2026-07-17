from unittest.mock import Mock, patch

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from accounts.utils.cache_manager import (_MISSING, CacheConnectionError,
                                          CacheError, CacheManager,
                                          CacheTimeoutError)


@pytest.fixture(scope="module")
def cache_manager():
    return CacheManager(92)


class TestBuildKey:
    def test_build_key(self, cache_manager):
        assert cache_manager._build_key("attempt") == "user:92:attempt"


class TestExecute:

    def test_execute_connection_error(self, cache_manager):
        mock = Mock(side_effect=RedisConnectionError)
        with pytest.raises(CacheConnectionError):
            cache_manager._execute(mock)

    def test_execute_timeout(self, cache_manager):
        mock = Mock(side_effect=RedisTimeoutError)
        with pytest.raises(CacheTimeoutError):
            cache_manager._execute(mock)

    def test_execute_redis_error(self, cache_manager):
        mock = Mock(side_effect=RedisError)
        with pytest.raises(CacheError):
            cache_manager._execute(mock)

    def test_execute_successful(self, cache_manager):
        mock = Mock(return_value="data")
        result = cache_manager._execute(mock)
        assert result == "data"


class TestCacheGet:

    @patch("accounts.utils.cache_manager.cache")
    def test_get_cache(self, mock_cache, cache_manager):
        mock_cache.get.return_value = "data"
        result = cache_manager.cache_get("key")
        assert result == "data"

    @patch("accounts.utils.cache_manager.cache")
    def test_get_cache_missing(self, mock_cache, cache_manager):
        mock_cache.get.return_value = _MISSING
        result = cache_manager.cache_get("key")
        assert result is None

    @patch("accounts.utils.cache_manager.cache")
    def test_get_cache_missing_custom_default(self, mock_cache, cache_manager):
        mock_cache.get.return_value = _MISSING
        result = cache_manager.cache_get("key", default="fallback")
        assert result == "fallback"


class TestCacheSet:

    @patch("accounts.utils.cache_manager.cache")
    def test_set_cache(self, mock_cache, cache_manager):
        cache_manager.cache_set(key="key", data="data", timeout=100)
        mock_cache.set.assert_called_once_with("user:92:key", "data", timeout=100)

    @pytest.mark.parametrize("timeout", [0, -1, -100])
    def test_set_cache_invalid_timeout(self, cache_manager, timeout):
        with pytest.raises(ValueError):
            cache_manager.cache_set(key="key", data="data", timeout=timeout)

    @patch("accounts.utils.cache_manager.cache")
    def test_set_cache_timeout_str(self, mock_cache, cache_manager):
        with pytest.raises(TypeError):
            cache_manager.cache_set(key="key", data="data", timeout="raven")


class TestCacheDel:

    @patch("accounts.utils.cache_manager.cache")
    def test_del_cache(self, mock_cache, cache_manager):
        mock_cache.delete.return_value = True
        result = cache_manager.cache_del(key="key")
        assert result is True
        mock_cache.delete.assert_called_once_with("user:92:key")

    @patch("accounts.utils.cache_manager.cache")
    def test_del_cache_failed(self, mock_cache, cache_manager):
        mock_cache.delete.return_value = False
        result = cache_manager.cache_del(key="key")
        assert result is False
        mock_cache.delete.assert_called_once_with("user:92:key")
