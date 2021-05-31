import datetime

import pytest
import shapely.wkt
from eodag import EODataAccessGateway, setup_logging
from eodag.config import load_default_config
from eodag.plugins.manager import PluginManager
from eodag.utils import ProgressCallback


@pytest.fixture
def dag():
    dag = EODataAccessGateway()
    dag.set_preferred_provider("scihub")

    yield dag


@pytest.fixture
def plugin_api():
    providers_config = load_default_config()
    plugins_manager = PluginManager(providers_config)

    yield next(plugins_manager.get_search_plugins(provider="scihub"))


@pytest.mark.usefixtures("logging_info")
def test_conf_provider(dag):
    """Check that provider configuration is loaded in eodag"""

    assert "scihub" in dag.providers_config.keys()
    assert hasattr(dag.providers_config["scihub"], "api")
    assert hasattr(dag.providers_config["scihub"].api, "type")
    assert dag.providers_config["scihub"].api.type == "SentinelsatAPI"
    assert hasattr(dag.providers_config["scihub"], "products")
    assert len(dag.providers_config["scihub"].products) > 0


@pytest.mark.usefixtures("logging_info")
def test_update_keyword(dag, plugin_api):
    """Check that query args are correctly set for sentinelsat api"""

    geometry = shapely.wkt.loads(
        "POLYGON ((1.23 43.42, 1.23 43.76, 1.68 43.76, 1.68 43.42, 1.23 43.42))"
    )

    parameters, provider_product_type = plugin_api._update_keyword(
        startTimeFromAscendingNode="2020-05-01",
        completionTimeFromAscendingNode="2020-05-02T15:00:00Z",
        geometry=geometry,
        productType="S2_MSI_L1C",
    )
    assert isinstance(parameters["area"], str)
    assert isinstance(
        shapely.wkt.loads(parameters["area"]), shapely.geometry.polygon.Polygon
    )
    start, end = parameters["date"]
    assert isinstance(start, datetime.datetime)
    assert isinstance(end, datetime.datetime)

    assert parameters["producttype"] == provider_product_type
    assert (
        parameters["producttype"]
        == dag.providers_config["scihub"].products["S2_MSI_L1C"]["productType"]
    )
    assert (
        parameters["platformname"]
        == dag.providers_config["scihub"].products["S2_MSI_L1C"]["platform"]
    )


@pytest.mark.usefixtures("logging_info")
def test_progress_bar(plugin_api):
    """Check that eodag progress bar settings are correctly passed to sentinelsat"""

    plugin_api.config.credentials = {"username": "", "password": ""}
    plugin_api._init_api()

    assert isinstance(plugin_api.api._tqdm(), ProgressCallback)
    assert plugin_api.api._tqdm().disable is False

    setup_logging(2, no_progress_bar=True)
    assert plugin_api.api._tqdm().disable is True
