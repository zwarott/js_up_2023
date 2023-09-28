import zipfile
from time import time
import warnings

import geopandas as gpd
from shapely.geometry import Polygon

from src.models.output_tables import js_tables, mandatory_tables


def shp_info(zip_dir: str, mun_code) -> None:
    """Check, if all mandatory shapefiles are included and
    not empty.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zipped files are stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # Crate list of missing shapefiles.
    missing_shp = [shp for shp in js_tables if shp not in shps_to_check]

    # Check each shapefile:
    for shp in js_tables:
        # If is included and not empty.
        if (
            shp not in missing_shp
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
            is False
        ):
            geom_number = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).geometry.count()
            print(f"Ok: '{shp}.shp' is included ({geom_number} feature(s)).")
        # If is included and empty.
        elif (
            shp not in missing_shp
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            ).empty
        ) is True:
            print(f"Error: '{shp}.shp' is inculded, but empty.")
        # If is not included and is not mandatory shapefile.
        elif shp in missing_shp and shp not in mandatory_tables:
            print(f"Warning: '{shp}.shp' is not included.")
        # If is not included and is mandatory shapefile.
        else:
            print(f"Error: '{shp}.shp' is not included.")


def mandatory_shp_miss(zip_dir: str, mun_code: int):
    """Return list with misssing mandatory shapefiles.

    Check, if all mandatory shapefiles are stored in
    zipped file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zipped files are stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # If any layers are missing, put them into the list.
    # Names of mandatory shapefiles are stored in mandatory_tables from
    # (output_tables.py module).
    missing_shp = [shp for shp in mandatory_tables if shp not in shps_to_check]
    return missing_shp


def mandatory_shp_empty(zip_dir: str, mun_code: int):
    """Return list of empty mandatory shapefiles.

    Parameters:
    -----------
    zip_dir : str
        A path to directory, where zipped files are stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
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


def unknown_shp(zip_dir: str, mun_code: int) -> list:
    """Return list with unknown shapefiles.

    Check, if all shapefiles that are stored in
    zipped file are in js_tables or start with "X"
    (non-standardized layer).

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zipped files are stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # If any layers are unknown, put them into the list.
    # Names of all known shapefiles are stored in js_tables from
    # (output_tables.py module).
    unknown_shp = [
        shp for shp in shps_to_check if shp not in js_tables and not shp.startswith("X")
    ]
    return unknown_shp


