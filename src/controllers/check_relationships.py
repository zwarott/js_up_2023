import zipfile
from datetime import datetime
import warnings

import geopandas as gpd
from numpy import empty
from shapely.geometry import Polygon

from src.models.output_tables import js_tables, mandatory_tables
from src.controllers.check_geometry import validity_shp_zip 


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
            print(f"Ok: {shp} layer is included. Number of features: {geom_number}.")
        #2: If standardized mandatory shapefile is included and empty.
        elif (
            shp in js_tables 
            and shp in mandatory_tables
            and shp not in miss_stand_shp 
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is True:
            print(f"Error: {shp} layer is inculded, but empty.")
        #3: If standardized non-mandatory shapefile is included and empty,
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
    print("Checking non-standardized layers ".center(60, "-"), end="\n" * 2)
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
        #2: If non-standardized shapefile respects naming convention and is empty.
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


def shp_within_mun(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export: bool = False,
) -> int:
    """Checking shapefile within ReseneUzemi_p shapefile.

    Check, if shapefile is within ReseneUzemi_p shapefile.
    If not, create difference of certain shapefile and ReseneUzemi_p
    shapefile and if needed, export these as new shapefile. Returns
    number of geometries that are not within ReseneUzemi_p.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
        A unique code of particular municipality, for which
        are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export : bool
        A boolean value for exporting area differences between
        ReseneUzemi_p shapefile and certain shapefile (shp parameter). 
        Default value is set up as False (for not exporting these 
        differences). For exporting these differences, put True.

    Returns
    -------
    int
        Number of geometries that are not within ReseneUzemi_p.
    """
    # Checking process announcement title.
    # List for geometry rows.
    geom_out = []
    try:
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            # Certain shapefile.
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp",
            )
            # Create GeoDataFrame from ReseneUzemi_p shapefile.
            mun_borders_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ReseneUzemi_p.shp",
            )
            # Create Polygon geometry from GeoDataFrame coordinates.
            borders_polygon = Polygon(mun_borders_gdf.get_coordinates())
            # List for informations about each row.
            info_col_out = []
            # Column's name and records (row).
            info_col = {"info": info_col_out}

            # For each row (index number) in all geometries (count) find out,
            # which are not within ReseneUzemi_p.
            for i in range(shp_gdf.geometry.count()):
                # If geometry is not within ReseneUzemi_p.
                if shp_gdf.geometry[i].within(borders_polygon) is False:
                    # Append info from the first column to info_col_out list.
                    info_col_out.append(shp_gdf.iloc[:, 0][i])
                    # Append geometry parts that lay outside ReseneUzemi_p into geom_out list.
                    geom_out.append(shp_gdf.geometry[i].difference(borders_polygon))
                # If this geometry is within ReseneUzemi_p, pass.
                else:
                    pass
            # If all geometries are within ReseneUzemi_p.
            if len(geom_out) == 0:
                print(
                    f"Ok: All geometries are within ReseneUzemi_p.",
                    end="\n" * 2
                )
            # If there are some geometries outside, do:
            elif len(geom_out) > 0 and export is True:
                # Filter only polygon geometry type.
                poly_geom = [geom for geom in geom_out if geom.geom_type in ("Polygon", "Multipolygon")]
                # Converts these geometries into Geoseries.
                geom_out_col = gpd.GeoSeries(data=poly_geom, crs="EPSG:5514")
                # Then create GeoDataFrame (from info list and Geoseries).
                gdf_outside = gpd.GeoDataFrame(
                    data=info_col, geometry=geom_out_col, crs="EPSG:5514"
                )
                # Export this GeoDataFrame as shapefile.
                gdf_outside.to_file(
                    f"{dest_dir_path}/{shp.lower()}_outside.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                # Print number of geometries that are not within ReseneUzemi_p.
                print(
                    f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}).",
                    f"       - These parts were saved as {shp.lower()}_outside.shp.",
                    end="\n" * 2
                )
            # If export = False, print number of features outside only.
            else:
                print(
                    f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}).", 
                    end="\n" * 2
                )
        else:
            print("Error: Checking features within ReseneUzemi_p cannot be run due to invalid geometries.",
                  end="\n" * 2)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(geom_out) 


