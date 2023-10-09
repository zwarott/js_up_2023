import zipfile
from time import time

import geopandas as gpd

from src.models.attributes import attributes, attribute_types


def mandatory_attrs_exist(zip_dir: str, mun_code: int) -> None:
    """Check existence of mandatory attributes.

    Check, if all mandatory attributes within
    each shapefile exist.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if shp.endswith(".shp")
    )
    # For each shapefile:
    for shp in shps_to_check:
        # Create GeoDataFrame.
        shp_gdf = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Create list of attribute names.
        attrs_to_check = shp_gdf.columns.tolist()
        # Create list of attribute names that are specified in attributes
        # dictionary (attributes.py module).
        included = [
            attr.lower()
            for attr in attrs_to_check
            if attr.lower() in attributes[shp.lower()]
        ]
        # Crete set of attributes that are missing.
        # Set was created using difference method (mandatory - included).
        missing = set(attributes[shp.lower()]).difference(set(included))
        # If all mandatory attributes are include.
        if len(missing) == 0:
            print(f"All mandatory attributes in '{shp}.shp' are included.")
        # If any mandatory attribute is missing.
        elif len(missing) > 0:
            for attr in missing:
                print(f"'{attr}' attribute in '{shp}.shp' is missing.")
    duration = time() - start_time
    separator = "-" * 150
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def mandatory_attrs_type(zip_dir: str, mun_code: int) -> None:
    """Check for correct attribute types.

    Check, if all mandatory attributes within
    each shapefile has correct data type.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """

    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if shp.endswith(".shp")
    )
    # For each shapefile:
    for shp in shps_to_check:
        # Create GeoDataFrame.
        shp_gdf = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Create list of attribute names.
        attrs_to_check = shp_gdf.columns.tolist()
        # Create list of attribute names that are specified in attributes
        # dictionary (attributes.py module).
        included = [
            attr for attr in attrs_to_check if attr.lower() in attributes[shp.lower()]
        ]
        # For each included attribute:
        for attr in included:
            # If type of included attribute is equal to mandatory attribute type.
            if shp_gdf[attr].dtype == attribute_types[shp.lower()][attr.lower()]:
                print(
                    f"Ok: '{attr.lower()}' attribute in '{shp}.shp' has correct type."
                )
            # If not.
            else:
                print(
                    f"Error: '{attr.lower()}' attribute in '{shp}.shp' has not correct type."
                )
    duration = time() - start_time
    separator = "-" * 150
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")
