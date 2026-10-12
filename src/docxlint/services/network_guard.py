"""Network guard untuk mode lokal (DECISION-010).

Memblokir koneksi keluar kecuali localhost/127.0.0.1 selama pemrosesan dokumen.
Tidak mencatat isi dokumen.
"""

import socket
from contextlib import contextmanager
from typing import Iterator, Tuple

from ..utils.errors import LocalModeNetworkBlocked

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}

_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection


def _is_localhost(address: object) -> bool:
    if isinstance(address, tuple) and address:
        host = address[0]
        return host in _LOCAL_HOSTS
    return False


def _blocked_connect(self, address):  # type: ignore[no-untyped-def]
    if _is_localhost(address):
        return _ORIGINAL_CONNECT(self, address)
    raise LocalModeNetworkBlocked(
        f"Koneksi keluar diblokir di mode lokal: {address!r}"
    )


def _blocked_create_connection(address, *args, **kwargs):  # type: ignore[no-untyped-def]
    if _is_localhost(address):
        return _ORIGINAL_CREATE_CONNECTION(address, *args, **kwargs)
    raise LocalModeNetworkBlocked(
        f"Koneksi keluar diblokir di mode lokal: {address!r}"
    )


@contextmanager
def network_guard() -> Iterator[None]:
    """Aktifkan network guard. Pulihkan kondisi semula di finally."""

    socket.socket.connect = _blocked_connect  # type: ignore[assignment]
    socket.create_connection = _blocked_create_connection  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = _ORIGINAL_CONNECT  # type: ignore[assignment]
        socket.create_connection = _ORIGINAL_CREATE_CONNECTION  # type: ignore[assignment]


__all__ = ["network_guard", "LocalModeNetworkBlocked", "Tuple"]