def covered_mun_both(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
) -> int:
    """Checking covering whole ReseneUzemi_p area.

    Check, if whole ReseneUzemi_p shapefile is covered by PlochyRZV_p and
    KoridoryP_p shapefiles. Returns number of geometries that do not cover
    ReseneUzemi_p.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    export : bool
       A boolean value for exporting area differences between ReseneUzemi_p
       shapefile and merged PlochyRZV_p and KoridoryP_p layers. Default value
       is set up as False (for not exporting these differences). For exporting
       these differences, put True.

    Returns
    -------
    int
        Number of geometries that do not cover ReseneUzemi_p.
    """
    try:
        errors = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "KoridoryP_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "ReseneUzemi_p") == 0
        ):
            plochy_rzv = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Create GeoDataFrame from ReseneUzemi_p.shp.
            resene_uzemi = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ReseneUzemi_p.shp"
            )
            # Create shapely geometry (polygon) from geodataframe coordinates.
            resene_uzemi_geom = Polygon(resene_uzemi.get_coordinates())
            koridory_p = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/KoridoryP_p.shp"
            )
            # Merge KoridoryP_p and PlochyRZV_p GeoDataFrames.
            merged = plochy_rzv.sjoin(koridory_p)
            # Dissolve merged GeoDataFrames.
            dissolved = merged.dissolve()
            # Dissolved PlochyRZV_p GeoDataFrame.
            diff = resene_uzemi_geom.difference(dissolved.geometry)
            # Create singleparts from diff.
            diff["singleparts"] = [p for p in diff]
            # Export diff geometries.
            diff_geom = diff["singleparts"]
            # Create new geodataframe from diff_geom.
            gdf_diff = gpd.GeoDataFrame(geometry=diff_geom, crs="EPSG:5514")
            # Explode multiparts geometries into single geometries (list to
            # rows).
            exploded = gdf_diff.explode(index_parts=False)
            # If there is no differences, print statement only.
            if diff is None:
                print(
                    f"Ok: All geometries from PlochyRZV_p and KoridoryP_p cover ReseneUzemi_p.",
                    end="\n" * 2
                )
            # If there are some differences and export = True, export them
            # as shapefile and print statements about differences.
            if diff is not None and export is True:
                exploded.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )

                print(
                    f"Error: ReseneUzemi_p is not fully covered by geometries from PlochyRZV_p and KoridoryP_p.",
                    f"       - Number of features not covering ReseneUzemi_p: {len(exploded.geometry)}.",
                    f"       - These part were saved as not_cover_reseneuzemi_p.shp",
                    end="\n" * 2,
                )
                errors += 1
            # If export = False, print info about differences only.
            else:
                print(
                    f"Error: ReseneUzemi_p is not fully covered by geometries from PlochyRZV_p and KoridoryP_p.",
                    f"       - Number of features not covering ReseneUzemi_p: {len(exploded.geometry)}.",
                    end="\n" * 2,
                )
                errors += 1
        else:
            print("Error: Checking covering ReseneUzemi_p by PlochyRZV_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2)
            errors += 1
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors 


def covered_mun_przv(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
    ) -> int: 
    """Checking covering ReseneUzemi_p by PlochyRZV_p.

    Check, if ReseneUzemi_p is fully covevered by PlochyRZV_p.
    This function is executed when KoridoryP_p is missing.
    
    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    export : bool
       A boolean value for exporting area differences between ReseneUzemi_p
       shapefile and geometries from PlochyRZV_p that do not cover
       ReseneUzemi_p. Default value is set up as False (for not exporting 
       these differences). For exporting these differences, put True.
    
    Returns
    -------
    int
        Number of geometries that do not cover ReseneUzemi_p.
    """
    try:
        errors = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "ReseneUzemi_p") == 0
        ):
            # Create GeoDataFrame from PlochyRZV_p.
            plochy_rzv = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Create GeoDataFrame from ReseneUzemi_p.shp.
            resene_uzemi = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ReseneUzemi_p.shp"
            )
            # Create shapely geometry (polygon) from geodataframe coordinates.
            resene_uzemi_geom = Polygon(resene_uzemi.get_coordinates())
            # Dissolved PlochyRZV_p GeoDataFrame.
            dissolved = plochy_rzv.dissolve()
            # Difference bewtween ReseneUzemi_p and dissolved GeoDataFrame.
            diff = resene_uzemi_geom.difference(dissolved.geometry)
            # Create singleparts from diff.
            diff["singleparts"] = [p for p in diff]
            # Export diff geometries.
            diff_geom = diff["singleparts"]
            # Create new geodataframe from diff_geom.
            gdf_diff = gpd.GeoDataFrame(geometry=diff_geom, crs="EPSG:5514")
            # Explode multiparts geometries into single geometries (list to
            # rows).
            exploded = gdf_diff.explode(index_parts=False)
            # If there is no differences, print statement only.
            if diff is None:
                print(
                    "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                    "Ok: All geometries in PlochyRZV_p cover ReseneUzemi_p.",
                    end="\n" * 2,
                )
            # If there are some differences and export = True, export them
            # as shapefile and print statements about differences.
            if diff is not None and export is True:
                exploded.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="5514",
                )
                errors += 1

                print(
                    "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                    "Error: ReseneUzemi_p is not fully covered by geometries from PlochyRZV_p.",
                    f"       - Number of features not covering ReseneUzemi_p: {len(exploded.geometry)}.",
                    "       - These parts were saved as 'not_cover_reseneuzemi_p.shp'",
                    end="\n" * 2,
                )
            # If export = false, print info about differences only.
            else:
                print(
                    "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                    "Error: ReseneUzemi_p is not fully covered by geoemtries from PlochyRZV_p.",
                    f"      - Number of features not covering ReseneUzemi_p: {len(exploded.geometry)}.",
                    end="\n" * 2,
                )
                errors += 1
        else:
            print("Error: Checking covering ReseneUzemi_p by PlochyRZV_p cannot be run due to invalid geometries.",
                  end="\n" * 2)
            errors += 1

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors 


