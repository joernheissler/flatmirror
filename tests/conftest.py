import pytest

from . import flatmirror

h2b = bytes.fromhex


@pytest.fixture
def fileinfo_empty() -> flatmirror.FileInfo:
    return flatmirror.FileInfo(
        0,
        {
            "md5": h2b("d41d8cd98f00b204e9800998ecf8427e"),
            "sha1": h2b("da39a3ee5e6b4b0d3255bfef95601890afd80709"),
            "sha256": h2b("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            "sha512": h2b(
                "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce"
                "47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
            ),
        },
        "empty",
    )


@pytest.fixture
def fileinfo_prng() -> flatmirror.FileInfo:
    return flatmirror.FileInfo(
        1 << 20,
        {
            "md5": h2b("a8cf8266a710e9c7c9468c076025929e"),
            "sha1": h2b("b2bd5a6abfe2546dd4a827170ac7cdbb32bf6977"),
            "sha256": h2b("642607a558c9c932e458f4c3a847928f572e5408b9848e106e7716884e3b5f0a"),
            "sha512": h2b(
                "cab353a38eeae0b2e46001bddc68b165e22e7e1c0a4cd28d1ed90e5bec8a3b9f"
                "6e9f5b038041cbb51309a65bb03c8f82e30eaf1290299fb70ce740c7405c98ae"
            ),
        },
        "prng",
    )


@pytest.fixture
def fileinfo_partial() -> flatmirror.FileInfo:
    return flatmirror.FileInfo(
        1 << 20,
        {
            "md5": h2b("a8cf8266a710e9c7c9468c076025929e"),
            "sha256": h2b("642607a558c9c932e458f4c3a847928f572e5408b9848e106e7716884e3b5f0a"),
        },
        "partial",
    )


@pytest.fixture
def fileinfo_bad() -> flatmirror.FileInfo:
    return flatmirror.FileInfo(
        1 << 10,
        {
            "md5": h2b("aaaaaaaaaaaaaabbbbbbbbbcccccddee"),
            "sha1": h2b("b2bd5a6abfe2546dd4a827170ac7cdbb32bf6977"),
            "sha256": h2b("642607a558c9c932e458f4c3a847928f572e5408b9848e106e7716884e3b5f0a"),
            "sha512": h2b(
                "cab353a38eeae0b2e46001bddc68b165e22e7e1c0a4cd28d1ed90e5bec8a3b9f"
                "6e9f5b038041cbb51309a65bb03c8f82e30eaf1290299fb70ce740c7405c98ae"
            ),
        },
        "bad",
    )
