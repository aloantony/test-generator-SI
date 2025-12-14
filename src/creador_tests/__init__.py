"""Top-level package for the creador_tests project.

This package provides command line tools and a programmatic API to
convert Moodle/UBUVirtual quiz review PDFs into a canonical JSON
representation. The conversion pipeline is broken into several
modules under ``creador_tests`` (see the ``README.md`` for an
overview).

The version defined here follows semantic versioning and will be
incremented as the project evolves.
"""

from importlib.metadata import version as _version

__all__ = ["__version__"]

try:
    # Attempt to read the version from the installed package metadata. If
    # ``creador_tests`` is not installed (e.g. during development), fall
    # back to a hard-coded default.
    __version__: str = _version("creador_tests")  # type: ignore[no-untyped-call]
except Exception:
    __version__ = "0.1.0"