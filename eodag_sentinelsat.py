# -*- coding: utf-8 -*-
# eodag-sentinelsat, a plugin for searching and downloading products from Copernicus Scihub
#     Copyright (C) 2018, CS Systemes d'Information, http://www.c-s.fr
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
from __future__ import unicode_literals
import logging
import zipfile
from datetime import datetime

from eodag.plugins.search.qssearch import ODataV4Search
from sentinelsat import SentinelAPI
from tqdm import tqdm
from eodag.plugins.apis.base import Api

logger = logging.getLogger('eodag.plugins.apis.sentinelsat')


class SentinelsatAPI(Api, ODataV4Search):
    """
    Api that enables to search and download EO products from catalogs implementing the SchiHub interface.
    It is basically a wrapper around sentinelsat, enabling it to be used on eodag.
    """

    def __init__(self, provider, config):
        super().__init__(provider, config)
        self.api = None

    @staticmethod
    def from_prodtype_to_platform(prod_type):
        if prod_type.startswith("S1"):
            return "Sentinel-1"

        elif prod_type.startswith("S2"):
            return "Sentinel-2"

        elif prod_type.startswith("S3"):
            return "Sentinel-3"

        else:
            raise Exception("Invalid producttype for Sentinelsat AOI")

    def query(self, product_type=None, *args, **kwargs):
        """
        Query
        :param product_type: (str) Product Type, not used, just here for compatibility reasons
        :param kwargs: (dict) Metadata
        :return: (list, int) List and number of queried products
        """
        eo_products = []
        product_type = kwargs.get("productType")
        if product_type is not None:
            # Init Sentinelsat API (connect...)
            self._init_api()

            # Modify the query parameters to be compatible with Sentinelsat query
            kwargs["platformname"] = self.from_prodtype_to_platform(product_type)
            query_params, provider_product_type = self.update_keyword(*args, **kwargs)
            try:
                # Query
                results = self.api.query(**query_params)

                # Create the storage_status field
                for uuid, res in results.items():
                    res["storage_status"] = self.api.is_online(uuid)

                # Normalize results skeletons (using providers.yml file)
                eo_products = self.normalize_results(results.values(),
                                                     product_type,
                                                     provider_product_type,
                                                     *args, **kwargs)

            except TypeError:
                import traceback as tb
                # Sentinelsat api query method raises a TypeError for finding None in the json feed received
                # as a response from the sentinel server, when looking for 'opensearch:totalResults' key.
                # This may be interpreted as the the api not finding any result from the query.
                # This is what is assumed here.
                logger.debug('Something went wrong during the query with self.api api:\n %s', tb.format_exc())
                logger.info('No results found !')

        return eo_products, len(eo_products)

    def download(self, product, auth=None, progress_callback=None, **kwargs) -> str:
        """
        Download products

        :param product: (EOProduct) EOProduct
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param kwargs: Not used, just here for compatibility reasons
        :return: Downloaded product path
        """
        # Init Sentinelsat API if needed (connect...)
        self._init_api()

        # Download all products
        prod_id = product.properties['id']
        product_info = self.api.download_all(
            [prod_id],
            directory_path=self.config.outputs_prefix
        )

        # Only select the downloaded products
        product_info = product_info[0][prod_id]

        # Extract them if needed
        if self.config.extract and product_info['path'].endswith('.zip'):
            logger.info('Extraction activated')
            with zipfile.ZipFile(product_info['path'], 'r') as zfile:
                fileinfos = zfile.infolist()
                with tqdm(fileinfos,
                          unit='file',
                          desc='Extracting files from {}'.format(product_info['path'])) as progressbar:
                    for fileinfo in progressbar:
                        zfile.extract(fileinfo, path=self.config.outputs_prefix)
            return product_info['path'][:product_info['path'].index('.zip')]
        else:
            return product_info['path']

    def download_all(self, product, auth=None, progress_callback=None, **kwargs) -> list:
        """
        Download products

        :param product: EOProduct
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param kwargs: Not used, just here for compatibility reasons
        :return: List of downloaded products
        """
        # Init Sentinelsat API if needed (connect...)
        self._init_api()

        # Download all products
        prod_ids = [prod.properties["uuid"] for prod in product.data]
        product_info = self.api.download_all(prod_ids, directory_path=self.config.outputs_prefix)

        # Only select the downloaded products
        paths = []
        for prod_id in prod_ids:
            info = product_info[0][prod_id]

            # Extract them if needed
            if self.config.extract and info['path'].endswith('.zip'):
                logger.info('Extraction activated')
                with zipfile.ZipFile(info['path'], 'r') as zfile:
                    fileinfos = zfile.infolist()
                    with tqdm(fileinfos,
                              unit='file',
                              desc='Extracting files from {}'.format(info['path'])) as progressbar:
                        for fileinfo in progressbar:
                            zfile.extract(fileinfo, path=self.config.outputs_prefix)
                paths.append(info['path'][:info['path'].index('.zip')])
            else:
                paths.append(info['path'])

        return paths

    def _init_api(self):
        """ Initialize Sentinelsat API if needed (connection and link) """
        if not self.api:
            logger.debug('Initializing Sentinelsat API')
            self.api = SentinelAPI(
                self.config.credentials['username'],
                self.config.credentials['password'],
                self.config.endpoint
            )
        else:
            logger.debug('Sentinelsat API already initialized')

    def update_keyword(self, *args, **kwargs):
        """
        Update keywords for SentinelSat API
        """
        product_type = kwargs.get("productType", None)
        provider_product_type = self.map_product_type(product_type, *args, **kwargs)
        keywords = {k: v for k, v in kwargs.items() if k != "auth" and v is not None}
        keywords["productType"] = provider_product_type

        # Add to the query, the queryable parameters set in the provider product type definition
        product_type_def_params = self.get_product_type_def_params(
            product_type, *args, **kwargs
        )
        keywords.update(
            {
                k: v
                for k, v in product_type_def_params.items() if (k not in keywords.keys()
                                                                and k in self.config.metadata_mapping.keys()
                                                                and isinstance(self.config.metadata_mapping[k], list))
            }
        )
        qp, qs = self.build_query_string(product_type, *args, **keywords)

        # If we were not able to build query params but have search criteria, this means
        # the provider does not support the search criteria given. If so, stop searching
        # right away
        if not qp and keywords:
            qp = {}
        self.query_params = qp
        self.query_string = qs

        # Overload of some parameters
        # Cloud cover
        if "cloudcoverpercentage" in qp:
            qp["cloudcoverpercentage"] = [0, qp["cloudcoverpercentage"]]

        # Date
        if "start" in qp:
            if "end" not in qp:
                raise ValueError("Missing ending day")
            qp["date"] = (datetime.fromisoformat(qp.pop("start")), datetime.fromisoformat(qp.pop("end")))

        # Footprint
        if "area" in qp:
            qp["area"] = qp.pop("area").wkt

        return qp, provider_product_type
