from pathlib import Path

import pytest

from . import flatmirror

"""
Note: tests/data/gpg.key is included in the repository deliberately. Its sole purpose is to
create the signatures for the tests and any member of the public is welcome to do so.
"""


@pytest.fixture
def datadir() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture
def gpg_checker(datadir: Path) -> flatmirror.GpgChecker:
    return flatmirror.GpgChecker(datadir / "gpg.pub")


def test_detached(gpg_checker: flatmirror.GpgChecker, datadir: Path) -> None:
    gpg_checker.check_detached(datadir / "gpg-test.txt.gpg", datadir / "gpg-test.txt")

    with pytest.raises(flatmirror.SignatureError):
        gpg_checker.check_detached(datadir / "gpg-bad.txt.gpg", datadir / "gpg-test.txt")


def test_inline(gpg_checker: flatmirror.GpgChecker, datadir: Path) -> None:
    value = gpg_checker.check_inline(datadir / "gpg-test.txt.asc")
    assert value == (datadir / "gpg-test.txt").read_text()

    with pytest.raises(flatmirror.SignatureError):
        gpg_checker.check_inline(datadir / "gpg-bad.txt.asc")
