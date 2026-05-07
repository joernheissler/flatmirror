import logging
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from . import flatmirror
from .httpmock import MockAdapter

DATA_PATH = Path(__file__).parent / "data"


@pytest.fixture
def mock() -> Iterator[MockAdapter]:
    yield MockAdapter(DATA_PATH / "http", "files")


def test_flatmirror0(mock: MockAdapter) -> None:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        # fmt: off
        args = [
            "--gpgkey", str(DATA_PATH / "gpg/gpg.pub"),
            "--url", "mock://localhost/files",
            "--path", "repo0/",
            "--cache", str(tmp / "cache"),
            "--dest", str(tmp / "dest"),
            "--arch", "z80",
            "--arch", "all",
            "--timeout", "30",
            "--minspeed", "1",
            "--exclude", "bogus",
            "--include", ".*u",
        ]
        # fmt: on

        logging.basicConfig(level=logging.INFO)
        fm = flatmirror.FlatMirror(args)
        fm.fetcher.http.mount("mock://", mock)
        with mock(1, 1, 4096):
            fm.run()


def test_flatmirror1(mock: MockAdapter) -> None:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        # fmt: off
        args = [
            "--gpgkey", str(DATA_PATH / "gpg/gpg.pub"),
            "--url", "mock://localhost/files",
            "--path", "repo1/",
            "--cache", str(tmp / "cache"),
            "--dest", str(tmp / "dest"),
            "--arch", "z80",
            "--arch", "all",
        ]
        # fmt: on

        logging.basicConfig(level=logging.INFO)
        fm = flatmirror.FlatMirror(args)
        fm.fetcher.http.mount("mock://", mock)
        with mock(1, 1, 4096):
            fm.run()


def test_flatmirror2(mock: MockAdapter) -> None:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        # fmt: off
        args = [
            "--gpgkey", str(DATA_PATH / "gpg/gpg.pub"),
            "--url", "mock://localhost/files",
            "--path", "repo2/",
            "--cache", str(tmp / "cache"),
            "--dest", str(tmp / "dest"),
            "--arch", "z80",
            "--arch", "all",
        ]
        # fmt: on

        logging.basicConfig(level=logging.INFO)
        fm = flatmirror.FlatMirror(args)
        fm.fetcher.http.mount("mock://", mock)
        with mock(1, 1, 4096):
            with pytest.raises(ValueError):
                fm.run()


def test_flatmirror3(mock: MockAdapter) -> None:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        # fmt: off
        args = [
            "--gpgkey", str(DATA_PATH / "gpg/gpg.pub"),
            "--url", "mock://localhost/files",
            "--path", "repo3/",
            "--cache", str(tmp / "cache"),
            "--dest", str(tmp / "dest"),
            "--arch", "z80",
            "--arch", "all",
        ]
        # fmt: on

        logging.basicConfig(level=logging.INFO)
        fm = flatmirror.FlatMirror(args)
        fm.fetcher.http.mount("mock://", mock)
        with mock(1, 1, 4096):
            with pytest.raises(flatmirror.SignatureError):
                fm.run()


def test_flatmirror4(mock: MockAdapter) -> None:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        # fmt: off
        args = [
            "--gpgkey", str(DATA_PATH / "gpg/gpg.pub"),
            "--url", "mock://localhost/files",
            "--path", "repo4/",
            "--cache", str(tmp / "cache"),
            "--dest", str(tmp / "dest"),
            "--arch", "z80",
            "--arch", "all",
        ]
        # fmt: on

        logging.basicConfig(level=logging.INFO)
        fm = flatmirror.FlatMirror(args)
        fm.fetcher.http.mount("mock://", mock)
        with mock(1, 1, 4096):
            with pytest.raises(flatmirror.SignatureError):
                fm.run()
