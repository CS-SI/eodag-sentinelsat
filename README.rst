eodag-sentinelsat
=================

This is a repository for sentinelsat plugin to `EODAG <https://bitbucket.org/geostorm/eodag>`_.
It's an `Api <https://eodag.readthedocs.io/en/latest/api.html#eodag.plugins.apis.base.Api>`_ plugin that enables to
search and download EO products from catalogs implementing the `SchiHub interface <https://scihub.copernicus.eu/userguide/3FullTextSearch>`_.
It is basically a wrapper around `sentinelsat <https://sentinelsat.readthedocs.io>`_, enabling it to be used on eodag.

Installation
============

First, clone the repository::

    git clone https://aoyono@bitbucket.org/aoyono/eodag-sentinelsat.git
    cd eodag-sentinelsat

Then:

* If you already have a particular version of eodag installed on your system::

    python -m pip install .

* If you don't have eodag installed and want it installed and knowing about sentinelsat plugin or if you want to
  develop on this repository::

    python -m pip install .[standalone]

  The standalone install will install eodag itself along the way

Providers configurations
========================

This repository comes with a `providers configuration file <providers.yml>`_ where providers that implement scihub
interface are configured. Currently available providers are:

* scihub: uses `SentinelsatAPI` for `the scihub apihub <https://scihub.copernicus.eu/apihub/>`_

To add these providers to the end of eodag's providers configuration that resides in the site packages of your
Python installation or virtual environment::

    cat providers.yml >> $(python -m pip show eodag | grep Location | cut -d' ' -f2)/eodag/resources/providers.yml

Contribute
==========

If you intend to contribute to eodag-sentinelsat source code::

    git clone https://bitbucket.org/geostorm/eodag-sentinelsat.git
    cd eodag-sentinelsat
    python -m pip intall -e .[standalone,dev]
    tox

LICENSE
=======

eodag-sentinelsat is licensed under GPLv3.
See LICENSE file for details.


AUTHORS
=======

eodag-sentinelsat is developed by CS Systèmes d'Information.


CREDITS
=======

See NOTICE file.
