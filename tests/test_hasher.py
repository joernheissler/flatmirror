from hashlib import sha256
from pathlib import Path
from random import randrange
from tempfile import NamedTemporaryFile

from . import flatmirror
from .fileinfos import fileinfo_empty, fileinfo_prng


class PseudoRandom:
    """
    Class to generate reproducible pseudo random bytes.
    """

    buf: bytearray
    state: int

    def __init__(self) -> None:
        self.buf = bytearray()
        self.state = 0

    def read(self, count: int) -> bytearray:
        result = self.buf
        while len(result) < count:
            dgst = sha256(self.state.to_bytes(8, "big")).digest()
            result.extend(dgst)
            self.state += 1

        self.buf = result[count:]
        del result[count:]

        return result


def test_empty(fileinfo_empty: flatmirror.FileInfo) -> None:
    hasher = flatmirror.Hasher()
    info = hasher.finalize("empty")

    assert info == fileinfo_empty


def test_prng(fileinfo_prng: flatmirror.FileInfo) -> None:
    hasher = flatmirror.Hasher()

    prng = PseudoRandom()
    while left := (1 << 20) - hasher.size:
        hasher.update(prng.read(randrange(left) + 1))
    info = hasher.finalize("prng")

    assert info == fileinfo_prng


def test_file(fileinfo_prng: flatmirror.FileInfo) -> None:
    with NamedTemporaryFile() as tmp:
        prng = PseudoRandom()
        tmp.write(prng.read(1 << 20))
        tmp.flush()
        info = flatmirror.Hasher.hash_file(Path(tmp.name), "prng")

    assert info == fileinfo_prng
