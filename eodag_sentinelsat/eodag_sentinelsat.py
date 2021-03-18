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

import ast
import logging
import zipfile
from datetime import datetime

from eodag.plugins.apis.base import Api
from eodag.plugins.search.qssearch import ODataV4Search
from eodag.utils import get_progress_callback
from eodag.utils.exceptions import RequestError, MisconfiguredError
from sentinelsat import SentinelAPI, SentinelAPIError

logger = logging.getLogger("eodag.plugins.apis.sentinelsat")


class SentinelsatAPI(Api, ODataV4Search):
    """
    SentinelsatAPI plugin.

    Api that enables to search and download EO products from catalogs implementing the SchiHub interface.
    It is basically a wrapper around sentinelsat, enabling it to be used on eodag.

    We use the API to download data. Available keywords are:
    [area, date, raw, area_relation, order_by, limit, offset, **keywords]
    https://sentinelsat.readthedocs.io/en/stable/api.html#sentinelsat.SentinelAPI.query

    The keywords are those that can be found here:
    https://sentinelsat.readthedocs.io/en/stable/api.html#opensearch-example
    """

    def __init__(self, provider, config):
        """Init Sentinelsat plugin."""
        super().__init__(provider, config)
        self.api = None

    def query(self, items_per_page=None, page=None, count=True, **kwargs):
        """
        Query for products.

        :param product_type: (str) Product Type, not used, just here for compatibility reasons
        :param kwargs: (dict) Metadata
        :return: (list, int) List and number of queried products
        """
        eo_products = []
        product_type = kwargs.get("productType", None)
        if product_type is not None:
            # Init Sentinelsat API (connect...)
            self._init_api()

            # Modify the query parameters to be compatible with Sentinelsat query
            query_params, provider_product_type = self.update_keyword(**kwargs)

            # add pagination
            pagination_params_str = self.config.pagination.get(
                "next_page_query_obj", {}
            ).format(
                items_per_page=items_per_page,
                page=page,
                skip=items_per_page * (page - 1),
            )
            pagination_params = ast.literal_eval(pagination_params_str)
            query_params.update(pagination_params)

            try:
                # Query
                results = self.api.query(**query_params)

                # Create the storage_status field
                for uuid, res in results.items():
                    res["storage_status"] = self.api.is_online(uuid)

                # Normalize results skeletons (using providers.yml file)
                eo_products = self.normalize_results(results.values(), **kwargs)

            except TypeError:
                import traceback as tb
                # Sentinelsat api query method raises a TypeError for finding None in the json feed received
                # as a response from the sentinel server, when looking for 'opensearch:totalResults' key.
                # This may be interpreted as the the api not finding any result from the query.
                # This is what is assumed here.
                logger.debug(
                    "Something went wrong during the query with self.api api:\n %s",
                    tb.format_exc(),
                )
                logger.info("No results found !")

            except SentinelAPIError as ex:
                # TODO: change it to ServerError when ssat 0.15 will be published !
                """
                    SentinelAPIError -- the parent, catch-all exception. Only used when no other more specific exception can be applied.
                    SentinelAPILTAError -- raised when retrieving a product from the Long Term Archive.
                    ServerError -- raised when the server responded in an unexpected manner, typically due to undergoing maintenance.
                    UnauthorizedError -- raised when attempting to retrieve a product with incorrect credentials.
                    QuerySyntaxError -- raised when the query string could not be parsed on the server side.
                    QueryLengthError -- raised when the query string length was excessively long.
                    InvalidKeyError -- raised when product with given key was not found on the server.
                    InvalidChecksumError -- MD5 checksum of a local file does not match the one from the server.
                """
                raise RequestError(ex) from ex

        return eo_products, len(eo_products)

    def download(self, product, auth=None, progress_callback=None, **kwargs) -> str:
        """
        Download product.

        :param product: (EOProduct) EOProduct
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param kwargs: Not used, just here for compatibility reasons
        :return: Downloaded product path
        """
        # Init Sentinelsat API if needed (connect...)
        prods = self.download_all(product, auth, progress_callback, **kwargs)

        # Manage the case if nothing has been downloaded
        return prods[0] if len(prods) > 0 else ""

    def download_all(
        self, search_result, auth=None, progress_callback=None, **kwargs
    ) -> list:
        """
        Download all products.

        :param search_result: A collection of EO products resulting from a search
        :type search_result: :class:`~eodag.api.search_result.SearchResult`
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param kwargs: Not used, just here for compatibility reasons
        :return: List of downloaded products
        """
        # Init Sentinelsat API if needed (connect...)
        self._init_api()

        # Download all products
        prod_ids = [prod.properties["uuid"] for prod in search_result.data]
        success, _, _ = self.api.download_all(
            prod_ids, directory_path=self.config.outputs_prefix
        )

        # Only extract the successfully downloaded products
        paths = [self.extract(prods) for prods in success.values()]
        return paths

    def extract(self, product_info: dict) -> str:
        """
        Extract products if needed

        :param product_info: Product info
        :return: Path (archive or extracted according to the config)
        """
        # Extract them if needed
        if self.config.extract and product_info["path"].endswith(".zip"):
            logger.info("Extraction activated")
            with zipfile.ZipFile(product_info["path"], "r") as zfile:
                fileinfos = zfile.infolist()
                with get_progress_callback() as bar:
                    bar.max_size = len(fileinfos)
                    bar.unit = "file"
                    bar.desc = "Extracting files from {}".format(product_info["path"])
                    bar.unit_scale = False
                    bar.position = 2
                    for fileinfo in fileinfos:
                        zfile.extract(fileinfo, path=self.config.outputs_prefix)
                        bar(1)
            return product_info["path"][: product_info["path"].index(".zip")]
        else:
            return product_info["path"]

    def _init_api(self) -> None:
        """ Initialize Sentinelsat API if needed (connection and link) """
        if not self.api:
            try:
                logger.debug('Initializing Sentinelsat API')
                self.api = SentinelAPI(
                    self.config.credentials['username'],
                    self.config.credentials['password'],
                    self.config.endpoint
                )
            except KeyError as ex:
                raise MisconfiguredError(ex) from ex
        else:
            logger.debug("Sentinelsat API already initialized")

    def update_keyword(self, **kwargs):
        """Update keywords for SentinelSat API."""
        product_type = kwargs.get("productType", None)
        provider_product_type = self.map_product_type(product_type, **kwargs)
        keywords = {k: v for k, v in kwargs.items() if k != "auth" and v is not None}
        keywords["productType"] = provider_product_type

        # Add to the query, the queryable parameters set in the provider product type definition
        product_type_def_params = self.get_product_type_def_params(
            product_type, **kwargs
        )
        keywords.update(
            {
                k: v
                for k, v in product_type_def_params.items()
                if (
                    k not in keywords.keys()
                    and k in self.config.metadata_mapping.keys()
                    and isinstance(self.config.metadata_mapping[k], list)
                )
            }
        )
        qp, qs = self.build_query_string(product_type, **keywords)

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

            qp["date"] = (
                datetime.fromisoformat(qp.pop("start")),
                datetime.fromisoformat(qp.pop("end")),
            )

        # Footprint
        if "area" in qp:
            qp["area"] = qp.pop("area").wkt

        return qp, provider_product_type
