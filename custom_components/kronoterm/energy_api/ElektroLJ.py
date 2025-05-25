"""Data provider module for Elektro Ljubljana."""

from custom_components.kronoterm.energy_api.GENI import visoka_tarifa
from .energy_api import EnergyAPI
from typing import override
from datetime import datetime

ENO = "Elektro Ljubljana (Enotarifno)"
DVO = "Elektro Ljubljana (Dvotarifno)"


class ElektroLJ(EnergyAPI):
    """EnergyAPI for Elektro Ljubljana."""

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


# TODO: actual API call: https://www.elektro-energija.si/za-dom/dokumenti-in-ceniki
VT_PRICE = 0.15238
MT_PRICE = 0.12554
ET_PRICE = 0.13896
