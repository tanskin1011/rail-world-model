"""Skip link-specific tests when the host does not permit creating symlinks."""
import errno
import unittest


def symlink_or_skip(link, target):
    try:
        link.symlink_to(target)
    except OSError as error:
        if getattr(error, 'winerror', None) == 1314 or error.errno in (errno.EPERM, errno.ENOTSUP):
            raise unittest.SkipTest('Host does not permit creating symbolic links') from error
        raise
