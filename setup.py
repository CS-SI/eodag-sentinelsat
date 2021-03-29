# -*- coding: utf-8 -*-
# eodag-sentinelsat, a plugin for searching and downloading products from Copernicus Scihub
#     Copyright 2021, CS GROUP - France, http://www.c-s.fr
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Sentinelsat plugin to EODAG."""

import os

from setuptools import find_packages, setup

BASEDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
with open(os.path.join(BASEDIR, "README.rst"), "r") as f:
    readme = f.read()

setup(
    name="eodag_sentinelsat",
    version="0.3.0",
    description="Sentinelsat plugin to EODAG (https://github.com/CS-SI/eodag)",
    long_description=readme,
    author="CS Systemes d'Information (CSSI)",
    author_email="admin@geostorm.eu",
    url="https://github.com/CS-SI/eodag-sentinelsat",
    license="GPLv3",
    packages=find_packages(),
    install_requires=[
        "sentinelsat",
        "eodag >= 2.2.0",
    ],
    extras_require={
        "dev": [
            "pre-commit",
            "tox",
        ]
    },
    entry_points={
        "eodag.plugins.api": [
            "SentinelsatAPI = eodag_sentinelsat.eodag_sentinelsat:SentinelsatAPI",
        ]
    },
    project_urls={
        "Bug Tracker": "https://github.com/CS-SI/eodag-sentinelsat/issues/",
        "Documentation": "https://github.com/CS-SI/eodagsentinelsat/blob/master/README.rst",
        "Source Code": "https://github.com/CS-SI/eodag-sentinelsat",
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    package_data={"eodag_sentinelsat": ["*.yml"]},
    include_package_data=True,
)
