import pytest

from . import flatmirror


def test_fileinfo_partial(
    fileinfo_prng: flatmirror.FileInfo, fileinfo_partial: flatmirror.FileInfo
) -> None:
    assert fileinfo_prng.matches(fileinfo_partial)

    with pytest.raises(KeyError):
        fileinfo_partial.matches(fileinfo_prng)


def test_fileinfo_bad(
    fileinfo_prng: flatmirror.FileInfo, fileinfo_bad: flatmirror.FileInfo
) -> None:

    assert not fileinfo_prng.matches(fileinfo_bad)