def check_gaps(
    zip_dir: str, dest_dir_path: str, mun_code: int, shp: str, export: bool = False
) -> int:
    """Checking gaps within certain shapefile.

    Check gaps between polygons within certain shapefile stored in
    zip file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be gaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export : bool
       A boolean value for exporting gaps within certain shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.
    
    Returns
    -------
    int
        Number of gaps within certain shapefile.
    """

    # Errors variable is defined, because I can get None type and I do not
    # run len() function on None type.
    errors = 0
    try:
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            )
            # Dissolve all rows (polygons) into one.
            dissolved = shp_gdf.dissolve()
            # Ignore UserWarning.
            warnings.filterwarnings("ignore", "Only Polygon objects", UserWarning)
            # Create list of interior geometries, if exist.
            # interiors method creates Series of list representing the inner rings
            # of each polygon in the GeoSeries. tolist() method converts Series into
            # list. We need specify 0 index, because we have these inner rings already
            # listed. See interiors and tolist() method for more info.
            interior = dissolved.geometry.interiors.tolist()[0]
            # Print statement for shapefiles without inner rings.
            if interior is None or len(interior) == 0:
                print(f"Ok: There are no gaps.",
                      end="\n" * 2
                      )
            # If there are some inner rings, exported them as shapefile and print
            # number of inner rings and where these inner rings are stored.
            elif len(interior) > 0 and export is True:
                errors += 1
                gaps_polygons = [Polygon(a) for a in interior]
                interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="EPSG:5514")
                interior_gdf = gpd.GeoDataFrame(geometry=interior_geom, crs="EPSG:5514")
                interior_gdf.to_file(
                    f"{dest_dir_path}/{shp.lower()}_gaps.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                print(
                    f"Error: There are gaps ({len(interior)}).",
                    f"       - Gaps were saved as {shp.lower()}_gaps.shp.",
                    end="\n" * 2,
                )
            # If export_gaps = False, print only number of inner rings.
            else:
                errors += 1
                print(
                    f"Error: There are gaps ({len(interior)}).",
                    end="\n" * 2
                )
        else:
            print("Error: Checking gaps cannot be run due to invalid geometries.",
                  end="\n" * 2)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors


