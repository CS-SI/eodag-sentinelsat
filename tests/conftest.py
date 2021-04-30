import os
import tempfile
from pathlib import Path

import pytest
from eodag import setup_logging


@pytest.fixture(scope="session", autouse=True)
def download_dir():
    test_download_dir = Path(tempfile.gettempdir()) / "eodag_tests"
    if not test_download_dir.exists():
        os.makedirs(test_download_dir)
    yield test_download_dir


@pytest.fixture
def logging_info():
    setup_logging(1)
    yield
    setup_logging(0)


@pytest.fixture
def logging_debug():
    setup_logging(3)
    yield
    setup_logging(0)
