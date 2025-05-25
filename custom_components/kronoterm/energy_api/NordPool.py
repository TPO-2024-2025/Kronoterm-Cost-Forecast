"""Data provider module for NordPool."""

import asyncio
from datetime import datetime
from typing import override
import urllib
import dateutil
from lru import LRU
from collections.abc import MutableMapping

import aiohttp as ahttp

from custom_components.kronoterm.energy_api.energy_api import EnergyAPI

BASE_URL: str = "https://dataportal-api.nordpoolgroup.com/api/DayAheadPriceIndices"

PROVIDER_TO_INTERNAL_PROVIDER_AND_CURRENCY: dict[str, tuple[str, str]] = {
    "Eesti (NordPool)": ("EE", "EUR"),  # Estonija
    "Lietuva (NordPool)": ("LT", "EUR"),  # Litva
    "Latvija (NordPool)": ("LV", "EUR"),  # Latvija
    "Österreich (NordPool)": ("AT", "EUR"),  # Avstrija
    "Belgien (NordPool)": ("BE", "EUR"),  # Belgija
    "France (NordPool)": ("FR", "EUR"),  # Francija
    "Deutschland (NordPool)": ("GER", "EUR"),  # Nemčija
    "Nederland (NordPool)": ("NL", "EUR"),  # Nizozemska
    "Polska PLN (NordPool)": ("PL", "PLN"),  # Polska
    "Danmark 1 DKK (NordPool)": ("DK1", "DKK"),  # Danska 1
    "Danmark 2 DKK (NordPool)": ("DK2", "DKK"),  # Danska 2
    "Suomi (NordPool)": ("FI", "EUR"),  # Finska
    "Norge 1 NOK (NordPool)": ("NO1", "NOK"),  # Norveška 1
    "Norge 2 NOK (NordPool)": ("NO2", "NOK"),  # Norveška 2
    "Norge 3 NOK (NordPool)": ("NO3", "NOK"),  # Norveška 3
    "Norge 4 NOK (NordPool)": ("NO4", "NOK"),  # Norveška 4
    "Norge 5 NOK (NordPool)": ("NO5", "NOK"),  # Norveška 5
    "Sverige 1 SEK (NordPool)": ("SE1", "SEK"),  # Švedska 1
    "Sverige 2 SEK (NordPool)": ("SE2", "SEK"),  # Švedska 2
    "Sverige 3 SEK (NordPool)": ("SE3", "SEK"),  # Švedska 3
    "Sverige 4 SEK (NordPool)": ("SE4", "SEK"),  # Švedska 4
    "United Kingdom (NordPool)": ("UK", "GBP"),  # Švedska 4
}

MARKETS = ["DayAhead", "N2EX_DayAhead"]  # 0: all but UK, 1: UK


class NordPool(EnergyAPI):
    """EnergyAPI for NordPool."""

    _internal_provider: str
    _currency: str
    _price_cache: MutableMapping[tuple[int, int, int], list[float]]

    @override
    def __init__(self, provider: str) -> None:
        entry = PROVIDER_TO_INTERNAL_PROVIDER_AND_CURRENCY.get(provider)

        if entry is None:
            raise ValueError(f"Unknown NordPool provider {provider}")

        self._internal_provider = entry[0]
        self._currency = entry[1]
        self._price_cache = LRU(10)  # type: ignore

    @override
    @staticmethod
    async def providers() -> list[str]:
        return list(PROVIDER_TO_INTERNAL_PROVIDER_AND_CURRENCY.keys())

    @override
    async def currency(self) -> str:
        return self._currency

    @override
    async def price(self, dt: datetime) -> float | None:
        """Return price of electricity at dt."""

        def convert(dt: datetime) -> datetime:
            return dt.astimezone(dateutil.tz.gettz("CET")).replace(tzinfo=None)

        dt = await asyncio.to_thread(convert, dt)

        cached = self._price_cache.get(
            (dt.year, dt.month, dt.day)
        ) or await self._fetch_prices(dt)

        if cached is None:
            return None

        minutes = dt.hour * 60
        minutes += dt.minute
        idx = minutes // self.INTERVALS
        return cached[idx]

    async def _fetch_prices(self, dt: datetime) -> list[float] | None:
        date = f"{dt.year:04}-{dt.month:02}-{dt.day:02}"
        market = MARKETS[0] if self._internal_provider != "UK" else MARKETS[1]

        params = {
            "date": date,
            "market": market,
            "indexNames": self._internal_provider,
            "currency": await self.currency(),
            "resolutionInMinutes": str(self.INTERVALS),
        }

        async with ahttp.ClientSession() as session:
            try:
                async with session.get(
                    BASE_URL + "?" + urllib.parse.urlencode(params),
                    allow_redirects=False,
                ) as res:
                    res.raise_for_status()
                    data: dict = await res.json()
                    cached = self._cache_data(dt, data)
                    return cached

            except ahttp.ClientError:
                return None

    def _cache_data(self, dt: datetime, data: dict) -> list[float]:
        prices_list: list[dict[str, dict[str, float]]] = data["multiIndexEntries"]
        prices = [
            price["entryPerArea"][self._internal_provider] / 1000
            for price in prices_list
        ]  # / 1000 : MWh -> kWh
        self._price_cache[(dt.year, dt.month, dt.day)] = prices
        return prices
