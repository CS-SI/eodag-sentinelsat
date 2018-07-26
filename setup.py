# -*- coding: utf-8 -*-
# Copyright 2018 CS Systemes d'Information (CS SI)
# All rights reserved
from setuptools import setup


setup(
    name="eodag_sentinelsat",
    description="Sentinelsat plugin to EODAG",
    author="CS Systemes d'Information (CSSI)",
    author_email="admin@geostorm.eu",
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
            'eodag'
        ]
    },
)
