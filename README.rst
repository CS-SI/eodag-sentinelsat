    [!CAUTION]

    **This repository is no longer maintained** as SciHub / Copernicus Open Access Hub is now closed.
    You should now directly use `EODAG <https://github.com/CS-SI/eodag>`_ with ``cop_dataspace`` (Copernicus Dataspace
    Ecosystem) provider which is the official data distribution system for Copernicus Sentinel data.

.. image:: https://badge.fury.io/py/eodag-sentinelsat.svg
    :target: https://badge.fury.io/py/eodag-sentinelsat

.. image:: https://img.shields.io/pypi/l/eodag-sentinelsat.svg
    :target: https://pypi.org/project/eodag-sentinelsat/

.. image:: https://img.shields.io/pypi/pyversions/eodag-sentinelsat.svg
    :target: https://pypi.org/project/eodag-sentinelsat/

eodag-sentinelsat
=================

This is a repository for sentinelsat plugin to `EODAG <https://github.com/CS-SI/eodag>`_.
It's an `Api <https://eodag.readthedocs.io/en/latest/plugins.html>`_ plugin that enables to
search and download EO products from catalogs implementing the
`SciHub / Copernicus Open Access Hub interface <https://scihub.copernicus.eu/userguide/WebHome>`_.
It is basically a wrapper around `sentinelsat <https://sentinelsat.readthedocs.io>`_, enabling it to be used on eodag.

.. image:: https://eodag.readthedocs.io/en/latest/_static/eodag_bycs.png
    :target: https://github.com/CS-SI/eodag

|


Installation
============

eodag-sentinelsat is on `PyPI <https://pypi.org/project/eodag-sentinelsat/>`_::

    python -m pip install eodag-sentinelsat

Configuration
=============

1. Register to `Scihub <https://scihub.copernicus.eu/userguide/SelfRegistration>`_ to get the required credentials (username/password).

2. Follow the guidelines provided in `EODAG's documentation <https://eodag.readthedocs.io/en/latest/getting_started_guide/configure.html>`_
   to configure the plugin. You can create a dedicated configuration file or edit the default one ``~/.config/eodag/eodag.yml``:

   .. code-block:: yaml

      scihub:
          priority: 2  # Must be higher than the other providers' priorities
          api:
              credentials:
                  username: "PLEASE_CHANGE_ME"  # Your own username
                  password: "PLEASE_CHANGE_ME"  # Your own password

Examples
========

Python API:

.. code-block:: python

   import eodag

   dag = EODataAccessGateway()

   search_results, _ = dag.search(
       productType="S2_MSI_L1C",
       start="2021-03-01",
       end="2021-03-31",
       geom={"lonmin": 1, "latmin": 43, "lonmax": 2, "latmax": 44}
   )
   product_paths = dag.download_all(search_results)

CLI:

.. code-block:: bash

   eodag search \
      --productType S2_MSI_L1C \
      --start 2018-01-01 \
      --end 2018-01-31 \
      --box 1 43 2 44 \
      --storage my_search.geojson
   eodag download --search-results my_search.geojson

Contribute
==========

If you intend to contribute to eodag-sentinelsat source code::

    git clone https://github.com/CS-SI/eodag-sentinelsat.git
    cd eodag-sentinelsat
    python -m pip install -e .[dev]
    pre-commit install

We use ``pre-commit`` to run a suite of linters, formatters and pre-commit hooks (``black``, ``isort``, ``flake8``)
to ensure the code base is homogeneously formatted and easier to read. It's important that you install
it, since we run the exact same hooks in the Continuous Integration.

To run the default test suite (which excludes end-to-end tests):

.. code-block:: bash

    tox

To only run end-to-end test:

.. code-block:: bash

    tox -- tests/test_end_to_end.py

LICENSE
=======

eodag-sentinelsat is licensed under GPLv3.
See `LICENSE <https://github.com/CS-SI/eodag-sentinelsat/blob/develop/LICENSE>`_ for details.

Authors
=======

eodag-sentinelsat has been created by `CS GROUP - France <https://www.csgroup.eu/>`_.

Credits
=======

See NOTICE file.
