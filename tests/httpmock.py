import urllib.parse
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from io import BytesIO
from os import urandom
from pathlib import Path
from typing import IO, Any, Self
from urllib.parse import urlsplit

from freezegun import freeze_time
from freezegun.api import (
    FrozenDateTimeFactory,
    StepTickTimeFactory,
    TickingDateTimeFactory,
)
from requests import ConnectTimeout, PreparedRequest, ReadTimeout, Response
from requests.adapters import BaseAdapter

urllib.parse.uses_relative.append("mock")
urllib.parse.uses_netloc.append("mock")


class MockAdapter(BaseAdapter):
    mock_initial: float
    mock_delay: float
    mock_size: int
    timefreeze: StepTickTimeFactory | TickingDateTimeFactory | FrozenDateTimeFactory
    root: Path
    prefix: str
    random: int | None

    def __init__(self, root: Path, prefix: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.root = root
        self.prefix = ("/" + prefix.lstrip("/")).rstrip("/") + "/"

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: None | float | tuple[None | float, None | float] = None,
        verify: bool | str = True,
        cert: None | bytes | str | tuple[bytes | str, bytes | str] = None,
        proxies: Mapping[str, str] | None = None,
    ) -> Response:
        conn_tmout, read_tmout = timeout if isinstance(timeout, tuple) else (timeout, timeout)

        if conn_tmout is None or conn_tmout >= self.mock_initial:
            self.timefreeze.tick(self.mock_initial)
        else:
            self.timefreeze.tick(conn_tmout)
            raise ConnectTimeout()

        resp = Response()

        assert request.url
        resp.url = request.url

        req_path = urlsplit(request.url).path
        assert isinstance(req_path, str)
        assert req_path.startswith(self.prefix)
        path = self.root / req_path.removeprefix(self.prefix)

        fp: IO[bytes]
        if self.random is not None:
            fp = BytesIO(urandom(self.random))
            resp.status_code = 200
            resp.reason = "OK"
        elif not path.is_file():
            fp = BytesIO(b"Not found")
            resp.status_code = 404
            resp.reason = "Not found"
        else:
            fp = path.open("rb")
            resp.status_code = 200
            resp.reason = "OK"

        resp.raw = StreamReader(self, fp, read_tmout)
        return resp

    @contextmanager
    def __call__(
        self,
        initial_delay: float,
        chunk_delay: float,
        chunk_size: int,
        random: int | None = None,
    ) -> Iterator[Self]:
        self.mock_initial = initial_delay
        self.mock_delay = chunk_delay
        self.mock_size = chunk_size
        self.random = random
        with freeze_time() as self.timefreeze:
            yield self


class StreamReader:
    _fp: None | IO[bytes]
    _timeout: None | float
    _mock: MockAdapter

    def __init__(self, mock: MockAdapter, fp: IO[bytes], timeout: None | float):
        self._fp = fp
        self._timeout = timeout
        self._mock = mock

    def read(self, size: int | None) -> bytes:
        if self._timeout is None or self._timeout >= self._mock.mock_delay:
            self._mock.timefreeze.tick(self._mock.mock_delay)
        else:
            self._mock.timefreeze.tick(self._timeout)
            raise ReadTimeout

        if size is None or size > self._mock.mock_size:
            size = self._mock.mock_size

        assert self._fp
        return self._fp.read(size)

    def close(self) -> None:
        assert self._fp
        self._fp.close()
        self._fp = None
