import socket

import pytest

from src.docxlint.models.document import (
    Block, DocumentSnapshot, Run,
)
from src.docxlint.services.dictionary_service import DictionaryService
from src.docxlint.services.language_checker import LanguageChecker
from src.docxlint.services.network_guard import network_guard
from src.docxlint.utils.errors import LocalModeNetworkBlocked


def test_network_blocked_during_check():
    svc = DictionaryService.from_data(words=("makan",))
    run = Run(run_index=0, text="makan", char_start=0, char_end=5,
              is_complex_run=False)
    block = Block(block_path="body/p[0]", block_type="paragraph",
                  part="document", text="makan", runs=[run])
    snapshot = DocumentSnapshot(
        snapshot_id="x", parts={"document": [block]}
    )

    with network_guard():
        LanguageChecker(svc).check(snapshot)
        with pytest.raises(LocalModeNetworkBlocked):
            socket.create_connection(("example.com", 80), timeout=0.1)