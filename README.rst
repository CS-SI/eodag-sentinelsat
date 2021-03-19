eodag-sentinelsat
=================

This is a repository for sentinelsat plugin to `EODAG <https://github.com/CS-SI/eodag>`_.
It's an `Api <https://eodag.readthedocs.io/en/latest/api.html#eodag.plugins.apis.base.Api>`_ plugin that enables to
search and download EO products from catalogs implementing the
`SciHub / Copernicus Open Access Hub interface <https://scihub.copernicus.eu/userguide/WebHome>`_.
It is basically a wrapper around `sentinelsat <https://sentinelsat.readthedocs.io>`_, enabling it to be used on eodag.


Installation
============

eodag-sentinelsat is on `PyPI <https://pypi.org/project/eodag-sentinelsat/>`_:

    python -m pip install eodag-sentinelsat


Contribute
==========

If you intend to contribute to eodag-sentinelsat source code::

    git clone https://github.com/CS-SI/eodag-sentinelsat.git
    cd eodag-sentinelsat
    python -m pip install -e .[dev]
    pre-commit install
    tox


LICENSE
=======

eodag-sentinelsat is licensed under GPLv3.
See LICENSE file for details.


AUTHORS
=======

eodag-sentinelsat is developed by `CS GROUP - France <https://www.c-s.fr>`_.


CREDITS
=======

See NOTICE file.
