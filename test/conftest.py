"""Fixtures for testing."""

from typing import Any
import pytest
import pytest_socket  # type: ignore


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
    """Enable custom integrations."""
    return


@pytest.fixture(autouse=True)
def allow_network() -> None:  # noqa: D103
    pytest_socket.socket_allow_hosts(["*"], True)
    pytest_socket.enable_socket()
    pytest_socket._remove_restrictions()
