"""Data provider module for Switzerland."""

from .energy_api import EnergyAPI

from typing import override

from datetime import datetime, date, timedelta
import dateutil

import aiohttp

from lru import LRU

import logging

_LOGGER = logging.getLogger(__name__)

PROVIDER_TO_DOMAIN: dict[str, str] = {
    "Switzerland (Energy Charts)": "CH",
    "Czech Republic (Energy Charts)": "CZ",
    "Hungary (Energy Charts)": "HU",
}


class EnergyCharts(EnergyAPI):
    """EnergyAPI for Energy-Charts.info."""

    def __init__(self, provider: str) -> None:
        """Initialize API."""
        self._daily_prices_cache: LRU[date, dict[int, float | None]] = LRU(10)
        self.session: aiohttp.ClientSession | None = None
        self.provider = PROVIDER_TO_DOMAIN[provider]

    @staticmethod
    @override
    async def providers() -> list[str]:
        return list(PROVIDER_TO_DOMAIN.keys())

    @override
    async def currency(self) -> str:
        return "EUR"

    @override
    async def price(self, dt: datetime) -> float | None:
        """Return price of electricity for specific datetime (hourly resolution)."""

        dt = dt.astimezone(dateutil.tz.UTC).replace(tzinfo=None)

        hour_rounded_dict = dt.hour
        date_key = dt.date()

        # check if we already fetched the data at some point:
        if date_key in self._daily_prices_cache:
            # last few values in dict might be None
            cached_price = self._daily_prices_cache[date_key].get(hour_rounded_dict)
            if cached_price is not None:
                return cached_price

        # build url + fetch data from there
        url = self._build_url(dt)
        json_data = await self._fetch_data(url)
        if json_data is None:
            return None

        # convert data into a dictionary
        prices_dict = self._parse_data(json_data, date_key)
        if prices_dict is None:
            return None

        # store data into cache (last few values might be none!)
        self._daily_prices_cache[date_key] = prices_dict

        return prices_dict.get(hour_rounded_dict)

    async def _fetch_data(self, url: str) -> dict | None:
        """Fetch data from the given URL."""

        json_data = None

        # Fetch data from the URL
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            self.session = session
            if response.status == 200:
                json_data = await response.json()
            else:
                _LOGGER.warning(f"Failed to retrieve data: {response.status}")

        return json_data

    # ruff: noqa: C901
    def _parse_data(self, json_data: dict, dt: date) -> dict[int, float | None] | None:
        """Return prices for one day in a form of dictionary."""

        if "price" not in json_data:
            return None

        prices = json_data["price"]

        prices_dict: dict[int, float | None] = {}
        for hour in range(24):
            if hour < len(prices):
                prices_dict[hour] = round(prices[hour] / 1000, 5)  # EUR/MWh -> EUR/kWh
            else:
                # for some reason there are only 21 prices available for the next day
                prices_dict[hour] = None

        return prices_dict

    def _build_url(self, date: datetime) -> str:
        """Return the URL for the one day."""

        # one day from 0.00 to 23.59
        start_date = date.replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=1) - timedelta(minutes=1)

        # converting to api's format
        start_str = start_date.isoformat(timespec="minutes")
        end_str = end_date.isoformat(timespec="minutes")

        url = f"https://api.energy-charts.info/price?bzn={self.provider}&start={start_str}&end={end_str}"
        return url
