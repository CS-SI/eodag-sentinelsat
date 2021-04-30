import datetime
import hashlib
import os
import shutil
import time
from pathlib import Path

import pytest
from eodag import EODataAccessGateway
from eodag.api.search_result import SearchResult
from eodag.utils import uri_to_path


@pytest.fixture
def dag(download_dir):
    dag = EODataAccessGateway()
    dag.set_preferred_provider("scihub")
    dag.providers_config["scihub"].api.outputs_prefix = str(download_dir)

    yield dag

    for p in download_dir.glob("**/*"):
        try:
            os.remove(p)
        except OSError:
            shutil.rmtree(p)


@pytest.mark.endtoend
@pytest.mark.usefixtures("logging_info")
def test_end_to_end_complete_scihub(dag, download_dir):
    """Complete end-to-end test with SCIHUB for search, download and download_all"""
    # Search for products that are ONLINE and as small as possible
    today = datetime.date.today()
    month_span = datetime.timedelta(weeks=4)
    search_results, _ = dag.search(
        productType="S2_MSI_L1C",
        start=(today - month_span).isoformat(),
        end=today.isoformat(),
        geom={"lonmin": 1, "latmin": 42, "lonmax": 5, "latmax": 46},
        items_per_page=100,
    )
    assert len(search_results) > 0
    prods_sorted_by_size = SearchResult(
        sorted(search_results, key=lambda p: float(p.properties["size"].split()[0]))
    )
    prods_online = [
        p for p in prods_sorted_by_size if p.properties["storageStatus"] == "ONLINE"
    ]
    if len(prods_online) < 2:
        pytest.skip("Not enough ONLINE products found, update the search criteria.")

    # Retrieve one product to work with
    product = prods_online[0]

    prev_remote_location = product.remote_location
    prev_location = product.location
    # The expected product's archive filename is based on the product's title
    expected_product_name = f"{product.properties['title']}.zip"

    # Download the product, but DON'T extract it
    archive_file_path = dag.download(product, extract=False)

    # The archive must have been downloaded
    assert os.path.isfile(archive_file_path)
    # Its name must be the "{product_title}.zip"
    assert expected_product_name in os.listdir(product.downloader.config.outputs_prefix)
    # Its size should be >= 5 KB
    archive_size = os.stat(archive_file_path).st_size
    assert archive_size >= 5 * 2 ** 10
    # The product remote_location should be the same
    assert prev_remote_location == product.remote_location
    # However its location should have been update
    assert prev_location != product.location
    # The location must follow the file URI scheme
    assert product.location.startswith("file://")
    # That points to the downloaded archive
    uri_to_path(product.location) == archive_file_path
    # A .downloaded folder must have been created
    record_dir = download_dir / ".downloaded"
    assert record_dir.is_dir()
    # It must contain a file per product downloade, whose name is
    # the MD5 hash of the product's remote location
    expected_hash = hashlib.md5(product.remote_location.encode("utf-8")).hexdigest()
    record_file = record_dir / expected_hash
    assert record_file.is_file()
    # Its content must be the product's remote location
    record_content = record_file.read_text()
    assert record_content == product.remote_location

    # The product should not be downloaded again if the download method
    # is executed again
    previous_archive_file_path = archive_file_path
    previous_location = product.location
    start_time = time.time()
    archive_file_path = dag.download(product, extract=False)
    end_time = time.time()
    assert (end_time - start_time) < 2  # Should be really fast (< 2s)
    # The paths should be the same as before
    assert archive_file_path == previous_archive_file_path
    assert product.location == previous_location

    # If we emulate that the product has just been found, it should not
    # be downloaded again since the record file is still present.
    product.location = product.remote_location
    # Pretty much the same checks as with the previous step
    previous_archive_file_path = archive_file_path
    start_time = time.time()
    archive_file_path = dag.download(product, extract=False)
    end_time = time.time()
    assert (end_time - start_time) < 2  # Should be really fast (< 2s)
    # The returned path should be the same as before
    assert archive_file_path == previous_archive_file_path
    assert uri_to_path(product.location) == archive_file_path

    # Remove the archive
    os.remove(archive_file_path)

    # Now, the archive is removed but its associated record file
    # still exists. Downloading the product again should really
    # download it, if its location points to the remote location.
    # The product should be automatically extracted.
    product.location = product.remote_location
    product_dir_path = dag.download(product)

    product_dir_path = Path(product_dir_path)

    # Its size should be >= 5 KB
    downloaded_size = sum(
        f.stat().st_size for f in product_dir_path.glob("**/*") if f.is_file()
    )
    assert downloaded_size >= 5 * 2 ** 10
    # The product remote_location should be the same
    assert prev_remote_location == product.remote_location
    # However its location should have been update
    assert prev_location != product.location
    # The location must follow the file URI scheme
    assert product.location.startswith("file://")
    # The location must point to a SAFE directory
    assert product.location.endswith("SAFE")
    # The path must point to a SAFE directory
    assert product_dir_path.is_dir()
    assert str(product_dir_path).endswith("SAFE")

    # Remove the archive and extracted product and reset the product's location
    os.remove(archive_file_path)
    shutil.rmtree(product_dir_path.parent)
    product.location = product.remote_location

    # Now let's check download_all
    products = prods_sorted_by_size[:2]
    # Pass a copy because download_all empties the list
    archive_paths = dag.download_all(products, extract=False)

    # The returned paths must point to the downloaded archives
    # Each product's location must be a URI path to the archive
    for product, archive_path in zip(products, archive_paths):
        assert os.path.isfile(archive_path)
        assert uri_to_path(product.location) == archive_path

    # Downloading the product again should not download them, since
    # they are all already there.
    prev_archive_paths = archive_paths
    start_time = time.time()
    archive_paths = dag.download_all(products, extract=False)
    end_time = time.time()
    assert (end_time - start_time) < 2  # Should be really fast (< 2s)
    assert archive_paths == prev_archive_paths
