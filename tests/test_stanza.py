import pytest

from . import flatmirror

RELEASE = """
Origin: Debian
Label: Debian
Suite: stable
Version: 12.7
Codename: bookworm
Changelogs: https://metadata.ftp-master.debian.org/changelogs/@CHANGEPATH@_changelog
Date: Sat, 31 Aug 2024 09:45:30 UTC
Acquire-By-Hash: yes
No-Support-for-Architecture-all: Packages
Architectures: all amd64 arm64 armel armhf i386 mips64el mipsel ppc64el s390x
Components: main contrib non-free-firmware non-free
Description: Debian 12.7 Released 31 August 2024
MD5Sum:
 0ed6d4c8891eb86358b94bb35d9e4da4  1484322 contrib/Contents-all
 d0a0325a97c42fd5f66a8c3e29bcea64    98581 contrib/Contents-all.gz
 6749b4b80c6d005994c534770a684894 22232676 main/binary-all/Packages
 d3b35a385861cbe833f7fc862f98aa72  5668718 main/binary-all/Packages.gz
 6ff093783ed25f273bc915af9a0c725c  4208772 main/binary-all/Packages.xz
SHA256:
 d6c9c82f4e61b4662f9ba16b9ebb379c57b4943f8b7813091d1f637325ddfb79  1484322 contrib/Contents-all
 c22d03bdd4c7619e1e39e73b4a7b9dfdf1cc1141ed9b10913fbcac58b3a943d0    98581 contrib/Contents-all.gz
 eba95496affec2ec9a4bcd71b3377882feaf922b29d1eaef07ede635941519b2 22232676 main/binary-all/Packages
 df3356cbd34dee0c7d63a03b8fc138d5f0934f917bd50d2239fb6a32613bc5dc  5668718 main/binary-all/Packages.gz
 fc5dbcedb34c268d7424ccc99a83995bd784e26cddfcaf04170eae0e319bfacd  4208772 main/binary-all/Packages.xz
"""

CONTROL = """Source: xorg-server
Build-Depends:
 debhelper-compat (= 12),
 po-debconf,
 quilt,
# glamor
 xkb-data,
Homepage:  https://www.x.org/ 

Package: xserver-xorg-core-udeb
Provides:
 ${videoabi},
 ${inputabi},
Description: Xorg X server - core server
    This is a udeb, or a microdeb, for the debian-installer.   
 . 
 More information about X.Org can be found at:
 <URL:https://www.x.org>
# exclude sparc because of linker errors
Architecture: any

"""

DUPLICTATE_KEY = """
Foo: Bar
Other: Value
Foo: Baz
"""

GIBBERISH = """
Foo: Bar
Hello, World!
"""

BAD_FOLD = """
 Hello
 World
Foo: Bar
"""

BAD_SUMS = """
MD5Sum: blah
  d0a0325a97c42fd5f66a8c3e29bcea64    98581 contrib/Contents-all.gz
"""

BAD_SIZE = """
MD5Sum:
 6ff093783ed25f273bc915af9a0c725c  4208772 main/binary-all/Packages.xz
SHA256:
 fc5dbcedb34c268d7424ccc99a83995bd784e26cddfcaf04170eae0e319bfacd  1234567 main/binary-all/Packages.xz
"""


def test_parse_release() -> None:
    releases = list(flatmirror.split_stanzas(RELEASE.splitlines()))
    assert len(releases) == 1
    release = releases[0]
    assert release.get_str("date") == "Sat, 31 Aug 2024 09:45:30 UTC"
    assert release.get_str("foo", "bar") == "bar"
    assert release.get_multi("md5sum") == (
        "",
        [
            "0ed6d4c8891eb86358b94bb35d9e4da4  1484322 contrib/Contents-all",
            "d0a0325a97c42fd5f66a8c3e29bcea64    98581 contrib/Contents-all.gz",
            "6749b4b80c6d005994c534770a684894 22232676 main/binary-all/Packages",
            "d3b35a385861cbe833f7fc862f98aa72  5668718 main/binary-all/Packages.gz",
            "6ff093783ed25f273bc915af9a0c725c  4208772 main/binary-all/Packages.xz",
        ],
    )

    with pytest.raises(KeyError):
        release.get_str("foo")

    with pytest.raises(KeyError):
        release.get_multi("foo")

    with pytest.raises(ValueError):
        release.get_str("md5sum")

    with pytest.raises(ValueError):
        release.get_multi("label")


def test_parse_control() -> None:
    control = flatmirror.split_stanzas(CONTROL.splitlines())
    src = next(control)
    assert src.get_multi("build-depends") == (
        "",
        ["debhelper-compat (= 12),", "po-debconf,", "quilt,", "xkb-data,"],
    )
    assert src.get_str("homepage") == "https://www.x.org/"

    pkg = next(control)
    assert pkg.get_str("architecture") == "any"
    assert pkg.get_multi("description") == (
        "Xorg X server - core server",
        [
            "This is a udeb, or a microdeb, for the debian-installer.",
            ".",
            "More information about X.Org can be found at:",
            "<URL:https://www.x.org>",
        ],
    )
    with pytest.raises(StopIteration):
        next(control)


def test_duplicate_key() -> None:
    with pytest.raises(ValueError):
        next(flatmirror.split_stanzas(DUPLICTATE_KEY.splitlines()))


def test_gibberish() -> None:
    with pytest.raises(ValueError):
        next(flatmirror.split_stanzas(GIBBERISH.splitlines()))


def test_bad_fold() -> None:
    with pytest.raises(ValueError):
        next(flatmirror.split_stanzas(BAD_FOLD.splitlines()))


def test_parse_release_packages() -> None:
    pks = flatmirror.parse_release_file(RELEASE.splitlines())

    with pytest.raises(ValueError):
        flatmirror.parse_release_file(CONTROL.splitlines())

    with pytest.raises(ValueError):
        flatmirror.parse_release_file(BAD_SUMS.splitlines())

    with pytest.raises(ValueError):
        flatmirror.parse_release_file(BAD_SIZE.splitlines())
