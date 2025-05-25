"""Data provider module for GEN-I."""

from .energy_api import EnergyAPI
from typing import override
from datetime import datetime
import holidays
import dateutil
import asyncio

ENO = "GENI (Enotarifno)"
DVO = "GENI (Dvotarifno)"


class GENI(EnergyAPI):
    """EnergyAPI for GEN-I."""

    enotna_tarifa: bool

    @override
    def __init__(self, provider: str):
        if provider == ENO:
            self.enotna_tarifa = True
        else:
            self.enotna_tarifa = False

    @override
    @staticmethod
    async def providers() -> list[str]:
        return [ENO, DVO]

    @override
    async def currency(self) -> str:
        return "EUR"

    @override
    async def price(self, dt: datetime) -> float | None:
        if self.enotna_tarifa:
            return ET_PRICE
        return VT_PRICE if await visoka_tarifa(dt) else MT_PRICE


si_holidays = holidays.country_holidays("SI")


async def visoka_tarifa(dt: datetime) -> bool:  # noqa: D103
    def convert(dt: datetime) -> datetime:
        return dt.astimezone(dateutil.tz.gettz("Europe/Ljubljana"))

    dt_slo = await asyncio.to_thread(convert, dt)
    return 6 <= dt_slo.hour < 22 and si_holidays.is_working_day(dt_slo.date())


# TODO: actual API call
VT_PRICE = 0.14628
MT_PRICE = 0.11944
ET_PRICE = 0.13286