def check_gaps_covered(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
) -> tuple:
    """Checking gaps between PlochyRZV_p and KoridoryP_p shapefiles.

    Check, if there are any gaps between PlochyRZV_p and
    KoridoryP_p coverings. If shapefile KoridoryP_p is
    not included, function will not run.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be gaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export : bool
       A boolean value for exporting gaps of certain shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.

    Returns
    -------
    tuple
         Tuple of two integers (first position is error, warning).
         If numbers are greater than zero, there are gaps (error)
         or KoridoryP_p shapefile is missing.
    """
    try:
        errors = 0
        warns = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "KoridoryP_p") == 0
        ):
            zip_contents = shps_in_zip(zip_dir, mun_code)
            # Path to PlochyRZV_p.shp.
            plochy_rzv_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Path to KoridoryP_p.shp.
            koridory_p_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/KoridoryP_p.shp"
            )
            # If both shapefiles above are included in zip file and are non-empty,
            # run checking process.
            if (
                "PlochyRZV_p" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and "KoridoryP_p" in zip_contents
                and gpd.read_file(koridory_p_path).empty is False
            ):
                # Create GeoDataFrames from shapefiles above.
                plochy_rzv_gdf = gpd.read_file(plochy_rzv_path)
                koridory_p_gdf = gpd.read_file(koridory_p_path)
                # Dissolve both GeoDataFrames.
                plochy_rzv_diss = plochy_rzv_gdf.dissolve()
                koridory_p_diss = koridory_p_gdf.dissolve()
                # Merge dissolved GeoDataFrames.
                merged = plochy_rzv_diss.sjoin(koridory_p_diss)
                dissolved = merged.dissolve()
                # Create list of interior geometries, if exist.
                # interiors method creates Series of list representing the inner rings
                # of each polygon in the GeoSeries. tolist() method converts Series into
                # list. We need specify 0 index, because we have these inner rings already
                # lited. See interiors and tolist() method for more info.
                interior = dissolved.geometry.interiors.tolist()[0]
                # If there are no inner rings, print info about it only.
                if interior is None or len(interior) == 0:
                    print(
                        "OK: There is no gaps between PlochyRZV_p and KoridoryP_p.",
                        end="\n" * 2,
                    )
                # If there are some inner rings, exported them as shapefile and print
                # number of inner rings and where these inner rings are stored.
                elif len(interior) > 0 and export is True:
                    gaps_polygons = [Polygon(a) for a in interior]
                    interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="EPSG:5514")
                    interior_gdf = gpd.GeoDataFrame(geometry=interior_geom, crs="EPSG:5514")
                    interior_gdf.to_file(
                        f"{dest_dir_path}/plochy_rzv_kordiory_p_gaps.shp",
                        driver="ESRI Shapefile",
                        crs="ESPG:5514",
                    )
                    print(
                        f"Error: There are gaps between PlochyRZV_p and KoridoryP_p {len(interior)}.",
                        f"       - Gaps were exported as plochy_rzv_kordiory_p_gaps.shp.",
                        end="\n" * 2,
                    )
                    errors += 1
                # If export = False, print number of inner rings only.
                else:
                    print(
                        f"Error: There are gaps between PlochyRZV_p and Koridory_p {len(interior)}.",
                        end="\n" * 2
                    )
            # If there is only PlochyRZV_p.
            elif (
                "PlochyRZV_p" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and "KoridoryP_p" not in zip_contents
            ):
                print(
                    "Warning: Gaps between PlochyRZV_p and KoridoryP_p cannot be check due to:",
                    "       - KoridoryP_p is missing.",
                    "       - Gaps in PlochyRZV_p has been already checked within other step.",
                    end="\n" * 2,
                )
                warns += 1

            # If there are both shapefiles, but KoridoryP_p is empty.
            elif (
                "PlochyRZV_p" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and gpd.read_file(koridory_p_path).empty is True
            ):
                print(
                    "Warning: Gaps between PlochyRZV_p and KoridoryP_p cannot be check due to:",
                    "       - KoridoryP_p is empty.",
                    "       - Gaps in PlochyRZV_p has been already checked within other step.",
                    end="\n" * 2,
                )
                warns += 1

            else:
                print(
                    "Error: Gaps between PlochyRZV_p and KoridoryP_p cannot be checked due to:"
                )
                # If KoridoryP_p is misssing.
                if "PlochyRZV_p" not in zip_contents:
                    print("       - PlochyRZV_p is missing.",
                          end="\n" * 2)
                # If KoridoryP_p is empty.
                elif gpd.read_file(plochy_rzv_path).empty is True:
                    print("       - PlochyRZV_p is empty.",
                          end="\n" * 2)
                errors += 1
        else:
            print("Error: Gaps between PlochyRZV_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2)
            errors += 1

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    return errors, warns


def check_overlaps(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export: bool = False,
) -> int:
    """Checking overlaps within certain shapefile (except VpsVpoAs layers).

    Check overlaps between polygons within each shapefile stored in
    zipped file (excepet VpsVpoAs layers, these features can overlap
    each other).

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export : bool
       A boolean value for exporting overlaping geometries of certain
       shapefile. Default value is set up as False (for not exporting
       these overlaping geometries). For exporting overlaps, put True.

    Returns
    -------
    int
        Number of overlaping geometries within certain shapefile.
    """
    try:
        intersected = []
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            )
            # Ignore RuntimeWarning.
            warnings.filterwarnings("ignore", "invalid value encountered", RuntimeWarning)
            # For each geometry check if overlaps other. If so, export this feature
            # into list (overlaping).
            overlaping = []
            for row in shp_gdf.geometry:
                if row.overlaps(shp_gdf.geometry).any():
                    overlaping.append(row)
                else:
                    pass
            # For each overlaping feature stored in list (overlaping) export
            # overlaping parts and store them into list (intersected).
            for part_f in overlaping:
                for sing_f in [oth_f for oth_f in overlaping if oth_f != part_f]:
                    if part_f.overlaps(sing_f):
                        intersected.append(part_f.intersection(sing_f))

            # Create Geoseries from intersected geometries.
            inters_geom = gpd.GeoSeries(intersected)
            # Convert GeometryCollections and Multipolygons into Polygons,
            # Polylines and Points.
            # If index_parts = True, column with index parts will be created.
            geom_exploded = inters_geom.explode(index_parts=True)
            # Filter Polygons only.
            polyg_only = [x for x in geom_exploded if x.geom_type == "Polygon"]
            # If there are no overlaps (polygon parts), print statement.
            if len(polyg_only) == 0:
                print("Ok: There are no overlaps.",
                      end="\n" * 2)
            # If there are overlaps (polygon parts), export them and
            # print their number and where were these geometries stored.
            elif len(polyg_only) > 0 and export is True:
                gdf_overlaps = gpd.GeoDataFrame(geometry=polyg_only, crs="EPSG:5514")
                gdf_overlaps.to_file(
                    f"{dest_dir_path}/{shp.lower()}_overlaps.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                print(
                    f"Error: There are overlaps ({len(polyg_only)}).",
                    f"       - Overlaps were saved as {shp.lower()}_overlaps.shp.",
                    end="\n" * 2,
                )
            # If export_overlaps = export number of oerlaps only.
            else:
                print(
                    f"Error: There are overlaps ({len(polyg_only)}).",
                    end="\n" * 2,
                )
        else:
            print("Error: Checking overlaps cannot be run due to invalid geometries.",
                  end="\n" * 2)

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(intersected)


