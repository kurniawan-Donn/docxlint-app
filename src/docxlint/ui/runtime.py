"""Deteksi mode jalan aplikasi (lokal vs demo publik).

Di Streamlit Community Cloud, secret tingkat atas juga tersedia sebagai
environment variable. Set `DOCXLINT_PUBLIC_DEMO = "1"` di Secrets agar UI
menampilkan peringatan dokumen non-sensitif.
"""

import os
from typing import Mapping, Optional

PUBLIC_DEMO_ENV = "DOCXLINT_PUBLIC_DEMO"
_TRUTHY = {"1", "true", "yes", "ya", "on"}


def is_public_demo(environ: Optional[Mapping[str, str]] = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(PUBLIC_DEMO_ENV, "")).strip().lower() in _TRUTHY


__all__ = ["PUBLIC_DEMO_ENV", "is_public_demo"]
