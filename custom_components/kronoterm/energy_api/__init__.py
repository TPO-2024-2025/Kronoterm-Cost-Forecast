"""Energy providers."""

from .energy_api import EnergyAPI
from .GENI import GENI
from .ElektroLJ import ElektroLJ
from .ENTSOE import ENTSOE
from .NordPool import NordPool
from .EnergyCharts import EnergyCharts

__all__ = ["EnergyAPI", "GENI", "ElektroLJ", "ENTSOE", "NordPool", "EnergyCharts"]
ALL_MODULES: list[type[EnergyAPI]] = [GENI, ElektroLJ, ENTSOE, NordPool, EnergyCharts]


class EnergyAPIFactory:
    """Factory for creating EnergyAPI instances."""

    _all_providers: dict[str, type[EnergyAPI]] = {}

    @staticmethod
    async def _get_or_init_all_providers() -> dict[str, type[EnergyAPI]]:
        """Return all providers available."""
        if not EnergyAPIFactory._all_providers:
            for module in ALL_MODULES:
                providers = await module.providers()
                for provider in providers:
                    if provider in EnergyAPIFactory._all_providers:
                        raise Exception(f"Provider {provider} is duplicated")
                    EnergyAPIFactory._all_providers[provider] = module
        return EnergyAPIFactory._all_providers

    @staticmethod
    async def providers() -> list[str]:
        """Return all providers available."""
        all_providers = await EnergyAPIFactory._get_or_init_all_providers()
        return list(all_providers.keys())

    @staticmethod
    async def create(provider: str) -> EnergyAPI:
        """Create an instance of EnergyAPI based on the provider."""
        all_providers = await EnergyAPIFactory._get_or_init_all_providers()
        if provider not in all_providers:
            raise ValueError(f"Unknown provider: {provider}")
        return all_providers[provider](provider)
