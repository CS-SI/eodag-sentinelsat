# -*- coding: utf-8 -*-
# Copyright 2021, CS GROUP - France, http://www.c-s.fr
#
# This file is part of EODAG project
#     https://www.github.com/CS-SI/EODAG
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Sentinelsat plugin to EODAG."""

import os

from setuptools import setup

BASEDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
with open(os.path.join(BASEDIR, "README.rst"), "r") as f:
    readme = f.read()

setup(
    name="eodag_sentinelsat",
    version="0.1.0",
    description="Sentinelsat plugin to EODAG (https://bitbucket.org/geostorm/eodag)",
    long_description=readme,
    author="CS Systemes d'Information (CSSI)",
    author_email="admin@geostorm.eu",
    url="https://bitbucket.org/geostorm/eodag-sentinelsat",
    license="GPLv3",
    entry_points={
        "eodag.plugins.api": [
            "SentinelsatAPI = eodag_sentinelsat:SentinelsatAPI",
        ]
    },
    py_modules=["eodag_sentinelsat"],
    install_requires=[
        "tqdm",
        "sentinelsat",
        "shapely",
    ],
    extras_require={
        "standalone": [
            "eodag >= 2.1.0",
        ],
        "dev": [
            "pre-commit",
            "tox",
        ],
    },
    project_urls={
        "Bug Tracker": "https://bitbucket.org/geostorm/eodag-sentinelsat/issues/",
        "Documentation": "https://bitbucket.org/geostorm/eodag-sentinelsat/src/master/README.rst",
        "Source Code": "https://bitbucket.org/geostorm/eodag-sentinelsat",
    },
    classifiers=(
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: GIS",
    ),
)
