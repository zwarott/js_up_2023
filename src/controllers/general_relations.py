import zipfile
from datetime import datetime

import geopandas as gpd

from src.models.output_tables import js_tables, mandatory_tables


def shps_in_zip(zip_dir: str, mun_code: int) -> set:
    """Return set of shapefile names within zip file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.

    Returns
    -------
    set
        Set of shapefile names within zip file.
    """
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if shp.endswith(".shp")
    )
    return shps_to_check


def unknown_shp(zip_dir: str, mun_code: int) -> list:
    """Return list with unknown shapefiles.

    Check, if all shapefiles that are stored in zip file 
    have the same name as features predefined in js_tables list 
    or start with "X" (non-standardized layer).

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.

    Returns:
    -------
    list
        List of non-standardized shapefiles that do not
        respect naming convention.
    """
    # Create set of shapefiles name only.
    shps_to_check = shps_in_zip(zip_dir, mun_code)
    # If any layers are unknown, put them into the list.
    # Names of all known shapefiles are stored in js_tables from
    # (output_tables.py module).
    unknown_shp = [
        shp for shp in shps_to_check if shp not in js_tables and not shp.startswith("X")
    ]
    return unknown_shp


def mandatory_shp_miss(zip_dir: str, mun_code: int) -> list:
    """Return list with misssing mandatory shapefiles.

    Check, if all mandatory shapefiles are stored in
    zip file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.

    Returns
    -------
    list
        List of missing mandatory shapefiles.
    """
    # Create set of shapefiles name only.
    shps_to_check = shps_in_zip(zip_dir, mun_code)

    # If any layers are missing, put them into the list.
    # Names of mandatory shapefiles are stored in mandatory_tables from
    # (output_tables.py module).
    missing_shp = [shp for shp in mandatory_tables if shp not in shps_to_check]
    return missing_shp


def mandatory_shp_empty(zip_dir: str, mun_code: int) -> list:
    """Return list of empty mandatory shapefiles.

    Check, if there are any empty mandatory layers in
    zip file.

    Parameters:
    -----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.

    Returns
    -------
    list
        List of empty mandatory shapefiles.
    """
    # List for empty mandatory shapefiles.
    empty_mandatory_shp = []
    # Run this function only, if no mandatory shapefie is missing.
    if len(mandatory_shp_miss(zip_dir, mun_code)) == 0:
        for shp in mandatory_tables:
            if (
                gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                ).empty
                is True
            ):
                empty_mandatory_shp.append(shp)
    else:
        pass

    return empty_mandatory_shp


def shp_info_standardized(zip_dir: str, mun_code: int) -> None:
    """Print overview about standardized layers in zip file.

    Check, if standardized shapefiles within zip file are empty
    and if all mandatory shapefiles are included.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.
    """
    # Create timestamp in format YYYY-MM-DD HH:MM:SS.
    time_info = datetime.today().isoformat(sep=" ", timespec="seconds")
    print(
        "\n",
        f"Importing spatial plan of municipality with code {mun_code} started at {time_info}.",
        sep="\n",
        end="\n" * 2,
    )
    print(" Checking standardized layers ".center(60, "-"), end="\n" * 2)
    # Create set of shapefile names in zipped file.
    shps_to_check = shps_in_zip(zip_dir, mun_code)
    # Crate list of missing standardized shapefiles.
    miss_stand_shp = [shp for shp in js_tables if shp not in shps_to_check]

    # Check each shapefile:
    for shp in shps_to_check:
        #1: If standardized shapefile is included and not empty.
        if (
            shp in js_tables 
            and shp not in miss_stand_shp
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            is False
        ):
            # Number of features in certain shapefile.
            geom_number = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).geometry.count()
            print(f"Ok: {shp} layer is included ({geom_number}).")
        #2: If standardized mandatory shapefile is included, but empty.
        elif (
            shp in js_tables 
            and shp in mandatory_tables
            and shp not in miss_stand_shp 
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is True:
            print(f"Error: {shp} layer is inculded, but empty.")
        #3: If standardized non-mandatory shapefile is included, but empty,
        elif (
            shp in js_tables
            and shp not in mandatory_tables
            and shp not in miss_stand_shp 
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is True:
            print(f"Warning: {shp} layer is inculded, but empty.")
        #4: If standardized mandatory shapefile is not included.
        elif (
            shp in js_tables
            and shp in mandatory_tables
            and shp in miss_stand_shp
            ):
            print(f"Error: {shp} is not included.")
        #5: If standardized non-mandatory shapefile is not included.
        elif (
            shp in js_tables
            and shp not in mandatory_tables
            and shp in miss_stand_shp
            ):
            print(f"Warning: {shp} layer is not included.")


def shp_info_non_standardized(zip_dir: str, mun_code: int) -> None:
    """Print overview about non-standardized layers in zip file.

    Check, if non-standardized shapefiles within zip file are empty
    and if these shapefiles respect naming convention.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.
    """
    print(" Checking non-standardized layers ".center(60, "-"), end="\n" * 2)
    # Create set of shapefile names in zipped file.
    shps_to_check = shps_in_zip(zip_dir, mun_code)
    nstand_shps = [
        shp for shp in shps_to_check if shp not in js_tables
    ]
    # Create list of non-standardized shapefiles that do not respect naming convention.
    wrong_nstand_shp = unknown_shp(zip_dir, mun_code)
    # Crete list of non-standardized shapefiles that respect naming convention
    ok_nstand_shp = [
        shp for shp in nstand_shps if shp.startswith("X")
    ] 

    # Check each shapefile:
    for shp in nstand_shps:
        #1: If non-standardized shapefile respects naming convention and is not empty.
        if (
            shp in ok_nstand_shp
            and shp not in wrong_nstand_shp
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is False:
            print(
            f"Ok: {shp} is included.",
            end="\n" * 2)
        #2: If non-standardized shapefile respects naming convention, but is empty.
        elif (
            shp in ok_nstand_shp
            and shp not in wrong_nstand_shp
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is True:
            print(
            f"Warning: {shp} is included, but empty.",
            end="\n" * 2)
        #3: If non-standardized shapefile is included (is not empty), but does not respect naming convention.
        elif (
            shp not in ok_nstand_shp
            and shp in wrong_nstand_shp 
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            ) is False:
            print(
            f"Warning: {shp} is included, but does not respect naming convention.",
            end="\n" * 2)
        #4: If non-standardized shapefile is included, does not respect naming convention and is empty.
        elif (
            shp not in ok_nstand_shp
            and shp in wrong_nstand_shp 
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            ) is True:
            print(
            f"Warning: {shp} does not respect naming convention and is empty.",
            end="\n" * 2)
        else:
            pass
