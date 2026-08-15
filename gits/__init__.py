"""gits — GitHub content fetcher & sync CLI."""

try:
    from importlib.metadata import version
    __version__ = version("gits")
except Exception:
    __version__ = "0.1.0"