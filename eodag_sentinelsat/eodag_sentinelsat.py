# -*- coding: utf-8 -*-
# eodag-sentinelsat, a plugin for searching and downloading products from Copernicus Scihub
#     Copyright 2021, CS GROUP - France, https://www.csgroup.eu/
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
import logging as py_logging
import shutil
import types
from datetime import date, datetime

from dateutil.parser import isoparse
from eodag.api.search_result import SearchResult
from eodag.plugins.apis.base import Api
from eodag.plugins.download.base import (
    DEFAULT_DOWNLOAD_TIMEOUT,
    DEFAULT_DOWNLOAD_WAIT,
    Download,
)
from eodag.plugins.search.qssearch import QueryStringSearch
from eodag.utils import ProgressCallback
from eodag.utils import logging as eodag_logging
from eodag.utils import path_to_uri
from eodag.utils.exceptions import (
    MisconfiguredError,
    NotAvailableError,
    RequestError,
)
from eodag.utils.notebook import NotebookWidgets
from sentinelsat import SentinelAPI, ServerError

logger = py_logging.getLogger("eodag.plugins.apis.sentinelsat")


class _ProductManager(object):
    """Manage product status before and after downloading it.

    A simple class whose instance attributes are used to save and update the
    product state after ``SentinelsatAPI._prepare_downloads`` and
    ``SentinelsatAPI.download_all``
    """

    def __init__(self, uuid, product):
        self.uuid = uuid  #  str
        self.product = product  #  EOProduct
        self.fs_path = None  #  str
        self.record_filename = None  # str
        self.to_download = None  # bool
        self.downloaded_by_sentinelsat = None  # bool