def shp_within_mun(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_outside: bool = False
) -> None:
    """Check all shapefiles if are within ReseneUzemi_p shapefile.

    Check, if all shapefile are within ReseneUzemi_p shapefile.
    If not, create difference of certain shapefiles and ReseneUzemi_p
    shapefile and if needed, export these as new shapefiles.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    export_outside : bool
        A boolean value for exporting area differences between ReseneUzemi_p
        shapefile and other shapefiles. Default value is set up as False
        (for not exporting these differences). For exporting these differences,
        put True.
    """
    # Start time of checking process
    start_time = time()
    # Create list of zip contents
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of all shapefiles' names only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = "*** Checking shapefiles within 'ReseneUzemi_p.shp' ***"
    print(spaces, checking_process, spaces, sep="\n")
    # Check if all non-empty mandatory shapefiles are included and there are
    # no unknown shapefiles (with different name). If so, run checking process.
    if (
        len(mandatory_shp_miss(zip_dir, mun_code)) == 0
        and len(mandatory_shp_empty(zip_dir, mun_code)) == 0
        and len(unknown_shp(zip_dir, mun_code)) == 0
    ):
        for shp in shps_to_check:
            # If non-mandatory shapefile is not empty, run process below.
            if (
                gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                ).empty
                is False
            ):
                shp_gdf = gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                )
                # Create GeoDataFrame from ReseneUzemi_p shapefile.
                mun_borders_gdf = gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ReseneUzemi_p.shp"
                )
                # Create Polygon geometry from GeoDataFrame coordinates.
                borders_polygon = Polygon(mun_borders_gdf.get_coordinates())
                # List for informations about each row.
                info_col_out = []
                # Column's name and records (row).
                info_col = {"info": info_col_out}
                # List for geometry rows.
                geom_out = []
                # Number of geometries.
                geom_out_count = 0
                # For each row (index number) in all geometries (count) find out,
                # which are not within ReseneUzemi_p.
                for i in range(shp_gdf.geometry.count()):
                    # If geometry is not within ReseneUzemi_p.
                    if shp_gdf.geometry[i].within(borders_polygon) is False:
                        # Append info from the first column to info_col_out list.
                        info_col_out.append(shp_gdf.iloc[:, 0][i])
                        # Append geometry parts that lay outside ReseneUzemi_p into geom_out list.
                        geom_out.append(shp_gdf.geometry[i].difference(borders_polygon))
                        # Count this geometry.
                        geom_out_count += 1
                    # If this geometry is within ReseneUzemi_p, pass.
                    else:
                        pass

                if geom_out_count == 0:
                    print(
                        f"Ok: All geometries from '{shp}.shp' are within 'ReseneUzemi_p.shp'.",
                    )
                # If there are some geometries outside, do:
                elif geom_out_count > 0 and export_outside is True:
                    # Converts these geometries into Geoseries.
                    geom_out_col = gpd.GeoSeries(data=geom_out, crs="epsg:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_outside = gpd.GeoDataFrame(
                        data=info_col, geometry=geom_out_col, crs="epsg:5514"
                    )
                    # Export this GeoDataFrame as shapefile.
                    gdf_outside.to_file(
                        f"{dest_dir_path}/{shp.lower()}_outside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    # Print number of geometries that are not within ReseneUzemi_p.
                    print(
                        f"Error: There are {geom_out_count} feature(s) from '{shp}.shp' outside 'ReseneUzemi_p.shp'.",
                        f"       - These parts were saved as '{shp.lower()}_outside.shp'.",
                        sep="\n",
                    )
                # If export_outside = False, print number of features outside only.
                else:
                    print(
                        f"Error: There are {geom_out_count} feature(s) from '{shp}.shp' outside 'ReseneUzemi_p.shp'.",
                    )
            # If non-mandatory shapefile is empty, print info about it only.
            else:
                print(f"Warning: '{shp}.shp' is empty.")
    else:
        print(
            "Error: Checking geometries within 'ReseneUzemi_p.shp' could not be done due to:"
        )
        # Print info about missing mandatory shapefiles.
        for shp in mandatory_shp_miss(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is missing.")
        # Print info about empty mandatory shapefiles.
        for shp in mandatory_shp_empty(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is empty.")
        # Print info about unknown non-mandatory shapefiles.
        for shp in unknown_shp(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is unknown.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def covered_mun(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_diff: bool = False
) -> None:
    """Check if whole 'ReseneUzemi_p' is covered.

    Check if whole 'ReseneUzemi_p' shapefile is covered by 'PlochyRZV_p' and
    'KoridoryP_p' shapefiles.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_diff : bool
       A boolean value for exporting area differences between ReseneUzemi_p
       shapefile and merged PlochyRZV_p and KoridoryP_p layers. Default value
       is set up as False (for not exporting these differences). For exporting
       these differences, put True.

    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of all shapefiles included in zip file.
    shps_in_zip = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # Create list with needed shapefile names.
    shps_to_check = ["PlochyRZV_p", "ReseneUzemi_p", "KoridoryP_p"]
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = "*** Checking covering 'ReseneUzemi_p.shp' ***"
    print(spaces, checking_process, spaces, sep="\n")

    # If PlochyRZV_p and KoridoryP_p exist and are not empty.
    if (
        shps_to_check[0] in shps_in_zip
        and gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[0]}.shp"
        ).empty
        is False
        and shps_to_check[1] in shps_in_zip
        and gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[0]}.shp"
        ).empty
        is False
    ):
        # Create GeoDataFrame from PlochyRZV_p.shp.
        plochy_rzv = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[0]}.shp"
        )
        # Create GeoDataFrame from ReseneUzemi_p.shp.
        resene_uzemi = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[1]}.shp"
        )
        # Create shapely geometry (polygon) from geodataframe coordinates.
        resene_uzemi_geom = Polygon(resene_uzemi.get_coordinates())
        # If KoridoryP_p.shp is missing or is empty, work with PlochyRZV_p and ReseneUzemi_p
        # only.
        if (
            shps_to_check[2] not in shps_in_zip
            or gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[0]}.shp"
            ).empty
            is True
        ):
            print("Warning: 'KoridoryP_p.shp' is missing or is empty.")
            # Dissolved PlochyRZV_p GeoDataFrame.
            dissolved = plochy_rzv.dissolve()
            # Difference bewtween ReseneUzemi_p and dissolved GeoDataFrame.
            diff = resene_uzemi_geom.difference(dissolved.geometry)
            # Create singleparts from diff.
            diff["singleparts"] = [p for p in diff]
            # Export diff geometries.
            diff_geom = diff["singleparts"]
            # Create new geodataframe from diff_geom.
            gdf_diff = gpd.GeoDataFrame(geometry=diff_geom, crs="epsg:5514")
            # Explode multiparts geometries into single geometries (list to
            # rows).
            exploded = gdf_diff.explode(index_parts=False)
            # If there is no differences, print statement only.
            if diff is None:
                print(
                    f"Ok: All geometries in 'PlochyRZV_p.shp' cover 'ReseneUzemi_p.shp'.",
                )
            # If there are some differences and export diff = True, export them
            # as shapefile and print statements about differences.
            if diff is not None and export_diff is True:
                exploded.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="5514",
                )

                print(
                    f"Error: 'ReseneUzemi_p.shp' is not fully covered by 'PlochyRZV_p.shp'.",
                    f"       - There are {len(exploded.geometry)} feature(s) that does not cover 'ReseneUzemi_p.shp'.",
                    f"       - These parts were saved as 'not_cover_reseneuzemi_p.shp'",
                    sep="\n",
                )
            # If export_diff = false, print info about differences only.
            else:
                print(
                    f"Error: 'ReseneUzemi_p.shp' is not fully covered by 'PlochyRZV_p.shp'.",
                    f"       - There are {len(exploded.geometry)} feature(s) that does not cover 'ReseneUzemi_p.shp'.",
                    sep="\n",
                )
        # If KoridoryP_p.shp exists and is not empty.
        elif (
            shps_to_check[2] in shps_in_zip
            and gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[2]}.shp"
            ).empty
            is False
        ):
            koridory_p = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shps_to_check[2]}.shp"
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
            gdf_diff = gpd.GeoDataFrame(geometry=diff_geom, crs="epsg:5514")
            # Explode multiparts geometries into single geometries (list to
            # rows).
            exploded = gdf_diff.explode(index_parts=False)
            # If there is no differences, print statement only.
            if diff is None:
                print(
                    f"Ok: All geometries in 'PlochyRZV_p' and 'KoridoryP_p.shp' cover 'ReseneUzemi_p.shp'.",
                )
            # If there are some differences and export diff = True, export them
            # as shapefile and print statements about differences.
            if diff is not None and export_diff is True:
                exploded.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )

                print(
                    f"Error: 'ReseneUzemi_p.shp' is not fully covered by 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.",
                    f"       - There are {len(exploded.geometry)} feature(s) that does not cover 'reseneuzemi_p.shp'.",
                    f"       - These part were saved as 'not_cover_reseneuzemi_p.shp'",
                    sep="\n",
                )
            # If export_diff = False, print info about differences only.
            else:
                print(
                    f"Error: 'ReseneUzemi_p' is not fully covered by 'PlochyRZV_p' and 'KoridoryP_p'.",
                    f"       - There are {len(exploded.geometry)} feature(s) that does not cover 'ReseneUzemi_p.shp'.",
                    sep="\n",
                )

    else:
        print("Error: Checking covering 'ReseneUzemi_p.shp' could not be done due to:")
        # Print info about missing and empty mandatory shapefiles.
        for shp in shps_to_check[:2]:
            if shp not in shps_in_zip:
                print(f"       - '{shp}.shp' is missing.")
            elif (
                shp in shps_in_zip
                and gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                ).empty
                is True
            ):
                print(f"       - '{shp}.shp' is empty.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def check_gaps(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_gaps: bool = False
) -> None:
    """Check gaps within each shapefile.

    Check gaps between polygons within each shapefile stored in
    zipped file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be gaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_gaps : bool
       A boolean value for exporting gaps of certain ESRI Shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of all shapefiles' names only.
    shps_to_check = set(
        shp.removeprefix("DUP_123456/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp
    )
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = "*** Checking gaps within each shapefile ***"
    print(spaces, checking_process, spaces, sep="\n")
    # Check if all non-empty mandatory shapefiles are included and there are
    # no unknown shapefiles (with different name). If so, run checking process.
    if (
        len(mandatory_shp_miss(zip_dir, mun_code)) == 0
        and len(mandatory_shp_empty(zip_dir, mun_code)) == 0
        and len(unknown_shp(zip_dir, mun_code)) == 0
    ):
        for shp in shps_to_check:
            # If non-mandatory is not empty, run process below.
            if (
                gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                ).empty
                is False
            ):
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
                # lited. See interiors and tolist() method for more info.
                interior = dissolved.geometry.interiors.tolist()[0]
                # Print statement for shapefiles without inner rings.
                if interior is None or len(interior) == 0:
                    print(f"Ok: There are no gaps in '{shp}.shp'.")
                # If there are some inner rings, exported them as shapefile and print
                # number of inner rings and where these inner rings are stored.
                elif len(interior) > 0 and export_gaps is True:
                    gaps_polygons = [Polygon(a) for a in interior]
                    interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="epsg:5514")
                    interior_gdf = gpd.GeoDataFrame(
                        geometry=interior_geom, crs="epsg:5514"
                    )
                    interior_gdf.to_file(
                        f"{dest_dir_path}/{shp.lower()}_gaps.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    print(
                        f"Error: There are {len(interior)} gaps in '{shp}.shp'.",
                        f"       - These gaps were saved as '{shp.lower()}_gaps.shp'.",
                        sep="\n",
                    )
                # If export_gaps = False, print only number of inner rings.
                else:
                    print(
                        f"Error: There are {len(interior)} gaps in '{shp}.shp.'",
                    )
            # If non-mandatory shapefile is empty, print info about it only.
            else:
                print(f"Warning: '{shp}.shp' is empty.")
    else:
        print("Error: Checking gaps within each shapefile could not be done due to:")
        # Print info about missing mandatory shapefiles.
        for shp in mandatory_shp_miss(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is missing.")
        # Print info about empty mandatory shapefiles.
        for shp in mandatory_shp_empty(zip_dir, mun_code):
            print(f"       - '{shp}.shp is empty.")
        # Print info about unknown non-mandatory shapefiles.
        for shp in unknown_shp(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is unknown.")
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def check_gaps_covered(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_gaps: bool = False
) -> None:
    """Check gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.

    Check, if there are any gaps between 'PlochyRZV_p.shp' and
    'KoridoryP_p.shp' coverings. If shapefile 'KoridoryP_p.shp' is
    not included, gaps are check in 'PlochyRZV_p.shp' only.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be gaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_gapexport_overlapsl
       A boolean value for exporting gaps of certain ESRI Shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = (
        "*** Check gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' shapefiles ***"
    )
    print(spaces, checking_process, spaces, sep="\n")

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
        f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
        and gpd.read_file(plochy_rzv_path).empty is False
        and f"DUP_{mun_code}/Data/KoridoryP_p.shp" in zip_contents
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
                "OK: There is no gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.",
                sep="\n",
            )
        # If there are some inner rings, exported them as shapefile and print
        # number of inner rings and where these inner rings are stored.
        elif len(interior) > 0 and export_gaps is True:
            gaps_polygons = [Polygon(a) for a in interior]
            interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="epsg:5514")
            interior_gdf = gpd.GeoDataFrame(geometry=interior_geom, crs="epsg:5514")
            interior_gdf.to_file(
                f"{dest_dir_path}/plochy_rzv_kordiory_p_gaps.shp",
                driver="ESRI Shapefile",
                crs="ESPG:5514",
            )
            print(
                f"Error: There are {len(interior)} gaps betweeen 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.",
                f"       - These gaps were exported as 'plochy_rzv_kordiory_p_gaps.shp'.",
                sep="\n",
            )
        # If export_gaps = False, print number of inner rings only.
        else:
            print(
                f"Error: There are {len(interior)} gaps between 'PlochyRZV_p.shp' and 'Koridory_p.shp'.",
            )
    # If there is only PlochyRZV_p.
    elif (
        f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
        and gpd.read_file(plochy_rzv_path).empty is False
        and f"DUP_{mun_code}/Data/KoridoryP_p.shp" not in zip_contents
    ):
        print(
            "Error: Gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' cannot be check due to:",
            "       - 'KoridoryP_p.shp' is missing.",
            "Gaps in 'PlochyRZV_p.shp' has been already checked within other step.",
            sep="\n",
        )
    # If there are both shapefiles, but KoridoryP_p is empty.
    elif (
        f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
        and gpd.read_file(plochy_rzv_path).empty is False
        and gpd.read_file(koridory_p_path).empty is True
    ):
        print(
            "Error: Gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' cannot be check due to:",
            "       - 'KoridoryP_p.shp' is empty.",
            "Gaps in 'PlochyRZV_p.shp' has been already checked within other step.",
            sep="\n",
        )
    else:
        print(
            "Error: Gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' cannot be checked due to:"
        )
        # If KoridoryP_p is misssing.
        if f"DUP_{mun_code}/Data/PlochyRZV_p.shp" not in zip_contents:
            print("       - 'PlochyRZV_p.shp' is missing.")
        # If KoridoryP_p is empty.
        elif gpd.read_file(plochy_rzv_path).empty is True:
            print("       - 'PlochyRZV_p.shp' is empty.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def check_overlaps(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_overlaps: bool = False
) -> None:
    """Check overlaps within each shapefile (except VpsVpoAs layers).

    Check overlaps between polygons within each shapefile stored in
    zipped file (excepet VpsVpoAs layers, these features can overlap
    each other).

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_overlaps : bool
       A boolean value for exporting overlaping geometries of certain
       ESRI Shapefile. Default value is set up as False (for not exporting
       these overlaping geometries). For exporting these overlaps, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles' names (VpsVpoAs shapefiles) are not included.
    shps_to_check = set(
        shp.removeprefix("DUP_123456/Data/").removesuffix(".shp")
        for shp in zip_contents
        if ".shp" in shp and "xml" not in shp and "VpsVpoAs" not in shp
    )
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = "*** Checking overlaps within each shapefile ***"
    print(spaces, checking_process, spaces, sep="\n")
    # If non-empty mandatory and non-unknown shapefiles are included,
    # run process below.
    if (
        len(mandatory_shp_miss(zip_dir, mun_code)) == 0
        and len(mandatory_shp_empty(zip_dir, mun_code)) == 0
        and len(unknown_shp(zip_dir, mun_code)) == 0
    ):
        for shp in shps_to_check:
            # From each shapefile create GeoDataFrame instead of empty non-mandatory
            # shapefile.
            if (
                gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                ).empty
                is False
            ):
                shp_gdf = gpd.read_file(
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
                )
                # Ignore RuntimeWarning.
                warnings.filterwarnings(
                    "ignore", "invalid value encountered", RuntimeWarning
                )
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
                intersected = []
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
                    print(f"Ok: There is no overlaps in '{shp}.shp'.")
                # If there are overlaps (polygon parts), export them and
                # print their number and where were these geometries stored.
                elif len(polyg_only) > 0 and export_overlaps is True:
                    gdf_overlaps = gpd.GeoDataFrame(
                        geometry=polyg_only, crs="epsg:5514"
                    )
                    gdf_overlaps.to_file(
                        f"{dest_dir_path}/{shp.lower()}_overlaps.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    print(
                        f"Error: There are {len(polyg_only)} overlaps in '{shp}.shp'.",
                        f"       - Overlaping parts were exported into as '{shp.lower()}_overlaps.shp'.",
                        sep="\n",
                    )
                # If export_overlaps = export number of oerlaps only.
                else:
                    print(
                        f"Error: There are {len(polyg_only)} overlaps in '{shp}.shp'.",
                    )
            # If non-mandatory shapefile is empty, print info about it only.
            else:
                print(f"Warning: '{shp}.shp' is empty.")

    else:
        print("Error: Checking gaps within each shapefile could not be done due to:")
        # Print info about missing mandatory shapefiles.
        for shp in mandatory_shp_miss(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is missing.")
        # Print info about empty mandatory shapefiles.
        for shp in mandatory_shp_empty(zip_dir, mun_code):
            print(f"       - '{shp}.shp is empty.")
        # Print info about unknown non-mandatory shapefiles.
        for shp in unknown_shp(zip_dir, mun_code):
            print(f"       - '{shp}.shp' is unknown.")

    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def overlaps_covered_mun(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_overlaps: bool = False
) -> None:
    """Check overlaps between PlochyRZV_p.shp and KoridoryP_p.shp.

    Check, if there are any overlaps between PlochyRZV_p.shp and
    KoridoryP_p.shp. If KoridoryP_p.shp is missing, overlaps will
    be not checked, because overlaps in KoridoryP_p.shp will be
    already checked.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_overlaps : bool
       A boolean value for exporting overlaping geometries of certain
       ESRI Shapefile. Default value is set up as False (for not exporting
       these overlaping geometries). For exporting these overlaps, put True.

    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = "*** Checking gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' shapefiles ***"
    print(spaces, checking_process, spaces, sep="\n")
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
        gdf_inter = gpd.GeoDataFrame(geometry=inter_geom, crs="epsg:5514")
        # Explode multiparts geometries into single geometries (list to
        # rows).
        # If index_parts = False, index_parts will be not exported as a
        # new column.
        exploded = gdf_inter.explode(index_parts=False)
        polyg_only = [x for x in exploded if x.geom_type == "Polygon"]
        # If there are not any .
        if len(polyg_only) == 0:
            print(
                "Ok: There are no overlaps between 'PlochyRZV_p' and 'KoridoryP_p'.",
            )
        # If there are some intersections and export_inter = True, export them
        # as shapefile and print statements about intersections.
        if len(polyg_only) > 0 and export_overlaps is True:
            exploded.to_file(
                f"{dest_dir_path}/plochy_rzv_koridory_p_overlaps.shp",
                driver="ESRI Shapefile",
                crs="ESPG:5514",
            )
            print(
                "Error: There are overlaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.",
                f"      - Number of overlaping geometries: {len(exploded.geometry)}.",
                f"      - Overlaping geometries were saved as 'plochy_rzv_koridory_p_overlaps.shp'.",
                sep="\n",
            )
        # If export_inter = False, print statement about differences.
        else:
            print(
                "Error: There are overlaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp'.",
                f"      - Number of overlaping geometries: {len(exploded.geometry)}.",
                sep="\n",
            )
    # If non-empty PlochyRZV_p is included and KoridoryP_p is missing.
    elif (
        f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
        and gpd.read_file(plochy_rzv_path).empty is False
        and f"DUP_{mun_code}/Data/KoridoryP_p.shp" not in zip_contents
    ):
        print(
            "Warning: Gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' were not checked due to:",
            "         - 'KoridoryP_p.shp' is missing.",
            "         - Overlaps in 'PlochyRZV_p.shp' has been already checked within other step.",
            sep="\n",
        )
    # If non-empty PlochyRZV_p is included and KoridoryP_p is empty.
    elif (
        f"DUP_{mun_code}/Data/PlochyRZV_p.shp" in zip_contents
        and gpd.read_file(plochy_rzv_path).empty is False
        and gpd.read_file(koridory_p_path).empty is True
    ):
        print(
            "Warning: Gaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' were not checked due to:",
            "         - 'KoridoryP_p.shp' is empty.",
            "         - Overlaps in 'PlochyRZV_p.shp' has been already checked within other step.",
            sep="\n",
        )
    else:
        print(
            "Error: Overlaps between 'PlochyRZV_p.shp' and 'KoridoryP_p.shp' cannot be checked due to:"
        )
        # If PlochyRZV_p is missing.
        if f"DUP_{mun_code}/Data/PlochyRZV_p.shp" not in zip_contents:
            print("       - 'PlochyRZV_p.shp' is missing.")
        # If PlochyRZV_p is empty.
        elif gpd.read_file(plochy_rzv_path).empty is True:
            print("       - 'PlochyRZV_p.shp' is empty.")

    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def vu_within_uses(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_outside: bool = False
) -> None:
    """Check 'VU' features from VpsVpoAs_p.shp within USES_p.shp.

    Check, if 'VU' features from VpsVpoAs_p.shp are within
    USES_p.shp. If 'VU' feaures is missing or is empty, checking
    process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       ESRI Shapefile that are not withis USES_p.shp. Default
       value is set up as False (for not exporting these
       geometries outside USES_p.shp). For exporting these
       geometries, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = (
        "*** Checking 'VpsVpoAs_p.shp' (VU) geometries within 'USES_p.shp' ***"
    )
    print(spaces, checking_process, spaces, sep="\n")
    # Path to USES_p shapefile.
    uses_p_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/USES_p.shp"
    # Path to VpsVpoAs_p shapefile.
    vpsvpoas_p_path = (
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/VpsVpoAs_p.shp"
    )
    # Create GeoDataFrames from paths above.
    uses_gdf = gpd.read_file(uses_p_path)
    vpsvpoas_gdf = gpd.read_file(vpsvpoas_p_path)
    # Filter rows with "VU" values.
    vpsvpoas_vu = vpsvpoas_gdf[vpsvpoas_gdf["id"].str.startswith("VU")]
    # Reset index to filtered rows (starts from 0).
    vpsvpoas_vu = vpsvpoas_vu.reset_index(drop=True)

    # If both shapefiles are included and GeoDataFrames are not empty.
    if (
        f"DUP_{mun_code}/Data/USES_p.shp" in zip_contents
        and uses_gdf.empty is False
        and f"DUP_{mun_code}/Data/VpsVpoAs_p.shp" in zip_contents
        and vpsvpoas_vu.empty is False
    ):
        # List for geometry rows.
        geom_out = []
        # Number of geometries.
        geom_out_count = 0
        # For each row (index number) in all geometries (count) find out,
        # which are not within USES_p.
        for i in range(vpsvpoas_vu.geometry.count()):
            # If geometry is not within USES_p.
            if vpsvpoas_vu.geometry[i].within(uses_gdf.geometry) is False:
                # Append geometry parts that lay outside USES_p into geom_out list.
                geom_out.append(vpsvpoas_vu.geometry[i].difference(uses_gdf.geometry))
                # Count this geometry.
                geom_out_count += 1
            # If this geometry is within USES_p, pass.
            else:
                pass
        # If all Vu features are within USES_p.
        if geom_out_count == 0:
            print(
                "Ok: All features (VU) from 'VpsVpoAs_p.shp' are within 'USES_p.shp'.",
            )
        # If there are some geometries outside, do:
        elif geom_out_count > 0 and export_outside is True:
            # Converts these geometries into Geoseries.
            geom_out_col = gpd.GeoSeries(data=geom_out, crs="epsg:5514")
            # Then create GeoDataFrame (from info list and Geoseries).
            gdf_outside = gpd.GeoDataFrame(geometry=geom_out_col, crs="epsg:5514")
            # Export this GeoDataFrame as shapefile.
            gdf_outside.to_file(
                f"{dest_dir_path}/vpsvpoas_p_vu_outside.shp",
                driver="ESRI Shapefile",
                crs="EPSG:5514",
            )
            # Print number of geometries that are not within ReseneUzemi_p.
            print(
                f"Error: There are {geom_out_count} VU feature(s) from 'VpsVpoAs_p.shp' outside 'ReseneUzemi_p.shp'.",
                "       - These parts were saved as 'vpsvpoas_p_vu_outside.shp'.",
                sep="\n",
            )
        # If export_outside = False, print number of features outside only.
        else:
            print(
                f"Error: There are {geom_out_count} VU feature(s) from 'VpsVpoAs_p.shp' outside 'ReseneUzemi_p.shp'.",
            )
    else:
        print(
            "Warning: Checking VU features from 'VpsVpoAs_p.shp' within 'USES_p.shp' cannot be done due to:"
        )
        if f"DUP_{mun_code}/Data/USES_p.shp" not in zip_contents:
            print("'USES_p.shp' is missing")
        elif f"DUP_{mun_code}/Data/VpsVpoAs_p.shp" not in zip_contents:
            print("'VpsVpoAs_p.shp' is missing")
        elif uses_gdf.empty is True:
            print("'USES_p.shp' is empty.")
        elif vpsvpoas_vu.empty is True:
            print("'VU' features are not included.")
        else:
            print("'VpsVpoAs_p.shp' is empty.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def p_within_zu(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_outside: bool = False
) -> None:
    """Check 'P' features from PlochyRZV_p.shp within ZastaveneUzemi_p.shp.

    Check, if 'P' features from VpsVpoAs_p.shp are within
    ZastaveneUzemi_p.shp. If 'P' feaures is missing or is empty, checking
    process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       ESRI Shapefile that are not within ZastaveneUzemi_p.shp.
       Default value is set up as False (for not exporting these
       geometries outside ZastaveneUzemi_p.shp). For exporting these
       geometries, put True.
    """

    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = (
        "*** Checking 'PlochyZmen_p.shp' (P) features within 'ZastaveneUzemi_p.shp' ***"
    )
    print(spaces, checking_process, spaces, sep="\n")
    # Path to ZastaveneUzemi_p shapefile.
    zu_p_path = (
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
    )
    # Path to PlochyZmen_p shapefile.
    pz_p_path = (
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
    )
    # Create GeoDataFrames from paths above.
    zu_gdf = gpd.read_file(zu_p_path)
    pz_gdf = gpd.read_file(pz_p_path)
    # Filter 'P' features from pz_gdf.
    pz_p = pz_gdf[pz_gdf["id"].str.startswith("P")]
    # Reset index from filtered rows (starts from 0).
    pz_p = pz_p.reset_index(drop=True)

    # If both shapefiles above are included and GeoDataFrames are not empty.
    if (
        f"DUP_{mun_code}/Data/ZastaveneUzemi_p.shp" in zip_contents
        and zu_gdf.empty is False
        and f"DUP_{mun_code}/Data/PlochyZmen_p.shp" in zip_contents
        and pz_p.empty is False
    ):
        # List for geometry rows.
        geom_out = []
        # Number of geometries.
        geom_out_count = 0
        # For each row (index number) in all geometries (count) find out,
        # which are not within ZastaveneUzemi_p.
        for i in range(pz_p.geometry.count()):
            # If geometry is not within ZastaveneUzemi_p.
            if pz_p.geometry[i].within(zu_gdf.geometry) is False:
                # Append geometry parts that lay outside ZastaveneUzemi_p into geom_out list.
                geom_out.append(pz_p.geometry[i].difference(zu_gdf.geometry))
                # Count this geometry.
                geom_out_count += 1
            # If this geometry is within ZastaveneUzemi_p, pass.
            else:
                pass
        # If all 'P' features are within ZastaveneUzemi_p.
        if geom_out_count == 0:
            print(
                "Ok: All 'P' features from 'PlochyZmen_p.shp' are within 'ZastaveneUzemi_p.shp'.",
            )
        # If there are some geometries outside, do:
        elif geom_out_count > 0 and export_outside is True:
            # Converts these geometries into Geoseries.
            geom_out_col = gpd.GeoSeries(data=geom_out, crs="epsg:5514")
            # Then create GeoDataFrame (from info list and Geoseries).
            gdf_outside = gpd.GeoDataFrame(geometry=geom_out_col, crs="epsg:5514")
            # Export this GeoDataFrame as shapefile.
            gdf_outside.to_file(
                f"{dest_dir_path}/plochyzmen_p_p_outside.shp",
                driver="ESRI Shapefile",
                crs="EPSG:5514",
            )
            # Print number of geometries that are not within ZastaveneUzemi_p.
            print(
                f"Error: There are {geom_out_count} 'P' feature(s) from 'PlochyZmen_p.shp' outside 'ZastaveneUzemi_p.shp'.",
                "       - These parts were saved as 'plochyzmen_p_p_outside.shp'.",
                sep="\n",
            )
        # If export_outside = False, print number of features outside only.
        else:
            print(
                f"Error: There are {geom_out_count} 'P' feature(s) from 'PlochyZmen_p.shp' outside 'ZastaveneUzemi_p.shp'.",
            )
    else:
        print(
            "Warning: Checking 'P' features from 'PlochyZmen_p.shp' within 'ZastaveneUzemi_p.shp' cannot be done due to:"
        )
        if f"DUP_{mun_code}/Data/ZastaveneUzemi_p.shp" not in zip_contents:
            print("'ZastaveneUzemi_p.shp' is missing")
        elif f"DUP_{mun_code}/Data/PlochyZmen_p.shp" not in zip_contents:
            print("'PlochyZmen_p.shp' is missing")
        elif zu_gdf.empty is True:
            print("'ZastaveneUzemi_p.shp' is empty.")
        elif pz_p.empty is True:
            print("'P' features are not included.")
        else:
            print("'PlochyZmen_p.shp' is empty.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")


def k_outside_zu(
    zip_dir: str, dest_dir_path: str, mun_code: int, export_inside: bool = False
) -> None:
    """Check 'K' features from PlochyRZV_p.shp outside ZastaveneUzemi_p.shp.

    Check, if 'K' features from VpsVpoAs_p.shp are outside
    ZastaveneUzemi_p.shp. If 'K' feaures is missing or is empty,
    checking process is skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be overlaps saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these spatial data tested.
    export_overlaps : bool
       A boolean value for exporting geometries of certain
       ESRI Shapefile that are  within ZastaveneUzemi_p.shp.
       Default value is set up as False (for not exporting these
       geometries within ZastaveneUzemi_p.shp). For exporting these
       geometries, put True.
    """

    # Start time of checking process.
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Checking process announcement title.
    separator = "-" * 150
    spaces = " " * 150
    checking_process = (
        "*** Checking 'PlochyZmen_p.shp' (K) features inside 'ZastaveneUzemi_p.shp' ***"
    )
    print(spaces, checking_process, spaces, sep="\n")
    # Path to ZastaveneUzemi_p shapefile.
    zu_p_path = (
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
    )
    # Path to PlochyZmen_p shapefile.
    pz_k_path = (
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
    )
    # Create GeoDataFrames from paths above.
    zu_gdf = gpd.read_file(zu_p_path)
    pz_gdf = gpd.read_file(pz_k_path)
    # Filter rows with 'K' features.
    pz_k = pz_gdf[pz_gdf["id"].str.startswith("K")]
    # Reset index for filtered rows (starts from 0).
    pz_k = pz_k.reset_index(drop=True)

    # If bowh shapefiles above are included and GeoDataFrames are not empty.
    if (
        f"DUP_{mun_code}/Data/ZastaveneUzemi_p.shp" in zip_contents
        and zu_gdf.empty is False
        and f"DUP_{mun_code}/Data/PlochyZmen_p.shp" in zip_contents
        and pz_k.empty is False
    ):
        # List for geometry rows.
        geom_in = []
        # Number of geometries.
        geom_in_count = 0
        # For each row (index number) in all geometries (count) find out,
        # which are within ZastaveneUzemi_p.
        for i in range(pz_k.geometry.count()):
            # If geometry is  within ZastaveneUzemi_p.
            if pz_k.geometry[i].within(zu_gdf.geometry) is True:
                # Append geometry parts that lay within ZastaveneUzemi_p into geom_in list.
                geom_in.append(pz_k.geometry[i].difference(zu_gdf.geometry))
                # Count this geometry.
                geom_in_count += 1
            # If this geometry is outside the ZastaveneUzemi_p, pass.
            else:
                pass
        # If all 'K' features are outside the ZastaveneUzemi_p.
        if geom_in_count == 0:
            print(
                "Ok: All 'K' features from 'PlochyZmen_p.shp' are inside 'ZastaveneUzemi_p.shp'.",
            )
        # If there are some geometries inside, do:
        elif geom_in_count > 0 and export_inside is True:
            # Converts these geometries into Geoseries.
            geom_in_col = gpd.GeoSeries(data=geom_in, crs="epsg:5514")
            # Then create GeoDataFrame (from info list and Geoseries).
            gdf_inside = gpd.GeoDataFrame(geometry=geom_in_col, crs="epsg:5514")
            # Export this GeoDataFrame as shapefile.
            gdf_inside.to_file(
                f"{dest_dir_path}/plochyzmen_k_p_inside.shp",
                driver="ESRI Shapefile",
                crs="EPSG:5514",
            )
            # Print number of geometries that are within ZastaveneUzemi_p.
            print(
                f"Error: There are {geom_in_count} 'K' feature(s) from 'PlochyZmen_p.shp' inside 'ZastaveneUzemi_p.shp'.",
                "       - These parts were saved as 'plochyzmen_k_p_inside.shp'.",
                sep="\n",
            )
        # If export_inside = False, print number of features inside only.
        else:
            print(
                f"Error: There are {geom_in_count} 'K' feature(s) from 'PlochyZmen_p.shp' inside 'ZastaveneUzemi_p.shp'.",
            )
    else:
        print(
            "Warning: Checking 'K' features from 'PlochyZmen_p.shp' inside 'ZastaveneUzemi_p.shp' cannot be done due to:"
        )
        if f"DUP_{mun_code}/Data/ZastaveneUzemi_p.shp" not in zip_contents:
            print("'ZastaveneUzemi_p.shp' is missing")
        elif f"DUP_{mun_code}/Data/PlochyZmen_p.shp" not in zip_contents:
            print("'PlochyZmen_p.shp' is missing")
        elif zu_gdf.empty is True:
            print("'ZastaveneUzemi_p.shp' is empty.")
        elif pz_k.empty is True:
            print("'K' features are not included.")
        else:
            print("'PlochyZmen_p.shp' is empty.")
    # Print checking and exporting process time.
    duration = time() - start_time
    print(separator, f"Checking time: {duration:.4f} s.", separator, sep="\n")
