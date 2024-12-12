from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

import pytest
from requests import ConnectTimeout, HTTPError, ReadTimeout

from . import flatmirror
from .httpmock import MockAdapter

DATA_PATH = Path(__file__).parent / "data"


@pytest.fixture
def mock() -> Iterator[MockAdapter]:
    yield MockAdapter(DATA_PATH / "http", "files")


@pytest.fixture
def fetcher(mock: MockAdapter) -> Iterator[flatmirror.Fetcher]:
    with TemporaryDirectory() as path:
        tmp = Path(path)

        config = flatmirror.Config(
            gpgkey=DATA_PATH / "gpg" / "gpg.pub",
            url="mock://localhost/files",
            path="/repo",
            cache=tmp / "cache",
            dest=tmp / "dest",
            arch={"all", "z80"},
            min_speed=1,
            timeout=30,
            exclude=[],
            include=[],
        )

        with flatmirror.FileCache(config.cache) as cache:
            fetcher = flatmirror.Fetcher(config, cache)
            fetcher.http.mount("mock://", mock)
            yield fetcher


def test_resolve(fetcher: flatmirror.Fetcher) -> None:
    url, dest = fetcher._resolve(("foo/", "bar"))
    assert url == "mock://localhost/files/foo/bar"
    assert str(dest).endswith("/dest/foo/bar")


def test_download(mock: MockAdapter, fetcher: flatmirror.Fetcher) -> None:
    with mock(3, 1, 4096, 12345):
        url, dest = fetcher._resolve(("download0",))
        with pytest.raises(ValueError):
            fetcher._download(url, dest, 9876)

    with mock(3, 5, 4096, 100_000):
        url, dest = fetcher._resolve(("download1",))
        with pytest.raises(TimeoutError):
            fetcher._download(url, dest, 100_000)

    with mock(3, 2, 67890, 1_000_000):
        url, dest = fetcher._resolve(("download2",))
        fetcher._download(url, dest, 1_000_000)

    with mock(50, 1, 4096, 1):
        url, dest = fetcher._resolve(("download3",))
        with pytest.raises(ConnectTimeout):
            fetcher._download(url, dest, 1)

    with mock(5, 50, 4096, 1):
        url, dest = fetcher._resolve(("download4",))
        with pytest.raises(ReadTimeout):
            fetcher._download(url, dest, 1)


def test_fetch_uncached(mock: MockAdapter, fetcher: flatmirror.Fetcher) -> None:
    with mock(3, 1, 4096):
        fetcher.fetch_uncached("README", max_size=5000)
        with pytest.raises(HTTPError):
            fetcher.fetch_uncached("missing", max_size=123)


def test_fetch_cached(mock: MockAdapter, fetcher: flatmirror.Fetcher) -> None:
    digests = {
        "md5": bytes.fromhex("ae272b9712bed73add345859b4fe5d61"),
        "sha256": bytes.fromhex(
            "63304d707a7c1761e3ace8e6309e51225b9a42b18436b4c3968cbe86c0373da2"
        ),
    }
    with mock(1, 1, 4096):
        with pytest.raises(ValueError):
            fetcher.fetch_cached({"md5": digests["md5"]}, 22, "deb/dummy.deb")

        fetcher.fetch_cached(digests, 22, "deb/dummy.deb")

        # Download again, from cache.
        fetcher.fetch_cached(digests, 22, "deb/dummy.deb")

        with pytest.raises(ValueError):
            fetcher.fetch_cached({**digests, "sha1": bytes(20)}, 22, "deb/dummy.deb")
