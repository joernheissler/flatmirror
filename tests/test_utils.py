from os import urandom
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin

import pytest

from . import flatmirror


def test_path_utils() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "srcfile"
        dst = tmp / "dstfile"

        assert flatmirror.path_inode(src) is None

        sdata = urandom(3_456_789)
        src.write_bytes(sdata)
        flatmirror.path_copy(src, dst)
        ddata = dst.read_bytes()
        assert sdata == ddata

        assert (src_inode := flatmirror.path_inode(src))
        assert (dst_inode := flatmirror.path_inode(dst))
        assert src_inode != dst_inode


BASE_URL = "https://example.net/path/"


def test_url_subpath_good() -> None:
    assert flatmirror.url_subpath(urljoin(BASE_URL, "foo/bar"), BASE_URL) == "foo/bar"

    offsite_url = urljoin(BASE_URL, "//evil.corp/somewhere")
    with pytest.raises(ValueError):
        flatmirror.url_subpath(offsite_url, BASE_URL)

    with pytest.raises(ValueError):
        url = urljoin(BASE_URL, "../foo")
        flatmirror.url_subpath(url, BASE_URL)
