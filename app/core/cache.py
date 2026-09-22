"""Central in-memory caching engine with TTL, request deduplication, and stale-fallback."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, Callable, Awaitable
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import WeatherDataUnavailableError


class CacheEntry:
    """Represents a cached dataset with provenance and freshness metadata."""

    def __init__(
        self,
        data: Any,
        source: str,
        valid_time: str,
        ttl_seconds: int,
    ):
        self.data = data
        self.source = source
        self.fetched_at_dt = datetime.now(timezone.utc)
        self.fetched_at = self.fetched_at_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.valid_time = valid_time
        self.expires_at = time.time() + ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> int:
        return max(0, int(time.time() - self.fetched_at_dt.timestamp()))

    def get_freshness_metadata(self, is_stale: bool = False) -> Dict[str, Any]:
        return {
            "source": self.source,
            "fetched_at": self.fetched_at,
            "valid_time": self.valid_time,
            "stale": is_stale or self.is_expired,
            "age_seconds": self.age_seconds,
        }


class WeatherCache:
    """
    In-memory weather cache supporting:
    - Partitioned storage: current_weather, forecast, temperature_grid, wind_grid, precipitation_grid, air_quality_grid, timeline
    - Request deduplication: Coalesces concurrent identical provider requests into a single network call
    - Stale-while-revalidate / error fallback: Returns existing data with stale=True if provider is temporarily down
    """

    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._inflight: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()

    def get(self, key: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Retrieve data if exists and unexpired.
        Returns (data, metadata) or None if absent or expired.
        """
        entry = self._cache.get(key)
        if entry is None:
            return None
        if not entry.is_expired:
            logger.info(f"[WEATHER] cache hit for key={key}")
            return entry.data, entry.get_freshness_metadata(is_stale=False)
        logger.info(f"[WEATHER] cache expired for key={key}")
        return None

    def get_stale(self, key: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Retrieve cached entry as stale fallback if provider fails."""
        entry = self._cache.get(key)
        if entry is not None:
            logger.warning(f"[WEATHER] serving stale cache for key={key}")
            return entry.data, entry.get_freshness_metadata(is_stale=True)
        return None

    def set(
        self,
        key: str,
        data: Any,
        source: str,
        valid_time: str,
        ttl_seconds: int,
    ) -> Dict[str, Any]:
        """Store newly fetched provider data."""
        entry = CacheEntry(
            data=data,
            source=source,
            valid_time=valid_time,
            ttl_seconds=ttl_seconds,
        )
        self._cache[key] = entry
        logger.info(f"[WEATHER] cache updated for key={key} (ttl={ttl_seconds}s)")
        return entry.get_freshness_metadata(is_stale=False)

    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[Tuple[Any, str, str]]],
        ttl_seconds: int,
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Retrieve from cache or execute fetcher with request deduplication.
        fetcher must return (data, source, valid_time).
        """
        # 1. Fast cache check
        cached = self.get(key)
        if cached is not None:
            return cached

        # 2. Coordinate deduplication
        future_to_await = None
        is_initiator = False

        async with self._lock:
            # Recheck after acquiring lock
            cached = self.get(key)
            if cached is not None:
                return cached

            if key in self._inflight:
                future_to_await = self._inflight[key]
            else:
                is_initiator = True
                loop = asyncio.get_running_loop()
                fut = loop.create_future()
                self._inflight[key] = fut

        if not is_initiator and future_to_await:
            logger.debug(f"[WEATHER] coalescing request on inflight fetch key={key}")
            try:
                await future_to_await
                # Re-fetch from cache
                cached = self.get(key)
                if cached:
                    return cached
                stale = self.get_stale(key)
                if stale:
                    return stale
            except Exception:
                pass

        # 3. Initiator fetches from provider
        try:
            logger.info(f"[WEATHER] fetching Open-Meteo for key={key}")
            t0 = time.time()
            data, source, valid_time = await fetcher()
            dt_ms = (time.time() - t0) * 1000
            logger.info(f"[WEATHER] provider response 200 in {dt_ms:.1f}ms for key={key}")

            meta = self.set(key, data, source, valid_time, ttl_seconds)

            # Resolve inflight future
            async with self._lock:
                if key in self._inflight:
                    fut = self._inflight.pop(key)
                    if not fut.done():
                        fut.set_result(True)

            return data, meta

        except Exception as exc:
            logger.error(f"[WEATHER] provider failure for key={key}: {exc}")
            # Reject inflight future safely without unhandled exception warning
            async with self._lock:
                if key in self._inflight:
                    fut = self._inflight.pop(key)
                    if not fut.done():
                        fut.set_result(False)

            # Check if stale cached data exists
            stale = self.get_stale(key)
            if stale is not None:
                return stale

            # Hard failure: no data at all -> HTTP 503
            raise WeatherDataUnavailableError(
                message=f"Live weather data is temporarily unavailable: {str(exc)}",
                source="open-meteo",
                retryable=True,
            )


# Global singleton instance
weather_cache = WeatherCache()
