# -*- coding: utf-8 -*-
import os

from setuptools import setup


BASEDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
with open(os.path.join(BASEDIR, 'README.rst'), 'r') as f:
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
        'eodag.plugins.api': [
            'SentinelsatAPI = eodag_sentinelsat:SentinelsatAPI',
        ]
    },
    py_modules=['eodag_sentinelsat'],
    install_requires=[
        'tqdm',
        'sentinelsat',
        'shapely',
    ],
    extras_require={
        'standalone': [
            'eodag',
        ],
        'dev': [
            'tox',
        ]
    },
    project_urls={
        "Bug Tracker": "https://bitbucket.org/geostorm/eodag-sentinelsat/issues/",
        "Documentation": "https://bitbucket.org/geostorm/eodag-sentinelsat/src/master/README.rst",
        "Source Code": "https://bitbucket.org/geostorm/eodag-sentinelsat",
    },
    classifiers=(
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering :: GIS',
    ),
)
