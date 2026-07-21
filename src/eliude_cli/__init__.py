from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("eliude-cli")
except PackageNotFoundError:
    # Running from source without the package installed.
    __version__ = "0.0.0+unknown"
