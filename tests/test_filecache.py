import hashlib
from collections.abc import Iterable
from os import urandom
from pathlib import Path
from tempfile import TemporaryDirectory

import cbor2
import pytest

from . import flatmirror


@pytest.fixture()
def cachedir() -> Iterable[Path]:
    with TemporaryDirectory() as path:
        yield Path(path)


def test_noop(cachedir: Path) -> None:
    with flatmirror.FileCache(cachedir / "cache") as cache:
        pass


def test_badversion(cachedir: Path) -> None:
    cache = flatmirror.FileCache(cachedir / "cache")
    cache._index_path.write_bytes(cbor2.dumps([1, None]))
    with pytest.raises(ValueError):
        cache.__enter__()


def test_store_retrieve(cachedir: Path) -> None:
    """
    The "usual" case. Try to retrieve a file. It doesn't exist, so download and store it.
    Later, retrieve it again.

    Afterwards an error happened elsewhere and the file is retrieved yet again, although it was
    already retrieved successfully.

    And lastly, assume that two different processes tried to fetch the same file. First failed
    and left behind a broken file. Then the other process succeeded. Now the first process again
    tries to retrieve the file from the cache. This works, but the broken file has to be
    removed.
    """
    data = urandom(12345)
    info = flatmirror.FileInfo(
        len(data),
        {
            # Insecure md5 must come first to test code path.
            "md5": hashlib.md5(data).digest(),
            "sha256": hashlib.sha256(data).digest(),
        },
        "URL",
    )

    dest = cachedir / "dest"

    with flatmirror.FileCache(cachedir / "cache") as cache:
        # File is not in cache, so this should fail.
        assert not cache.retrieve(info, dest)

        # "Download" the file
        dest.write_bytes(data)
        full_info = flatmirror.Hasher.hash_file(dest, info.url)
        stat0 = dest.stat()

        # Add file to cache
        cache.addfile(full_info, dest)

    # Remove original filename from disk; file should still be in cache.
    dest.unlink()

    with flatmirror.FileCache(cachedir / "cache") as cache:
        # This time retrieval should work.
        info2 = cache.retrieve(info, dest)
        assert info2 == full_info

    # Verify that retrieved file is as expected.
    stat1 = dest.stat()
    assert stat1.st_ino == stat0.st_ino
    assert stat1.st_size == len(data)
    assert dest.read_bytes() == data

    # Retrieve the file again, this should be a noop.
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    stat2 = dest.stat()
    assert stat1 == stat2

    # Prepare a broken file.
    dest.unlink()
    dest.write_text("Broken")

    # Retrieve the file again, this should remove the broken file and create a link from cache.
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    stat2 = dest.stat()
    assert stat1 == stat2


def test_file_gone(cachedir: Path) -> None:
    """
    File was stored into the cache, but later the file was removed from the filesystem. 🤬
    When trying to retrieve the file later, it's found in the index, but missing on disk.
    Means it needs to be downloaded again.
    """
    data = urandom(12345)
    dest = cachedir / "dest"
    dest.write_bytes(data)
    info = flatmirror.Hasher.hash_file(dest, "url")

    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(info, dest)
        path = cache._cache_path(info)

    path.unlink()
    dest.unlink()

    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert not cache.retrieve(info, dest)


def test_index_gone(cachedir: Path) -> None:
    """
    A file exists in the cache, but someone deleted the index. 🤬
    If will be retrieved from the cache nonetheless, but digests
    need to be recomputed.
    """
    data = urandom(12345)
    dest = cachedir / "dest"
    dest.write_bytes(data)
    stat0 = dest.stat()
    full_info = flatmirror.Hasher.hash_file(dest, "url")
    info = flatmirror.FileInfo(len(data), {"sha256": full_info.digests["sha256"]}, "here")

    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(full_info, dest)

    # Remove the index.
    cache._index_path.unlink()

    # And the added file.
    dest.unlink()

    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    # Verify that retrieved file is as expected.
    stat1 = dest.stat()
    assert stat1.st_ino == stat0.st_ino
    assert stat1.st_size == len(data)
    assert dest.read_bytes() == data

    # Remove the index, not the destination.
    cache._index_path.unlink()

    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    # Verify that retrieved file is as expected.
    stat1 = dest.stat()
    assert stat1.st_ino == stat0.st_ino
    assert stat1.st_size == len(data)
    assert dest.read_bytes() == data

    # Remove the index.
    cache._index_path.unlink()

    # And the added file.
    dest.unlink()
    dest.write_text("foobar")

    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    # Verify that retrieved file is as expected.
    stat1 = dest.stat()
    assert stat1.st_ino == stat0.st_ino
    assert stat1.st_size == len(data)
    assert dest.read_bytes() == data


