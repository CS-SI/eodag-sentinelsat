eodag-sentinelsat
=================

This is a repository for sentinelsat plugin to `EODAG <https://github.com/CS-SI/eodag>`_.
It's an `Api <https://eodag.readthedocs.io/en/latest/api.html#eodag.plugins.apis.base.Api>`_ plugin that enables to
search and download EO products from catalogs implementing the
`SciHub / Copernicus Open Access Hub interface <https://scihub.copernicus.eu/userguide/WebHome>`_.
It is basically a wrapper around `sentinelsat <https://sentinelsat.readthedocs.io>`_, enabling it to be used on eodag.


Installation
============

* If you already have a particular version of eodag installed on your system::

    python -m pip install eodag-sentinelsat

* If you don't have eodag installed and want it installed and knowing about sentinelsat plugin or if you want to
  develop on this repository::

    python -m pip install eodag-sentinelsat[standalone]

  The standalone install will install eodag itself along the way


Contribute
==========

If you intend to contribute to eodag-sentinelsat source code::

    git clone https://github.com/CS-SI/eodag-sentinelsat.git
    cd eodag-sentinelsat
    python -m pip install -e .[standalone,dev]
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
