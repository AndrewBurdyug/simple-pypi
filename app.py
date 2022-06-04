"""Simple PyPI server.

WARNING: use this only for local development!
"""
import hashlib
import logging
import os
from collections import defaultdict
from functools import cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import NewType, Tuple

from packaging.utils import parse_sdist_filename, parse_wheel_filename

SERVER_HOST = os.environ.get("SIMPLE_PYPI_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SIMPLE_PYPI_PORT", 8888))
PKG_DIR = os.environ.get("SIMPLE_PYPI_PKG_DIR")
LOGGER = logging.getLogger("simple-pypi")
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
LOGGER.addHandler(ch)

BASE_HREF = "/simple"
REBUILD_LOC = f"{BASE_HREF}/rebuild-index"
INDEX_URL = f"http://{SERVER_HOST}:{SERVER_PORT}{BASE_HREF}"
REBUILD_URL = f"http://{SERVER_HOST}:{SERVER_PORT}{REBUILD_LOC}"

if not PKG_DIR:
    LOGGER.error("Failure: SIMPLE_PYPI_PKG_DIR must not be empty")
    exit(1)


PackageName = NewType("PackageName", str)
PackageVersion = NewType("PackageVersion", str)
PackageSHA1 = NewType("PackageSHA1", str)


@cache
def extract_package_metadata(
    pkg_filename: str,
) -> Tuple[PackageName, PackageVersion, PackageSHA1]:
    """Extract base metadtaa from package: name and version."""
    if pkg_filename.endswith(".whl"):
        name, ver, *_ = parse_wheel_filename(pkg_filename)
    else:
        name, ver = parse_sdist_filename(pkg_filename)
    sha1 = hashlib.sha1(open(Path(PKG_DIR) / Path(pkg_filename), "rb").read())
    return name, ver.base_version, sha1.hexdigest()


STATIC_FILES = []


def find_packages(pkg_dir: str) -> dict:
    """Find packages and generate their links."""
    data = defaultdict(list)
    for pkg in os.listdir(PKG_DIR):
        if pkg.endswith(".whl") or pkg.endswith(".gz"):
            name, ver, sha1 = extract_package_metadata(pkg)
            STATIC_FILES.append(f"{BASE_HREF}/{pkg}")
            data[f"{BASE_HREF}/{name}"].append(
                {"name": name, "ver": ver, "filename": pkg, "sha1": sha1}
            )
    return data


@cache
def generate_package_page(pkg_page: str) -> str:
    """Generate package page content."""
    pkg_metadata = PACKAGES[pkg_page]
    pkg_name = pkg_metadata[0]["name"]
    pkg_links = " ".join(
        f'<a rel="internal" href="{BASE_HREF}/{x["filename"]}#sha1={x["sha1"]}">{x["filename"]}</a>'
        for x in pkg_metadata
    )
    return f"""<!DOCTYPE html>
<html>
  <head>
    <title>Links for {pkg_name}</title>
  </head>
  <body>
    <h1>Links for {pkg_name}</h1>
    {pkg_links}
  </body>
</html>"""


def refresh_index(pkg_dir: str) -> None:
    """Refresh packages."""
    global PACKAGES
    PACKAGES = find_packages(pkg_dir)


refresh_index(PKG_DIR)


def generate_index() -> str:
    """Generate index page."""
    packages = " ".join(
        f'<a href="{k}">{v[0]["name"]}</a>' for k, v in PACKAGES.items()
    )
    return f"""<!DOCTYPE html>
<html>
  <head>
    <title>Simple Index</title>
    <meta name="api-version" value="2" />
  </head>
  <body>
    {packages}
  </body>
</html>"""


PackageContent = NewType("PackageContent", bytes)
PackageContentType = NewType("PackageContentType", str)


def read_package_content(pkg_link: str) -> Tuple[PackageContent, PackageContentType]:
    pkg_filename, *_ = Path(pkg_link).name.split("#")
    content_type = "application/octet-stream"
    if pkg_filename.endswith(".whl"):
        content_type = "application/x-tar"
    return open(Path(PKG_DIR) / Path(pkg_filename), "rb").read(), content_type


class RequestHandler(SimpleHTTPRequestHandler):
    """Simple http request handler."""

    protocol_version = "HTTP/1.1"

    def do_GET(self):  # noqa: N802
        """Handle all GET requests."""
        content_type = "text/html"
        path = self.path.rstrip("/")
        if path == BASE_HREF:
            payload = generate_index().encode("utf8")
        elif path in PACKAGES.keys():
            payload = generate_package_page(path).encode("utf8")
        elif path in STATIC_FILES:
            payload, content_type = read_package_content(path)
        elif path == REBUILD_LOC:
            refresh_index(PKG_DIR)
            payload = b"Index was rebuild successfully"
        else:
            payload = b"Not Found"

        self.send_response(200)

        self.send_header("Connection", "Keep-Alive")
        self.send_header("Keep-Alive", "timeout=5, max=1000")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(payload))
        self.send_header("Access-Control-Allow-Origin", "*")

        self.end_headers()

        self.wfile.write(payload)


def run_http_server():
    """Run http server.

    WARNING: Infinite loop!
    """
    server = ThreadingHTTPServer((SERVER_HOST, SERVER_PORT), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    LOGGER.info(
        f"listening for incoming requests on: {SERVER_HOST}:{SERVER_PORT}\n"
        f"index url: {INDEX_URL}\n"
        f"rebuild-index url: {REBUILD_URL}\n"
    )
    run_http_server()
