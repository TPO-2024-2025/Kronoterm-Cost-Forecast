"""Energy providers interface."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dateutil.tz import tzutc


class EnergyAPI(ABC):
    """Interface for energy providers."""

    INTERVALS: int = 15  # min

    @abstractmethod
    def __init__(self, provider: str) -> None:
        """Initialize energy price module with provided provider."""
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    @abstractmethod
    async def providers() -> list[str]:
        """
        Return providers that are provided with this module.

        This is used for modules that provide data for multiple regions/providers
        or to pack provider options into user options.

        User selected provider will be passed to __init__
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def price(self, dt: datetime) -> float | None:
        """
        Return price of electricity at dt.

        Datetime is in UTC timezone.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def currency(self) -> str:
        """Return currency of electricity price in ISO 4217."""
        raise NotImplementedError  # pragma: no cover

    async def unit(self) -> str:
        """Return unit of price: `${currency}/kWh`."""
        return f"{await self.currency()}/kWh"

    async def current_price(self) -> float | None:
        """Return current price of electricity."""
        return await self.price(datetime.now(tzutc()))

    async def prices(self, start: datetime) -> list[tuple[datetime, float | None]]:
        """
        Return series of future electricity prices (per interval defined in this class).

        If no timezone is specified, local will be used.
        """

        start = start.astimezone(tzutc())

        def dt(dt: datetime, times_interval: int = 0) -> datetime:
            d = datetime(
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                (dt.minute // EnergyAPI.INTERVALS) * EnergyAPI.INTERVALS,
                0,
                0,
                dt.tzinfo,
                fold=dt.fold,
            )
            return d + timedelta(minutes=EnergyAPI.INTERVALS * times_interval)

        return [(dt(start, i), await self.price(dt(start, i))) for i in range(4 * 8)]