def test_url_missing(cachedir: Path) -> None:
    """
    The index was deleted and the repair job found a file in the cache, but its original URL is unknown.
    Later, a normal retrieval takes place with a known URL.
    """
    data = urandom(12345)
    dest = cachedir / "dest"
    dest.write_bytes(data)
    real_info = flatmirror.Hasher.hash_file(dest, "url")

    # Add file to cache.
    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(real_info, dest)

    # Remove the index.
    cache._index_path.unlink()

    # Add file without URL to cache. This is what the repair job would do.
    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache._add_index(flatmirror.FileInfo(real_info.size, real_info.digests, ""))

    # And now fix the URL during a retrieval.
    info = flatmirror.FileInfo(len(data), {"sha256": real_info.digests["sha256"]}, "url")
    dest.unlink()
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)


def test_index_gone_nonprimary_hashfunc(cachedir: Path) -> None:
    """
    A file exists in the cache, but someone deleted the index. 🤬
    Later we want to retrieve the file, but we don't know the primary digest.
    This is unfortunate because retrieval will fail even though the file is cached.
    We download the file and store it in the cache as usual.

    The cache should now find the cached file and replace the just-downloaded
    file from the cache.
    """
    # Add a file to the cache
    data = urandom(12345)
    orig = cachedir / "orig"
    orig.write_bytes(data)
    ostat = orig.stat()
    orig_info = flatmirror.Hasher.hash_file(orig, "orig")
    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(orig_info, orig)

    # Remove the index.
    cache._index_path.unlink()

    # Try to fetch file with nonprimary digest.
    np_info = flatmirror.FileInfo(
        len(data),
        {
            "md5": orig_info.digests["md5"],
            "sha512": orig_info.digests["sha512"],
        },
        "somelocation",
    )
    dest = cachedir / "dest"
    with flatmirror.FileCache(cachedir / "cache") as cache:
        # File is in cache but won't be found.
        assert not cache.retrieve(np_info, dest)
        assert not dest.exists()

        dest.write_bytes(data)
        # This is a different file.
        assert dest.stat().st_ino != ostat.st_ino

        # Add the file to the cache. Again.
        cache.addfile(orig_info, dest)

    # Check that the file is a link of the original file.
    dstat = dest.stat()
    assert ostat.st_ino == dstat.st_ino
    assert ostat.st_size == len(data)
    assert dest.read_bytes() == data


def test_broken_file_in_cache(cachedir: Path) -> None:
    """
    A file exists in the cache, but someone broke it. 🤬
    Even worse, because hardlinks are used, all links of the file are broken too!

    Later we want to retrieve the file, but luckily the file size is broken too, so we notice
    the problem. We download the file again and store it in the cache as usual.

    This should repair the broken file (and all its links) and replace the just-downloaded file
    from the cache.

    Soon after, the file is broken again. 🤬🤬
    Download it again, but because the files are linked together, the download repairs the
    cached file too.
    """
    # Add a file to the cache
    data = urandom(12345)
    orig = cachedir / "orig"
    orig.write_bytes(data)
    ostat = orig.stat()
    orig_info = flatmirror.Hasher.hash_file(orig, "orig")
    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(orig_info, orig)

    # Break the file
    orig.write_text("Whoopsy!")

    # Try to fetch file.
    info = flatmirror.FileInfo(
        len(data),
        {
            "sha256": orig_info.digests["sha256"],
        },
        "somelocation",
    )
    dest = cachedir / "dest"
    with flatmirror.FileCache(cachedir / "cache") as cache:
        # File in cache is broken, so it can't be retrieved.
        assert not cache.retrieve(info, dest)
        assert not dest.exists()

        # Download the file.
        dest.write_bytes(data)

        # This is a different file.
        assert dest.stat().st_ino != ostat.st_ino

        # Add the file to the cache. Again.
        cache.addfile(orig_info, dest)

    # Check that the file is a link of the original file.
    dstat = dest.stat()
    assert ostat.st_ino == dstat.st_ino
    assert ostat.st_size == len(data)
    assert dest.read_bytes() == data
    assert orig.read_bytes() == data

    # Break the file. Again.
    orig.write_text("Whoopsy!")

    with flatmirror.FileCache(cachedir / "cache") as cache:
        # File in cache is broken, so it can't be retrieved. But it won't remove dest either.
        assert dest.exists()
        assert not cache.retrieve(info, dest)
        assert dest.exists()

        # Download the file.
        dest.write_bytes(data)

        # Which is still the same file.
        assert dest.stat().st_ino == ostat.st_ino

        # Add the file to the cache. Again!
        cache.addfile(orig_info, dest)

    # Check that the file is a link of the original file.
    dstat = dest.stat()
    assert ostat.st_ino == dstat.st_ino
    assert ostat.st_size == len(data)
    assert dest.read_bytes() == data
    assert orig.read_bytes() == data


