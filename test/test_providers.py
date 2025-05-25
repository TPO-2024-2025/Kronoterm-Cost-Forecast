"""Test providers."""

from datetime import datetime
from unittest.mock import patch

import pytest
from custom_components.kronoterm.energy_api import (
    GENI,
    ElektroLJ,
    ENTSOE,
    NordPool,
    EnergyCharts,
    EnergyAPIFactory,
)


def assert_valid_price(price: float | None) -> None:  # noqa:D103
    assert price is not None
    assert isinstance(price, float)


async def test_providers_dict() -> None:
    """Test uniqueness all all providers."""
    all = await EnergyAPIFactory.providers()
    assert len(all) > 0


@patch("custom_components.kronoterm.energy_api.ALL_MODULES", [GENI, GENI])
@patch("custom_components.kronoterm.energy_api.EnergyAPIFactory._all_providers", {})
async def test_duplicated_providers() -> None:
    """Test uniqueness all all providers."""
    with pytest.raises(Exception):
        await EnergyAPIFactory.providers()


async def test_geni() -> None:  # noqa:D103
    for provider in await GENI.providers():
        geni = GENI(provider)
        price = await geni.current_price()
        assert_valid_price(price)
        prices = await geni.prices(datetime.now())
        for _, price in prices:
            assert_valid_price(price)
        unit = await geni.unit()
        assert unit == "EUR/kWh"


async def test_elektro_lj() -> None:  # noqa:D103
    for provider in await ElektroLJ.providers():
        elektro = ElektroLJ(provider)
        price = await elektro.current_price()
        assert_valid_price(price)
        prices = await elektro.prices(datetime.now())
        for _, price in prices:
            assert_valid_price(price)
        unit = await elektro.unit()
        assert unit == "EUR/kWh"


@pytest.mark.xfail(strict=False)
@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_entsoe() -> None:  # noqa:D103
    for provider in await ENTSOE.providers():
        entsoe = ENTSOE(provider)
        price = await entsoe.price(datetime.now())
        assert_valid_price(price)
        prices = await entsoe.prices(datetime.now())
        for _, price in prices:
            assert_valid_price(price)
        unit = await entsoe.unit()
        assert unit == "EUR/kWh"


@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_nord_pool() -> None:  # noqa:D103
    for provider in await NordPool.providers():
        nord_pool = NordPool(provider)
        price = await nord_pool.current_price()
        assert_valid_price(price)
        prices = await nord_pool.prices(datetime.now())
        for _, price in prices:
            assert_valid_price(price)
        unit = await nord_pool.unit()

        if "PLN" in provider:
            assert unit == "PLN/kWh"
        elif "DKK" in provider:
            assert unit == "DKK/kWh"
        elif "NOK" in provider:
            assert unit == "NOK/kWh"
        elif "SEK" in provider:
            assert unit == "SEK/kWh"
        elif "United Kingdom" in provider:
            assert unit == "GBP/kWh"
        else:
            assert unit == "EUR/kWh"


@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_swiss() -> None:  # noqa:D103
    for provider in await EnergyCharts.providers():
        sui = EnergyCharts(provider)

        price = await sui.current_price()
        assert_valid_price(price)

        prices = await sui.prices(datetime.now())
        for _, p in prices:
            assert_valid_price(p)

        unit = await sui.unit()
        assert unit == "EUR/kWh"