class SentinelsatAPI(Api, QueryStringSearch, Download):
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

        :param page: The page number to retur (default: 1)
        :type page: int
        :param items_per_page: The number of results that must appear in one single
                               page
        :type items_per_page: int
        :param count:  To trigger a count request (default: True)
        :type count: bool
        :param kwargs: (dict) Metadata
        :return: A collection of EO products matching the criteria and the total count of products
                 available
        :rtype: tuple(:class:`~eodag.api.search_result.SearchResult`, int or None)
        """
        eo_products = []

        # Init Sentinelsat API (connect...)
        self._init_api()

        # Modify the query parameters to be compatible with Sentinelsat query
        query_params, provider_product_type = self._update_keyword(**kwargs)

        # add pagination
        try:
            pagination_params_str = self.config.pagination.get(
                "next_page_query_obj", {}
            ).format(
                items_per_page=items_per_page,
                page=page,
                skip=items_per_page * (page - 1),
            )
            pagination_params = ast.literal_eval(pagination_params_str)
        except TypeError:
            pagination_params = {}

        try:
            # Count
            if count:
                logger.info("Sending count request with `sentinelsat`")
                total_count = self.api.count(**query_params)
            else:
                total_count = None

            # Query
            query_params.update(pagination_params)
            logger.info("Sending query request with `sentinelsat`")
            results = self.api.query(**query_params)

            # Create the storage_status field
            for uuid, res in results.items():
                res["storage_status"] = self.api.is_online(uuid)

            # Normalize results skeletons (using providers.yml file)
            eo_products = self._normalize_results(results.values(), **kwargs)

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

        except ServerError as ex:
            """
            SentinelAPIError -- the parent, catch-all exception. Only used when no other more specific exception
                                can be applied.
            SentinelAPILTAError -- raised when retrieving a product from the Long Term Archive.
            ServerError -- raised when the server responded in an unexpected manner, typically due to undergoing
                            maintenance.
            UnauthorizedError -- raised when attempting to retrieve a product with incorrect credentials.
            QuerySyntaxError -- raised when the query string could not be parsed on the server side.
            QueryLengthError -- raised when the query string length was excessively long.
            InvalidKeyError -- raised when product with given key was not found on the server.
            InvalidChecksumError -- MD5 checksum of a local file does not match the one from the server.
            """
            raise RequestError(ex) from ex

        return eo_products, total_count

    def _normalize_results(self, results, **kwargs):
        """Extend the base QueryStringSearch.normalize_results method.

        Convert Python date/datetime objects returned by sentinelsat into their ISO format.
        """
        products = super().normalize_results(results, **kwargs)
        for product in products:
            for pname, pvalue in product.properties.items():
                if isinstance(pvalue, (date, datetime)):
                    product.properties[pname] = pvalue.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return products

    def _prepare_downloads(self, search_result, **kwargs):
        """Prepare the downloads.

        Create a product manager per product to download, that is responsible
        for creating a file path and a record filename by calling
        ``eodag.plugins.download.base.Download._prepare_download``,
        which allows to check whether this product has already been downloaded or not.
        """
        prepared = []
        for product in search_result:
            pm = _ProductManager(uuid=product.properties["uuid"], product=product)
            pm.fs_path, pm.record_filename = self._prepare_download(product, **kwargs)
            # Do not try to download this product
            if not pm.fs_path or not pm.record_filename:
                if pm.fs_path:
                    product.location = path_to_uri(pm.fs_path)
                pm.to_download = False
            else:
                pm.to_download = True

            prepared.append(pm)
        return prepared

    def _finalize_downloads(self, product_managers, **kwargs):
        """Finalize the downloads.

        Return the paths to the downloaded products. It:
        * can return a path  of product that was already downloaded
          (e.g. ``download_all`` was called on a list of products already partially
          downloaded).
        * By calling ``eodag.plugins.download.base.Download._prepare_download`` it
          takes care of extracting the products if required.
        * It also saves a record file by downloaded product to check later if it needs
          to be downloaded again.
        * It updates product.location
        """
        product_paths = []
        for pm in product_managers:
            # fs_path is obtained from _prepare_download which can return None
            if pm.to_download is False and pm.fs_path is not None:
                product_path = pm.fs_path
            elif pm.downloaded_by_sentinelsat:
                # Save the record file for this product, to detect later in another session
                # if it has already been downloaded or not.
                with open(pm.record_filename, "w") as fh:
                    fh.write(pm.product.remote_location)
                logger.debug("Download recorded in %s", pm.record_filename)
                # Call _finalize to extract the product if required and return the right path.
                product_path = self._finalize(pm.fs_path, **kwargs)
                # Update the product.location to the product's filepath URI (file://...)
                pm.product.location = path_to_uri(product_path)
            else:
                product_path = None
            if product_path is not None:
                product_paths.append(product_path)
        return product_paths

    def download(
        self,
        product,
        auth=None,
        progress_callback=None,
        wait=DEFAULT_DOWNLOAD_WAIT,
        timeout=DEFAULT_DOWNLOAD_TIMEOUT,
        **kwargs
    ) -> str:
        """
        Download product.

        :param product: (EOProduct) EOProduct
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param wait: If download fails, wait time in minutes between two download tries
        :type wait: int, optional
        :param timeout: If download fails, maximum time in minutes before stop retrying
            to download
        :type timeout: int, optional
        :param dict kwargs: ``outputs_prefix`` (str), ``extract`` (bool)  can be provided
                            here and will override any other values defined in a
                            configuration file or with environment variables.
                            ``checksum``, ``max_attempts``, ``n_concurrent_dl``, ``fail_fast``
                            and ``node_filter`` can be passed to ``sentinelsat.download_all`` directly
                            which is used under the hood.
        :returns: The absolute path to the downloaded product in the local filesystem
        :rtype: str
        """
        fs_paths = self.download_all(
            SearchResult([product]),
            auth=auth,
            progress_callback=progress_callback,
            wait=wait,
            timeout=timeout,
            **kwargs
        )

        if len(fs_paths) > 0:
            return fs_paths[0]
        else:
            raise NotAvailableError(
                "%s is not available (%s) and could not be downloaded, timeout reached"
                % (product.properties["title"], product.properties["storageStatus"])
            )

    def download_all(
        self,
        search_result,
        auth=None,
        progress_callback=None,
        wait=DEFAULT_DOWNLOAD_WAIT,
        timeout=DEFAULT_DOWNLOAD_TIMEOUT,
        **kwargs
    ) -> list:
        """
        Download all products.

        :param search_result: A collection of EO products resulting from a search
        :type search_result: :class:`~eodag.api.search_result.SearchResult`
        :param auth: Not used, just here for compatibility reasons
        :param progress_callback: Not used, just here for compatibility reasons
        :param wait: If download fails, wait time in minutes between two download tries
        :type wait: int, optional
        :param timeout: If download fails, maximum time in minutes before stop retrying
            to download
        :type timeout: int, optional
        :param dict kwargs: ``outputs_prefix`` (str), ``extract`` (bool)  can be provided
                            here and will override any other values defined in a
                            configuration file or with environment variables.
                            ``checksum``, ``max_attempts``, ``n_concurrent_dl``, ``fail_fast``
                            and ``node_filter`` can be passed to ``sentinelsat.download_all`` directly.
        :return: A collection of absolute paths to the downloaded products
        :rtype: list
        """
        # Init Sentinelsat API if needed (connect...)
        self._init_api()

        product_managers = self._prepare_downloads(search_result, **kwargs)
        uuids_to_download = [pm.uuid for pm in product_managers if pm.to_download]

        # If a progress_callback is passed, use its disable attribute.
        # First, backup logging settings, then change them temporally to disable/enable progress bars
        eodag_logging_verbose = eodag_logging.get_logging_verbose()
        eodag_logging_disable_tqdm = eodag_logging.disable_tqdm
        if progress_callback is not None:
            no_progress_bar = getattr(progress_callback, "disable", False)
            if eodag_logging_verbose is None:
                # no logging but still displays progress bars by default
                eodag_logging_verbose = 1
            eodag_logging.setup_logging(
                verbose=eodag_logging_verbose, no_progress_bar=no_progress_bar
            )

        if uuids_to_download:
            outputs_prefix = kwargs.get("outputs_prefix") or self.config.outputs_prefix
            sentinelsat_kwargs = {
                k: kwargs.pop(k)
                for k in list(kwargs)
                if k
                in [
                    "max_attempts",
                    "checksum",
                    "n_concurrent_dl",
                    "fail_fast",
                    "nodefilter",
                ]
            }

            if progress_callback is None:
                create_sentinelsat_pbar = ProgressCallback
            else:
                create_sentinelsat_pbar = progress_callback.copy

            # Use eodag progress bars and avoid duplicates
            self.api.pbar_count = 0

            def _tqdm(self, **kwargs):
                """sentinelsat progressbar wrapper"""
                if self.api.pbar_count == 0 and progress_callback is not None:
                    pbar = progress_callback
                    for k in kwargs.keys():
                        setattr(pbar, k, kwargs[k])
                        pbar.refresh()
                else:
                    pbar = create_sentinelsat_pbar(**kwargs)
                self.api.pbar_count += 1
                return pbar

            self.api.downloader._tqdm = types.MethodType(_tqdm, self.api.downloader)

            # another output for notebooks
            nb_info = NotebookWidgets()

            retry_info = (
                "Will try downloading every %s' for %s' if product is not ONLINE"
                % (wait, timeout)
            )
            logger.info(retry_info)
            logger.info(
                "Once ordered, OFFLINE/LTA product download retries may not be logged"
            )
            nb_info.display_html(retry_info)

            self.api.lta_timeout = timeout * 60

            # Download all products
            # Three dicts returned by sentinelsat.download_all, their key is the uuid:
            # 1. Product information from get_product_info() as well as the path on disk.
            # 2. Product information for products successfully triggered for retrieval
            # from the long term archive but not downloaded.
            # 3. Product information of products where either downloading or triggering failed
            success, _, _ = self.api.download_all(
                uuids_to_download,
                directory_path=outputs_prefix,
                lta_retry_delay=wait * 60,
                **sentinelsat_kwargs
            )

            for pm in product_managers:
                if pm.uuid in success:
                    pm.downloaded_by_sentinelsat = True
                    # EODAG and sentinelsat may have different ways of determining the download
                    # file name. The logic below makes sure that EODAG's way is applied.
                    sentinelsat_path = success[pm.uuid]["path"]
                    if sentinelsat_path != pm.fs_path:
                        logger.debug(
                            "sentinelsat product path (%s) is different from EODAG's (%s),"
                            "file or directory moved to EODAG's path.",
                            sentinelsat_path,
                            pm.fs_path,
                        )
                        shutil.move(sentinelsat_path, pm.fs_path)

        # restore logging settings
        if eodag_logging_verbose is not None:
            eodag_logging.setup_logging(
                verbose=eodag_logging_verbose,
                no_progress_bar=eodag_logging_disable_tqdm,
            )

        paths = self._finalize_downloads(product_managers, **kwargs)
        return paths

    def _init_api(self) -> None:
        """Initialize Sentinelsat API if needed (connection and link)."""
        if not self.api:
            try:
                logger.debug("Initializing Sentinelsat API")
                self.api = SentinelAPI(
                    getattr(self.config, "credentials", {}).get("username", ""),
                    getattr(self.config, "credentials", {}).get("password", ""),
                    self.config.endpoint,
                )
                # Use eodag progress bar which can be globally disabled
                self.api._tqdm = ProgressCallback
            except KeyError as ex:
                raise MisconfiguredError(ex) from ex
        else:
            logger.debug("Sentinelsat API already initialized")

    def _update_keyword(self, **kwargs):
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
                isoparse(qp.pop("start")),
                isoparse(qp.pop("end")),
            )

        # Footprint
        if "area" in qp and isinstance(qp["area"], list):
            qp["area"] = qp["area"][0]

        # id
        if "filename" in qp:
            qp["filename"] = "%s*" % qp["filename"]

        return qp, provider_product_type
