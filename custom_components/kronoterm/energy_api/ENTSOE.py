"""Data provider module for ENTSO-E."""

import asyncio
import dateutil
from .energy_api import EnergyAPI
from typing import override
from datetime import datetime, timedelta, date
import aiohttp
import xml.etree.ElementTree as ET
from lru import LRU
import os


def _get_entsoe_api_key() -> str | None:
    """Get ENTSO-E API key from environment variable."""
    return os.environ.get("ENTSOE_API_KEY")


PROVIDER_TO_DOMAIN: dict[str, str] = {
    "Ireland (ENTSOE)": "10Y1001A1001A59C",  # Ireland (IE)
    # "Switzerland (ENTSOE)": "10YCH-SWISSGRIDZ",  # Switzerland (CH)
    # "Austria (ENTSOE)": "10YAT-APG------L",  # Austria (AT)
    # "France (ENTSOE)": "10YFR-RTE------C",  # France (FR)
    # "Germany (ENTSOE)": "10Y1001A1001A82H",  # Germany (DE)
    # "Netherlands (ENTSOE)": "10YNL----------L",  # Netherlands (NL)
    # "Belgium (ENTSOE)": "10YBE----------2",  # Belgium (BE)
    # "Finland (ENTSOE)": "10YFI-1--------U",  # Finland (FI)
    # "Lithuania (ENTSOE)": "10YLT-1001A0008Q",  # Lithuania (LT)
    # "Latvia (ENTSOE)": "10YLV-1001A00074",  # Latvia (LV)
    # "Estonia (ENTSOE)": "10Y1001A1001A39I",  # Estonia (EE)
    # "Czech Republic (ENTSOE)": "10YCZ-CEPS-----N",  # Czech Republic (CZ)
    "Slovakia (ENTSOE)": "10YSK-SEPS-----K",  # Slovakia (SK)
    # "Poland (ENTSOE)": "10YPL-AREA-----S",  # Poland (PL)
    # "Hungary (ENTSOE)": "10YHU-MAVIR----U",  # Hungary (HU)
    "Italy - North (ENTSOE)": "10Y1001A1001A73I",  # Italy (IT)
    "Italy - Central North (ENTSOE)": "10Y1001A1001A73I",  # Italy (IT)
    "Italy - Central South (ENTSOE)": "10Y1001A1001A71M",  # Italy (IT)
    "Italy - South (ENTSOE)": "10Y1001A1001A788",  # Italy (IT)
    "Italy - Calabria (ENTSOE)": "10Y1001C--00096J",  # Italy (IT)
    "Italy - Sicily (ENTSOE)": "10Y1001A1001A75E",  # Italy (IT)
    # "Italy - SACODC (ENTSOE)": "10Y1001A1001A893",  # Italy (IT)
    # "Italy - SACOAC (ENTSOE)": "10Y1001A1001A885",  # Italy (IT)
    "Italy - Sardinia (ENTSOE)": "10Y1001A1001A74G",  # Italy (IT)
}


class ENTSOE(EnergyAPI):
    """ENTSOE data provider."""

    def __init__(self, provider: str) -> None:
        """Initialize the daily prices cache."""
        domain = PROVIDER_TO_DOMAIN.get(provider)
        if domain is None:
            raise ValueError(f"Unknown ENTSOE provider {provider}")
        self._domain = domain
        self._daily_prices_cache: LRU[date, dict[datetime, float]] = LRU(10)
        self._country = provider.split(" - ")[1]

    @staticmethod
    @override
    async def providers() -> list[str]:
        if _get_entsoe_api_key() is None:
            return []
        return list(PROVIDER_TO_DOMAIN.keys())

    @override
    async def currency(self) -> str:
        return "EUR"

    @override
    async def price(self, dt: datetime) -> float | None:
        """Return price for specific datetime (hourly resolution)."""

        # TODO: use UTC
        def convert(dt: datetime) -> datetime:
            return dt.astimezone(dateutil.tz.gettz("CET")).replace(tzinfo=None)

        dt = await asyncio.to_thread(convert, dt)

        hour_rounded = dt.replace(minute=0, second=0, microsecond=0)
        date_key = hour_rounded.date()
        if date_key in self._daily_prices_cache:
            return self._daily_prices_cache[date_key].get(hour_rounded)

        xml_data = await self._fetch_entsoe_data(hour_rounded)
        if not xml_data:
            return None

        prices_dict = self._parse_xml_response(xml_data)
        self._daily_prices_cache[date_key] = prices_dict
        return prices_dict.get(hour_rounded)

    async def _fetch_entsoe_data(self, dt: datetime) -> str:
        """Fetch XML data from ENTSO-E API."""
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        date_from = start.strftime("%Y%m%d%H%M")
        date_to = end.strftime("%Y%m%d%H%M")

        api_key = _get_entsoe_api_key()
        if api_key is None:
            return ""

        url = (
            f"https://web-api.tp.entsoe.eu/api?"
            f"documentType=A44"
            f"&out_Domain={self._domain}"
            f"&in_Domain={self._domain}"
            f"&periodStart={date_from}"
            f"&periodEnd={date_to}"
            f"&securityToken={api_key}"
        )

        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status != 200:
                return ""
            return await resp.text()

    def _parse_xml_response(self, xml_data: str) -> dict[datetime, float]:
        """Parse XML response from ENTSO-E API."""
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError:
            return {}

        ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
        prices_dict: dict[datetime, float] = {}

        for timeseries in root.findall(".//ns:TimeSeries", ns):
            self._process_timeseries(timeseries, ns, prices_dict)

        return prices_dict

    def _process_timeseries(
        self,
        timeseries: ET.Element,
        ns: dict[str, str],
        prices_dict: dict[datetime, float],
    ) -> None:
        """Process a single timeseries element from the XML."""
        period = timeseries.find("ns:Period", ns)
        if period is None:
            return

        time_interval = period.find("ns:timeInterval", ns)
        if time_interval is None:
            return

        series_start = self._parse_series_start(time_interval, ns)
        if series_start is None:
            return

        resolution = period.find("ns:resolution", ns)
        if resolution is None:
            return

        if resolution.text != "PT60M" and self._country != "Italy":
            return

        for point in period.findall("ns:Point", ns):
            self._process_point(point, ns, series_start, prices_dict)

    def _parse_series_start(
        self, time_interval: ET.Element, ns: dict[str, str]
    ) -> datetime | None:
        """Parse the series start time from XML."""
        start_element = time_interval.find("ns:start", ns)
        if start_element is None or start_element.text is None:
            return None

        try:
            series_start = datetime.strptime(start_element.text, "%Y-%m-%dT%H:%MZ")
            # Convert from UTC to CET
            return (series_start + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except ValueError:
            return None

    def _process_point(
        self,
        point: ET.Element,
        ns: dict[str, str],
        series_start: datetime,
        prices_dict: dict[datetime, float],
    ) -> None:
        """Process a single point element from the XML."""
        position_element = point.find("ns:position", ns)
        price_amount_element = point.find("ns:price.amount", ns)

        if position_element is None or position_element.text is None:
            return
        if price_amount_element is None or price_amount_element.text is None:
            return

        try:
            position = int(position_element.text)
            price_amount = float(price_amount_element.text)
        except (ValueError, TypeError):
            return

        if self._country == "Italy":
            position = position // 4 + 1

        point_time = series_start + timedelta(hours=position - 1)
        prices_dict[point_time] = round(price_amount / 1000, 5)  # Convert to EUR/kWh
