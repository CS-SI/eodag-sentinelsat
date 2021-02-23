# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

BASEDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
with open(os.path.join(BASEDIR, 'README.rst'), 'r') as f:
    readme = f.read()

setup(
    name="eodag_sentinelsat",
    version="0.2.0",
    description="Sentinelsat plugin to EODAG (https://bitbucket.org/geostorm/eodag)",
    long_description=readme,
    author="CS Systemes d'Information (CSSI)",
    author_email="admin@geostorm.eu",
    url="https://bitbucket.org/geostorm/eodag-sentinelsat",
    license="GPLv3",
    packages=find_packages(),
    install_requires=[
        'tqdm',
        'sentinelsat',
        'eodag',
        'shapely'
    ],
    extras_require={
        'dev': [
            'tox',
        ]
    },
    entry_points={
        'eodag.plugins.api': [
            'SentinelsatAPI = eodag_sentinelsat:SentinelsatAPI',
        ]
    },
    project_urls={
        "Bug Tracker": "https://bitbucket.org/geostorm/eodag-sentinelsat/issues/",
        "Documentation": "https://bitbucket.org/geostorm/eodag-sentinelsat/src/master/README.rst",
        "Source Code": "https://bitbucket.org/geostorm/eodag-sentinelsat",
    },
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    package_data={'eodag_sentinelsat': ['*.yml']},
    include_package_data=True
)