def overlaps_covered_mun(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
) -> tuple:
    """Checking overlaps between PlochyRZV_p and KoridoryP_p shapefiles.

    Check, if there are any overlaps between PlochyRZV_p and
    KoridoryP_p. If KoridoryP_p is missing, overlaps will
    be not checked, because overlaps in KoridoryP_p will be
    already checked.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    export : bool
       A boolean value for exporting overlaping geometries of certain
       shapefile. Default value is set up as False (for not exporting
       these overlaping geometries). For exporting these overlaps, put True.
    
    Returns
    -------
    tuple
         Tuple of two integers (first position is error, warning).
         If numbers are grater than zero, there are gaps (error)
         or KoridoryP_p shapefile is missing.
    """
    try:
        errors = 0
        warns = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "KoridoryP_p") == 0
        ):
            zip_contents = shps_in_zip(zip_dir, mun_code)
            # Path to PlochyRZV_p shapefile.
            plochy_rzv_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Path to KoridoryP_p shapefile.
            koridory_p_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/KoridoryP_p.shp"
            )
            # If both shapefiles above are included and are not empty.
            if (
                f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and f"DUP_{mun_code}/Data/KoridoryP_p.shp" in zip_contents
                and gpd.read_file(koridory_p_path).empty is False
            ):
                # Create GeoDataFrames from these shapefiles.
                plochy_rzv_gdf = gpd.read_file(plochy_rzv_path)
                koridory_p_gdf = gpd.read_file(koridory_p_path)
                # Dissolve each GeoDataFrame.
                plochy_rzv_diss = plochy_rzv_gdf.dissolve()
                koridory_p_diss = koridory_p_gdf.dissolve()
                # Intersect these dissolved geometries.
                inter = plochy_rzv_diss.geometry.intersection(koridory_p_diss.geometry)
                # Create singleparts from inter.
                inter["singleparts"] = [p for p in inter]
                # Export inter geometries.
                inter_geom = inter["singleparts"]
                # Create new GeoDataFrame from inter_geom.
                gdf_inter = gpd.GeoDataFrame(geometry=inter_geom, crs="EPSG:5514")
                # Explode multiparts geometries into single geometries (list to
                # rows).
                # If index_parts = False, index_parts will be not exported as a
                # new column.
                exploded = gdf_inter.explode(index_parts=False)
                polyg_only = [x for x in exploded if x.geom_type == "Polygon"]
                # If there are not any .
                if len(polyg_only) == 0:
                    print(
                        "Ok: There are no overlaps between PlochyRZV_p and KoridoryP_p.",
                        end="\n" * 2
                    )
                # If there are some intersections and export_inter = True, export them
                # as shapefile and print statements about intersections.
                if len(polyg_only) > 0 and export is True:
                    exploded.to_file(
                        f"{dest_dir_path}/plochy_rzv_koridory_p_overlaps.shp",
                        driver="ESRI Shapefile",
                        crs="ESPG:5514",
                    )
                    print(
                        f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(exploded.geometry)}).",
                        f"      - Overlaps were saved as plochy_rzv_koridory_p_overlaps.shp.",
                        end="\n" * 2,
                    )
                    errors += 1
                # If export_inter = False, print statement about differences.
                else:
                    print(
                        f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(exploded.geometry)}).",
                        end="\n" * 2
                    )
                    errors += 1
            # If non-empty PlochyRZV_p is included and KoridoryP_p is missing.
            elif (
                f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and f"DUP_{mun_code}/Data/KoridoryP_p.shp" not in zip_contents
            ):
                print(
                    "Warning: Gaps between PlochyRZV_p and KoridoryP_p were not checked due to:",
                    "         - KoridoryP_p is missing.",
                    "         - Overlaps in PlochyRZV_p has been already checked within other step.",
                    end="\n" * 2,
                )
                warns += 1
            # If non-empty PlochyRZV_p is included and KoridoryP_p is empty.
            elif (
                f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
                and gpd.read_file(plochy_rzv_path).empty is False
                and gpd.read_file(koridory_p_path).empty is True
            ):
                print(
                    "Warning: Gaps between PlochyRZV_p and KoridoryP_p were not checked due to:",
                    "         - KoridoryP_p is empty.",
                    "         - Overlaps in PlochyRZV_p has been already checked within other step.",
                    end="\n" * 2,
                )
                warns += 1
            else:
                print(
                    "Error: Overlaps between PlochyRZV_p and KoridoryP_p cannot be checked due to:"
                )
                # If PlochyRZV_p is missing.
                if f"DUP_{mun_code}/Data/PlochyRZV_p.shp" not in zip_contents:
                    print("       - PlochyRZV_p is missing.",
                          end="\n" * 2)
                # If PlochyRZV_p is empty.
                elif gpd.read_file(plochy_rzv_path).empty is True:
                    print("       - PlochyRZV_p is empty.",
                          end="\n" * 2)
                errors += 1
        else:
            print("Error: Overlaps between KoridoryP_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2)
            errors += 1

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    return errors, warns


def vu_within_uses(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export: bool = False,
) -> int:
    """Checking VU features from VpsVpoAs_p within USES_p.

    Check, if VU features from VpsVpoAs_p shapefie are within
    USES_p shapefile. If VU feaures are missing or are empty,
    checking process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       shapefile that are not withis USES_p shapefile. 
       Default value is set up as False (for not exporting these
       geometries outside USES_p shapefile). For exporting these
       geometries, put True.

    Returns
    -------
    int
        Integer that indicates if there are some errors (0 -> no
        errors, 1 -> errors occurr). 
    """
    errors = 0
    try:
        shps_from_zip = shps_in_zip(zip_dir, mun_code)
        shps_to_check = [
            shp
            for shp in js_tables
            if shp in shps_from_zip
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            is False
        ]
        if shp == "VpsVpoAs_p" and "USES_p" in shps_to_check:
            if validity_shp_zip(zip_dir, mun_code, shp) == 0 and validity_shp_zip(zip_dir, mun_code, "USES_p") == 0:
                # Path to USES_p shapefile.
                uses_p_path = (
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/USES_p.shp"
                )
                # Path to VpsVpoAs_p shapefile.
                vpsvpoas_p_path = (
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/VpsVpoAs_p.shp"
                )
                # Create GeoDataFrames from paths above.
                uses_gdf = gpd.read_file(uses_p_path)
                vpsvpoas_gdf = gpd.read_file(vpsvpoas_p_path)
                # Create list of column names from vpsvpoas_gdf.
                col_names = vpsvpoas_gdf.columns.tolist()
                # Change column names to lowecase.
                for col in col_names:
                    vpsvpoas_gdf.rename(columns={col: col.lower()}, inplace=True)
                # Filter rows with "VU" values.
                vpsvpoas_vu = vpsvpoas_gdf[vpsvpoas_gdf["id"].str.startswith("VU")]
                # Reset index to filtered rows (starts from 0).
                vpsvpoas_vu = vpsvpoas_vu.reset_index(drop=True)
                # List for geometry rows.
                geom_out = []
                # For each row (index number) in all geometries (count) find out,
                # which are not within USES_p.
                for i in range(vpsvpoas_vu.geometry.count()):
                    # If geometry is not within USES_p.
                    if vpsvpoas_vu.geometry[i].within(uses_gdf.geometry) is False:
                        # Append geometry parts that lay outside USES_p into geom_out list.
                        geom_out.append(
                            vpsvpoas_vu.geometry[i].difference(uses_gdf.geometry)
                        )
                    # If this geometry is within USES_p, pass.
                    else:
                        pass
                # If all Vu features are within USES_p.
                if len(geom_out) == 0:
                    print(
                        "Ok: There are no VU geometries outside USES_p.",
                        end="\n" * 2
                    )
                # If there are some geometries outside, do:
                elif len(geom_out) > 0 and export is True:
                    errors += 1
                    # Converts these geometries into Geoseries.
                    geom_out_col = gpd.GeoSeries(data=geom_out, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_outside = gpd.GeoDataFrame(geometry=geom_out_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_outside.to_file(
                        f"{dest_dir_path}/vpsvpoas_p_vu_outside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    # Print number of geometries that are not within ReseneUzemi_p.
                    print(
                        f"Error: There are VU geometries outside USES_p ({len(geom_out)}).",
                        "       - These parts were saved as vpsvpoas_p_vu_outside.shp.",
                        end="\n" * 2
                    )
                # If export_outside = False, print number of features outside only.
                else:
                    errors += 0
                    print(
                        f"Error: There are VU geometries outside USES_p ({len(geom_out)}).",
                        end="\n" * 2
                    )
            else:
                print("Error: Checking VU features within USES_p cannot be run due to invalid geometries.",
                      sep="\n" * 2
                      )
        else:
            pass

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors 


def p_within_zu(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export_outside: bool = False,
) -> int:
    """Checking P features from PlochyRZV_p within ZastaveneUzemi_p.

    Check, if P features from VpsVpoAs_p shapefile are within
    ZastaveneUzemi_p. If P features are missing or are empty, checking
    process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       shapefile that are not within ZastaveneUzemi_p shapefile.
       Default value is set up as False (for not exporting these
       geometries outside ZastaveneUzemi_p). For exporting these
       geometries, put True.
    
    Returns
    -------
    int
        Integer that indicates if there are some errors (0 -> no
        errors, 1 -> errors occurr).
    """
    errors = 0
    try:
        shps_from_zip = shps_in_zip(zip_dir, mun_code)
        shps_to_check = [
            shp
            for shp in js_tables
            if shp in shps_from_zip
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            is False
        ]

        if shp == "PlochyZmen_p" and "ZastaveneUzemi_p" in shps_to_check:
            if validity_shp_zip(zip_dir, mun_code, shp) == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0:

                # Path to ZastaveneUzemi_p shapefile.
                zu_p_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
                # Path to PlochyZmen_p shapefile.
                pz_p_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
                # Create GeoDataFrames from paths above.
                zu_gdf = gpd.read_file(zu_p_path)
                pz_gdf = gpd.read_file(pz_p_path)
                # Create list of column names from pz_gdf.
                col_names = pz_gdf.columns.tolist()
                # Change column names to lowecase.
                for col in col_names:
                    pz_gdf.rename(columns={col: col.lower()}, inplace=True)
                # Filter 'P' features from pz_gdf.
                pz_p = pz_gdf[pz_gdf["id"].str.startswith("P")]
                # Reset index from filtered rows (starts from 0).
                pz_p = pz_p.reset_index(drop=True)

                # List for geometry rows.
                geom_out = []
                # Number of geometries.
                # For each row (index number) in all geometries (count) find out,
                # which are not within ZastaveneUzemi_p.
                for i in range(pz_p.geometry.count()):
                    # If geometry is not within ZastaveneUzemi_p.
                    if pz_p.geometry[i].within(zu_gdf.geometry) is False:
                        # Append geometry parts that lay outside ZastaveneUzemi_p into geom_out list.
                        geom_out.append(pz_p.geometry[i].difference(zu_gdf.geometry))
                    # If this geometry is within ZastaveneUzemi_p, pass.
                    else:
                        pass
                # If all 'P' features are within ZastaveneUzemi_p.
                if len(geom_out) == 0:
                    print(
                        "Ok: There are no P geometries outside ZastaveneUzemi_p.",
                        end="\n" * 2
                    )
                # If there are some geometries outside, do:
                elif len(geom_out) > 0 and export_outside is True:
                    errors += 1
                    # Converts these geometries into Geoseries.
                    geom_out_col = gpd.GeoSeries(data=geom_out, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_outside = gpd.GeoDataFrame(geometry=geom_out_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_outside.to_file(
                        f"{dest_dir_path}/plochyzmen_p_p_outside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    # Print number of geometries that are not within ZastaveneUzemi_p.
                    print(
                        f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)}).",
                        "       - These parts were saved as plochyzmen_p_p_outside.shp.",
                        end="\n" * 2,
                    )
                # If export_outside = False, print number of features outside only.
                else:
                    errors += 1
                    print(
                        f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)}).",
                        sep="\n" * 2,
                    )
            else:
                print("Error: Checking Z features within ZastaveneUzemi_p cannot be run due to invalid geometries.")

        else:
            pass
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors


def k_outside_zu(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export_inside: bool = False,
) -> int:
    """Checking K features from PlochyRZV_p outside ZastaveneUzemi_p.

    Check, if K features from VpsVpoAs_p shapefile are outside
    of ZastaveneUzemi_p shapefile. If K features are missing or are empty,
    checking process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    shp : str
        A shapefile name, for which are these relationships
        tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       shapefile that are within ZastaveneUzemi_p.Default value 
       is set up as False (for not exporting these geometries within 
       ZastaveneUzemi_p.shp). For exporting these geometries, put True.
    
    Returns
    -------
    int
        Integer that indicates if there are some errors (0 -> no
        errors, 1 -> errors occurr).
    """
    errors = 0
    try:
        shps_from_zip = shps_in_zip(zip_dir, mun_code)
        shps_to_check = [
            shp
            for shp in js_tables
            if shp in shps_from_zip
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            is False
        ]
        if shp == "PlochyZmen_p" and "ZastaveneUzemi_p" in shps_to_check:
            if validity_shp_zip(zip_dir, mun_code, shp) == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0:
                # Path to ZastaveneUzemi_p shapefile.
                zu_p_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
                # Path to PlochyZmen_p shapefile.
                pz_k_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
                # Create GeoDataFrames from paths above.
                zu_gdf = gpd.read_file(zu_p_path)
                pz_gdf = gpd.read_file(pz_k_path)
                # Create list of column names from pz_gdf.
                col_names = pz_gdf.columns.tolist()
                # Change column names to lowecase.
                for col in col_names:
                    pz_gdf.rename(columns={col: col.lower()}, inplace=True)
                # Filter rows with 'K' features.
                pz_k = pz_gdf[pz_gdf["id"].str.startswith("K")]
                # Reset index for filtered rows (starts from 0).
                pz_k = pz_k.reset_index(drop=True)
                # List for geometry rows.
                geom_in = []
                # For each row (index number) in all geometries (count) find out,
                # which are within ZastaveneUzemi_p.
                for i in range(pz_k.geometry.count()):
                    # If geometry is  within ZastaveneUzemi_p.
                    if pz_k.geometry[i].within(zu_gdf.geometry) is True:
                        # Append geometry parts that lay within ZastaveneUzemi_p into geom_in list.
                        geom_in.append(pz_k.geometry[i].difference(zu_gdf.geometry))
                    # If this geometry is outside the ZastaveneUzemi_p, pass.
                    else:
                        pass
                # If all 'K' features are outside the ZastaveneUzemi_p.
                if len(geom_in) == 0:
                    print(
                        "Ok: There are no K geometries outside ZastaveneUzemi_p.",
                        end="\n" * 2,
                    )
                # If there are some geometries inside, do:
                elif len(geom_in) > 0 and export_inside is True:
                    errors += 1
                    # Converts these geometries into Geoseries.
                    geom_in_col = gpd.GeoSeries(data=geom_in, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_inside = gpd.GeoDataFrame(geometry=geom_in_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_inside.to_file(
                        f"{dest_dir_path}/plochyzmen_k_p_inside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    # Print number of geometries that are within ZastaveneUzemi_p.
                    print(
                        f"Error: There are K geometries inside ZastaveneUzemi_p ({len(geom_in)}).",
                        "       - These parts were saved as plochyzmen_k_p_inside.shp.",
                        end="\n" * 2,
                    )
                # If export_inside = False, print number of features inside only.
                else:
                    errors += 1
                    print(
                        f"Error: There are {len(geom_in)} 'K' feature(s) inside ZastaveneUzemi_p ({len(geom_in)}).",
                        end="\n" * 2,
                    )
            else:
                print("Error: Checking K features outside of ZastaveneUzemi_p cannot be run due to invalid geometries.")
        else:
            pass
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors
