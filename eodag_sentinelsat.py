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

import datetime
import logging
import zipfile

import shapely.wkt
from sentinelsat import SentinelAPI
from shapely import geometry
from tqdm import tqdm

from eodag.api.product import EOProduct
from eodag.api.product.representations import properties_from_json
from eodag.utils.metadata_mapping import get_search_param
from eodag.plugins.apis.base import Api


logger = logging.getLogger('eodag.plugins.apis.sentinelsat')


class SentinelsatAPI(Api):

    def __init__(self, config):
        super(SentinelsatAPI, self).__init__(config)
        self.api = None

    def query(self, product_type, **kwargs):
        self._init_api()
        query_params = self._convert_query_params(kwargs)
        try:
            final = []
            results = self.api.query(
                producttype=self.config['products'][product_type]['product_type'],
                limit=10,
                **query_params)
            if results:
                append_to_final = final.append
                for _id, original in results.items():
                    original['footprint'] = shapely.wkt.loads(original['footprint'])
                    original['beginposition'] = original['beginposition'].isoformat()
                    original['endposition'] = original['endposition'].isoformat()
                    append_to_final(EOProduct(
                        product_type,
                        self.instance_name,
                        original['link'],
                        properties_from_json(original, self.config['metadata_mapping']),
                        searched_bbox=kwargs.get('geometry')
                    ))
            return final
        except TypeError:
            import traceback as tb
            # Sentinelsat api query method raises a TypeError for finding None in the json feed received as a response
            # from the sentinel server, when looking for 'opensearch:totalResults' key. This may be interpreted as the
            # the api not finding any result from the query. This is what is assumed here.
            logger.debug('Something went wrong during the query with self.api api:\n %s', tb.format_exc())
            logger.info('No results found !')
            return []

    def download(self, product, auth=None):
        self._init_api()
        if self.config['on_site']:
            data = self.api.get_product_odata(product.properties['id'], full=True)
            logger.info('Product already present on this platform. Identifier: %s', data['Identifier'])
            return data['Identifier']
        else:
            product_info = self.api.download_all(
                [product.properties['id']],
                directory_path=self.config['outputs_prefix']
            )
            product_info = product_info[0][product.properties['id']]

            if self.config['extract'] and product_info['path'].endswith('.zip'):
                logger.info('Extraction activated')
                with zipfile.ZipFile(product_info['path'], 'r') as zfile:
                    fileinfos = zfile.infolist()
                    with tqdm(fileinfos, unit='file', desc='Extracting files from {}'.format(
                            product_info['path'])) as progressbar:
                        for fileinfo in progressbar:
                            zfile.extract(fileinfo, path=self.config['outputs_prefix'])
                return product_info['path'][:product_info['path'].index('.zip')]
            else:
                return product_info['path']

    def _init_api(self):
        if not self.api:
            logger.debug('Initialising sentinelsat api')
            self.api = SentinelAPI(
                self.config['credentials']['username'],
                self.config['credentials']['password'],
                self.config['endpoint']
            )
        else:
            logger.debug('Sentinelsat api already initialized')

    def _convert_query_params(self, params):
        area_param = get_search_param(self.config['metadata_mapping']['geometry'])
        cloud_cover_param = get_search_param(self.config['metadata_mapping']['cloudCover'])
        start_date_param = get_search_param(self.config['metadata_mapping']['startTimeFromAscendingNode'])
        query = {}
        if params.get('geometry'):
            footprint = params['geometry']
            box_values = (footprint['lonmin'], footprint['latmin'], footprint['lonmax'], footprint['latmax'])
            query[area_param] = geometry.box(*box_values).to_wkt()
        if params.get('cloudCover'):
            query[cloud_cover_param] = (0, params['cloudCover'])
        if params.get('startTimeFromAscendingNode') and params.get('completionTimeFromAscendingNode'):
            def handle_date(date):
                if any(isinstance(date, klass) for klass in (datetime.datetime, datetime.date)):
                    return date.strftime('%Y%m%d')
                return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')

            query[start_date_param] = (
                handle_date(params['startTimeFromAscendingNode']),
                handle_date(params['completionTimeFromAscendingNode'])
            )
        return query
