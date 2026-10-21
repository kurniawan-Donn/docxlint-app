import socket
import threading

import pytest

from src.docxlint.services.network_guard import network_guard
from src.docxlint.utils.errors import LocalModeNetworkBlocked


def test_blocked_create_connection():
    with network_guard():
        with pytest.raises(LocalModeNetworkBlocked):
            socket.create_connection(("example.com", 80), timeout=0.1)


def test_blocked_socket_connect():
    with network_guard():
        s = socket.socket()
        try:
            with pytest.raises(LocalModeNetworkBlocked):
                s.connect(("example.com", 80))
        finally:
            s.close()


def test_localhost_allowed():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def accept_once():
        try:
            conn, _ = server.accept()
            conn.close()
        except OSError:
            pass

    t = threading.Thread(target=accept_once, daemon=True)
    t.start()
    try:
        with network_guard():
            s = socket.create_connection(("127.0.0.1", port), timeout=2)
            s.close()
    finally:
        server.close()


def test_guard_restores_after_exit():
    original = socket.create_connection
    with network_guard():
        assert socket.create_connection is not original
    assert socket.create_connection is original