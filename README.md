# simple-pypi

Super lightweight PyPi server for local development.

Basically it cannot does much, just mimics real PyPI servers: lookup given directory for packages,
generates simple index page with links to them and package's pages with all available versions,
sha1 checksums included.

## How do I run it?

It has no config, but you can configure basic things: listen IP address, port and directory
where simple-pypi will lookup for packages.

All these things are configurable with env vars:
1. `SIMPLE_PYPI_HOST`: listen ip address (default: `127.0.0.1`)
1. `SIMPLE_PYPI_PORT`: listen port (default: `8888`)
1. `SIMPLE_PYPI_PKG_DIR`: directory with python packages

To run simple-pypi server execute this command:
```
$ python app.py
listening for incoming requests on: 127.0.0.1:8888
index url: http://127.0.0.1:8888/simple
rebuild-index url: http://127.0.0.1:8888/simple/rebuild-index
```

## How do I use it?

The tools like `pip` or `pipenv` allow specification of extra index URL,
so you can use `simple-pypi` as extra PyPI index with your private packages
or for your experiments without waste a time for setting up `devpi` server
or for publishing your packages to somewhere.

So the typical work process looks like:
1. working on package (e.g. `api-client`), writing a code, testing
1. build a new package release (e.g. `api-client-0.0.1-py3-none-any.whl`)
1. place package archive to somewhere, where simple-pypi expects (see `SIMPLE_PYPI_PKG_DIR` option)
1. rebuild simple-pypi index (make a `GET /simple/rebuild-index` request)
1. update virtual env of your project with new version of package
1. run project tests

## F.A.Q.

1. Q: Why I should use simple-pypi or devpi instead of install dependencies as 'editable' package?

A: You should not, but if you want to be sure that builded release of your package
will work as expected, you should test it as a package.

1. Q: Why I cannot use `devp`i or `bandersnatch` or `nexus` or whatever else?

A: You can, but simple-pypi is much very lightweight and zero configurate unlike mentioned solutions,
they all have a lot of cool features, but in fact often needs just simple a fast way to place package
to somewhere what can be interpreatated as PyPI index and check project with this new release.
Simple-pypi was created exactly for this.

1. Q: How do I use it with `pip`?

A: Pip supports extra index url, you can use it in this way:

```
pip install --extra-index-url -U http://localhost:8888/simple api-client
```

1. Q: How do I use extra index with pipenv?

A: Please see: https://pipenv.pypa.io/en/latest/advanced/#specifying-package-indexes

Example:

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[[source]]
url = "http://127.0.0.1:8888/simple"
name = "simple-pypi"

[dev-packages]

[packages]
api-client = {version="*", index="simple-pypi"}
aiohttp = {version="*"}
```

1. Q: How do I use it with poetry?

A: Unfortunately poetry has no option like `pip` or `pipenv`, but you can specify url:

```toml
[tool.poetry.dependencies]
python = "^3.10"
api-client = {url = "http://127.0.0.1:8888/simple/api-client-0.0.1-py3-none-any.whl"}
```

Please se: https://python-poetry.org/docs/dependency-specification/#url-dependencies