def test_file_in_dest(cachedir: Path) -> None:
    """
    A file was downloaded correctly before, but while adding it to the cache something failed.
    On a subsequent run, the file already exists, so there is no need to download it again. It
    will be stored into the cache and index.

    Next, the index is deleted and the retrieval is tried again with a non-primary digest only.

    And lastly, index is removed again and the cached file is broken (or not) while a whole new
    file is in dest.
    """
    data = urandom(12345)
    dest = cachedir / "dest"
    dest.write_bytes(data)
    info = flatmirror.Hasher.hash_file(dest, "url")

    # Retrieval will work.
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(info, dest)

    # Remove the index.
    cache._index_path.unlink()

    # File exists in the storage. Now try to retrieve it without knowing the primary digest.
    np_info = flatmirror.FileInfo(
        len(data),
        {
            "md5": info.digests["md5"],
            "sha512": info.digests["sha512"],
        },
        "url",
    )

    # Retrieve without known primary digest
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(np_info, dest)

    # Remove the index.
    cache._index_path.unlink()

    # Break the cached file, add a whole file to dest again.
    dest.write_text("broken")
    dest.unlink()
    dest.write_bytes(data)

    # Retrieve without known primary digest
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(np_info, dest)

    # Remove the index.
    cache._index_path.unlink()

    # DO NOT break the cached file, but add a whole file to dest again.
    dest.unlink()
    dest.write_bytes(data)

    # Retrieve without known primary digest
    with flatmirror.FileCache(cachedir / "cache") as cache:
        assert cache.retrieve(np_info, dest)


def test_hash_collision(cachedir: Path) -> None:
    """
    Check the behaviour in case of a VERY unlikely hash collision in the primary digest.
    """
    file0 = cachedir / "file0"
    file0.write_bytes(urandom(12345))
    info0 = flatmirror.Hasher.hash_file(file0, "file0")

    file1 = cachedir / "file1"
    file1.write_bytes(urandom(6789))
    info1 = flatmirror.FileInfo(6789, info0.digests.copy(), "file1")
    # reverse the md5 sum.
    info1.digests["md5"] = bytes(255 - i for i in info1.digests["md5"])

    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(info0, file0)

        # The code assumes that info1 is correct. In fact it might be, although astronomically unlikely.
        with pytest.raises(SystemError):
            cache.addfile(info1, file1)


def test_wrong_secondary_digest(cachedir: Path) -> None:
    """
    A file was correctly stored into the cache.
    Later, a retrieval is tried, but a non-secure digest that was requested
    mismatches the cached file.

    This might indicate a hash collision in a secure hash function, or MUCH more
    likely invalid data in the request.
    """
    orig = cachedir / "orig"
    orig.write_bytes(urandom(12345))
    info = flatmirror.Hasher.hash_file(orig, "orig")
    dest = cachedir / "dest"
    wrong_info = flatmirror.FileInfo(info.size, info.digests.copy(), "wrong")
    wrong_info.digests["md5"] = bytes(255 - i for i in wrong_info.digests["md5"])

    with flatmirror.FileCache(cachedir / "cache") as cache:
        cache.addfile(info, orig)
        assert not cache.retrieve(wrong_info, dest)
