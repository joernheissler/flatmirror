==========
flatmirror
==========

Mirror program for Debian's "Flat Repository Format".

The format is described in:
https://wiki.debian.org/DebianRepository/Format#Flat_Repository_Format

`flatmirror` downloads a "flat" debian repository and stores it in the local file system.
All files are hard linked into a cache directory for efficient storage + download.

The downloaded files can be served to local apt clients through a webserver.

Requirements
------------
* File system with hard-link support.
* Support for POSIX file locks
* Python >= 3.10
* Python packages: requests, cbor2
* gpgv utility

Installation
------------
.. console::

    # apt install python3 python3-requests python3-cbor2 gpgv
    # cp flatmirror /usr/local/bin/

Usage
-----
XXX

Contributing
------------
Open an issue, pull request or discussion on `GitHub <https://github.com/joernheissler/flatmirror>`.
All contributions are made available under the project's `license <LICENSE>`.
