import os
from time import time

import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame, GeoSeries
from sqlalchemy import inspect
from shapely import from_wkt, to_wkt
from shapely.geometry import Point
from shapely.validation import explain_validity

from config import engine


def postgis_to_wkt(schema_name: str, table_name: str) -> GeoDataFrame:
    """Converting PostGIS table into a WKT.

    Convert PostGIS table into a WKT format by specifying
    PostGIS schema name and particular table.

    Parameters
    ----------
    schema_name : str
        A string representing schema in PostGIS database,
        where is particular table stored.
    table_name : str
        A string representing table, which will be converted
        into WKT format.
    """
    # Selecting geometry attribute from PostGIS table.
    sql = f"SELECT geometry FROM {schema_name}.{table_name}"
    # GeoDataFrame from PostGIS table.
    gdf_from_postgis = gpd.GeoDataFrame.from_postgis(
        crs="EPSG:5514", sql=sql, con=engine, geom_col="geometry"
    )
    # Return geometry attribute in WKT.
    return from_wkt(gdf_from_postgis.to_wkt())


def shp_to_wkt(shp_path: str) -> GeoSeries:
    """Convert ESRI Shapefile into a WKT.

    Convert ESRI Shapefile into a WKT format by specifying
    path to this shapefile.

    Parameters
    ----------
    sha_path : str
        A string representing path to the particular
        ESRI Shapefile. Need to import aboslute path.
    """
    # GeoSeries from shp.
    gdf_from_shp = gpd.read_file(shp_path)
    # Convert shp attribute (geometry) into wkt.
    return from_wkt(gdf_from_shp.geometry.to_wkt())


def check_validity_postgis(schema_name: str, table_name: str) -> None:
    """Checking geometry validity of PostGIS table.

    Check geometry validity of PostGIS table that was converted
    into WKT format using postgis_to_wkt() user function. Need to
    specify schema name and table name as parameters for function
    converting PostGIS table into WKT. It prints information about
    geometry validity within particular PostGIS table.

    Parameters
    ----------
    schema_name : str
        A string representing particular schema from PostGIS table.
        This is parameter of postgis_to_wkt() user function.
    table_name : str
        A string representing particular table from PostGIS table.
        This is parameter of postgis_to_wkt() user function.
    """
    # Start time of checking process.
    start_time = time()
    # Converted PostGIS table into WKT.
    table_to_check = postgis_to_wkt(schema_name, table_name)
    # List of invalid geometries.
    invalid_geom = []
    # Number of invalid geometries.
    invalid_count = 0
    # Print overview of invalid geometries (cause and coordinates).
    print("Checking Validity Details:")
    # Check geometry for each record (row).
    for geometry in table_to_check.geometry:
        # If geometry is not valid, print cause with coordinates,
        # put it into list with invalid geometries and add it into
        # counting.
        if not explain_validity(geometry) == "Valid Geometry":
            print(explain_validity(geometry))
            invalid_geom.append(to_wkt(geometry))
            invalid_count += 1
        # If geometry is valid, pass.
        else:
            pass
    # If all geometries are valid, print statement about it.
    if invalid_count == 0:
        print("All geometries are valid.")
    # If there are some invalid geometries, print number of them.
    else:
        invalid_msg = f"Number of invalid geometries: {invalid_count}."
        print("-" * 50, invalid_msg, sep="\n")
    duration = time() - start_time
    # Print checking time.
    print(f"Checking time: {duration:.2f} s.")


def check_validity_shp(shp_path: str) -> None:
    """Checking geometry validity of ESRI Shapefile.

    Check geometry validity of ESRI Shapefile that was converted
    into WKT format using shp_to_wkt() user function. Need to
    specify path to shapefile as parameter for function converting
    shapefile into WKT. It prints infromation about geometry validity
    within particular shapefile.

    Parameters
    ----------
    shp_path : str
        A string representing path to the particular
        ESRI Shapefile. Need to import aboslute path.
    """

    # Start time of checking process.
    start_time = time()
    # Converted shapefile into WKT.
    shp_to_check = shp_to_wkt(shp_path)
    # List of invalid geometries.
    invalid_geom = []
    # Number of invalid geometries.
    invalid_count = 0
    # Print overview of invalid geometries (cause and coordinates).
    print("Checking Validity Details:")
    # Check geometry for each record (row).
    for geometry in shp_to_check:
        # If geometry is not valid, print cause with coordinates,
        # put it into list with invalid geometries and add it into
        # counting.
        if not explain_validity(geometry) == "Valid Geometry":
            print(explain_validity(geometry))
            invalid_geom.append(to_wkt(geometry))
            invalid_count += 1
        # If geometry is valid, pass.
        else:
            pass
    # If all geometries are valid, print statement about it.
    if invalid_count == 0:
        print("All geometries are valid.")
    # If there are some invalid geometries, print number of them.
    else:
        invalid_msg = f"Number of invalid geometries: {invalid_count}."
        print("-" * 50, invalid_msg, sep="\n")
    duration = time() - start_time
    # Print checking time.
    print(f"Checking time: {duration:.2f} s.")


def check_validity_shp_dir(dir_path: str, export_invalid: bool = False) -> None:
    """Checking geometry validity of ESRI Shapefiles in directory.

    Check gometry validity of all ESRI Shapefiles in specific
    directory. Need to specify path to directory with shapefiles as 
    parameter for function converting shapefile into WKT. It prints 
    infromation about geometry validity within particular shapefile.

    Parameters
    ----------
    dir_path : str
        A string representing path to direcotry with shapefiles.
    export_ivalid : bool
        A boolean value that specify order for exporting any invalid
        geometries, if exist. Default values is set up as False (not
        export). For exporting invalid geometries, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Create set of shapefiles (only *.shp needed).
    shps_to_check = set(
        shp[:-4] for shp in os.listdir(dir_path) if ".shp" in shp and "xml" not in shp
    )
    single_sep = "-" * 70
    for shp in shps_to_check:
        shp_to_check = shp_to_wkt(f"{dir_path}/{shp}.shp")
        # List of invalid geometries.
        invalid_geom = []
        # Number of invalid geometries.
        invalid_count = 0
        # Print overview of invalid geometries (cause and coordinates).
        invalidity = []
        # Print overview of invalid geometries (cause and coordinates).
        print(f"Checking Validity Details: shapefile '{shp}.shp'")
        # Check geometry for each record (row).
        for geometry in shp_to_check:
            # If geometry is not valid, print cause with coordinates,
            # put it into list with invalid geometries and add it into
            # counting.
            if not explain_validity(geometry) == "Valid Geometry":
                inv_reason = explain_validity(geometry)
                print(inv_reason)
                invalidity.append(inv_reason)
                invalid_geom.append(to_wkt(geometry))
                invalid_count += 1

            # If geometry is valid, pass.
            else:
                pass

        # If all geometries are valid, print statement about it.
        if invalid_count == 0:
            print(
                f"All geometries in shapefile {shp} are valid.",
                single_sep,
                sep="\n",
            )
        # If there are some invalid geometries and these geometries need to be
        # exported, they will be saved as shapefiles. Also print number ot them
        # and destination of exported shapefiles.
        elif invalid_count > 0 and export_invalid is True:
            # Convert infromation about geometry from WKT into GeoSeries.
            geom_col = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="EPSG:5514")
            # Set up a new column with values stored in list above.
            inv_col = {"invalidity": invalidity}
            # Create GeoDataFrame from 'geom_col' as geometry and 'inv_col' as a
            # invalidity reason containg reason and coordinates.
            gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col, crs="EPSG:5514")
            # Path of destination directory (where will be invalid data saved).
            dest_dir_path = "./src/models/data/zc3_up_hrabisin/output/"
            # Save these invalid data as shapefiles.
            gdf.to_file(f"{dest_dir_path}{shp}_invalid.shp")
            # Stored path of each invalid shapefile.
            abs_path = os.path.abspath(f"{dest_dir_path}/{shp}_invalid.shp")
            # Export point layer that include error locations.
            # Step 1 -> String containing characters to remove.
            to_remove_1 = (
                "RingSelf-intersectionSelf-intersectionToofewpointsingeometrycomponent "
            )
            # Step 2 -> Remove characters stored in 'to_remove' variable (error causes).
            stripped_1 = [w.strip(to_remove_1) for w in invalidity]
            # Step 3 -> String containing square brackets to remove.
            to_remove_2 = "[]"
            # Step 4 -> Remove square brackets and create list of strings including
            # coordinates of each error.
            stripped_2 = [w.strip(to_remove_2) for w in stripped_1]
            # Step 5 -> replace space separator by comma separator.
            sep_replaced = [b.replace(" ", ", ") for b in stripped_2]
            # Step 6 -> Convert list of string into list of tuples including
            # float coordinates prepared for exporting as points coordinates.
            coords_tuple = [tuple(map(float, i.split(","))) for i in sep_replaced]
            # Step 7 -> Create point geometry in WKT format.
            geom = [Point(v) for v in coords_tuple]
            # Step 8 -> Create GeoDataFrame including geometry column and column with
            # error causes.
            points_gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom, crs="EPSG:5514")
            # Step 9 -> Export GeoDataFrame as shapefile.
            points_gdf.to_file(f"{dest_dir_path}{shp}_invalid_location.shp")
            # Save absolute path of exported shapefile.
            abs_path_2 = os.path.abspath(
                (f"{dest_dir_path}/{shp}_invalid_location.shp")
            )
            # Print infaromation about: which table contains invalid geometries,
            # number of invalid geometries and where these shapefiles were
            # saved (geometries with error and error locations).
            print(
                f"Number of invalid geometries: {invalid_count}.",
                f"Invalid geometries from shapefile '{shp}.shp' were saved to {abs_path}.",
                f"Invalid geometry locations from shapefile '{shp}.shp' were saved to {abs_path_2}.",
                single_sep,
                sep="\n",
            )
        # If I do not need export invalied geometries, only print their number.
        else:
            print(
                f"Number of invalid geometries: {invalid_count}.",
                single_sep,
                sep="\n",
            )
    # In the end, print checking time.
    duration = time() - start_time
    print(f"Checking time: {duration:.2f} s.")


def validity_shp_zip(
    zip_dir: str,
    mun_code: int,
    shp: str,
) -> int:
    """Checking shapefile validity in zip file.
    
    Check, if certain shapefile in zip file is 
    valid. This user function is created for testing
    validity within other function without printing
    any information as output.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        is certain shapefile tested.
    shp : str
        A shapefile name, for which are geometry validity 
        tested.

    Returns:
    --------
    int
        Number of invalid geometries.
    """
    # GeoSeries from shp.
    gdf_from_shp = gpd.read_file(
        f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
    )
    # Convert shp attribute (geometry) into wkt.
    shp_to_check = from_wkt(gdf_from_shp.geometry.to_wkt())
    # List of invalid geometries.
    invalid_geom = []
    # Print overview of invalid geometries (cause and coordinates).
    invalidity = []
    # Check geometry for each record (row).
    for geometry in shp_to_check:
        # If geometry is not valid, print cause with coordinates,
        # put it into list with invalid geometries and add it into
        # counting.
        if not explain_validity(geometry) == "Valid Geometry":
            inv_reason = explain_validity(geometry)
            invalidity.append(inv_reason)
            invalid_geom.append(to_wkt(geometry))

        # If geometry is valid, pass.
        else:
            pass
    return len(invalid_geom)


def check_validity_shp_zip(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export: bool = False,
):
    """Checking validity of certain shapefile in zip file.

    Check, if certain shapefile in zip file is valid. This 
    user function is created for single testing that prints
    information about validity and invalid geometries.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where  zip file is stored.
    dest_dir_path : str
        A path to directory, where will be invalid geometries saved.
    mun_code : int
        A unique code of particular municipality, for which
        is certain shapefile tested.
    shp : str
        A shapefile name, for which are geometry validity 
        tested.
    export : bool
        A boolean value for exporting invalid geometries. 
        Default value is set up as False (for not exporting these 
        differences). For exporting these differences, put True.

    Returns
    -------
    int
        Number of invalid geometries.

    """
    try:
        # GeoSeries from shp.
        gdf_from_shp = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Convert shp attribute (geometry) into wkt.
        shp_to_check = from_wkt(gdf_from_shp.geometry.to_wkt())
        # List of invalid geometries.
        invalid_geom = []
        # Print overview of invalid geometries (cause and coordinates).
        invalidity = []
        # Check geometry for each record (row).
        for geometry in shp_to_check:
            # If geometry is not valid, print cause with coordinates,
            # put it into list with invalid geometries and add it into
            # counting.
            if not explain_validity(geometry) == "Valid Geometry":
                inv_reason = explain_validity(geometry)
                invalidity.append(inv_reason)
                invalid_geom.append(to_wkt(geometry))

            # If geometry is valid, pass.
            else:
                pass

        # If all geometries are valid, print statement about it.
        if len(invalid_geom) == 0:
            print(
                f"OK: All geometries are valid.",
                end="\n" * 2
            )
        # If there are some invalid geometries and these geometries need to be
        # exported, they will be saved as shapefiles. Also print number ot them
        # and destination of exported shapefiles.
        elif len(invalid_geom) > 0 and export is True:
            # Convert infromation about geometry from WKT into GeoSeries.
            geom_col = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="EPSG:5514")
            # Set up a new column with values stored in list above.
            inv_col = {"invalidity": invalidity}
            # Create GeoDataFrame from 'geom_col' as geometry and 'inv_col' as a
            # invalidity reason containg reason and coordinates.
            gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col, crs="EPSG:5514")
            # Save these invalid data as shapefiles.
            gdf.to_file(f"{dest_dir_path}/{shp.lower()}_invalid.shp")
            # Export point layer that include error locations.
            # Step 1 -> String containing characters to remove.
            to_remove_1 = (
                "RingSelf-intersectionSelf-intersectionToofewpointsingeometrycomponent "
            )
            # Step 2 -> Remove characters stored in 'to_remove' variable (error causes).
            stripped_1 = [w.strip(to_remove_1) for w in invalidity]
            # Step 3 -> String containing square brackets to remove.
            to_remove_2 = "[]"
            # Step 4 -> Remove square brackets and create list of strings including
            # coordinates of each error.
            stripped_2 = [w.strip(to_remove_2) for w in stripped_1]
            # Step 5 -> replace space separator by comma separator.
            sep_replaced = [b.replace(" ", ", ") for b in stripped_2]
            # Step 6 -> Convert list of string into list of tuples including
            # float coordinates prepared for exporting as points coordinates.
            coords_tuple = [tuple(map(float, i.split(","))) for i in sep_replaced]
            # Step 7 -> Create point geometry in WKT format.
            geom = [Point(v) for v in coords_tuple]
            # Step 8 -> Create GeoDataFrame including geometry column and column with
            # error causes.
            points_gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom, crs="EPSG:5514")
            # Step 9 -> Export GeoDataFrame as shapefile.
            points_gdf.to_file(f"{dest_dir_path}/{shp.lower()}_invalid_location.shp")
            # Print infaromation about: which table contains invalid geometries,
            # number of invalid geometries and where these shapefiles were
            # saved (geometries with error and error locations).
            print(
                f"Error: There are invalid geometries ({len(invalid_geom)}).",
                f"       - Invalid geometries were saved as {shp.lower()}_invalid.shp",
                f"       - Invalid geometry locations (points) were saved as {shp.lower()}_invalid_location.shp.",
                end="\n" * 2,
            )
        # If I do not need export invalied geometries, only print their number.
        elif len(invalid_geom) > 0:
            print(
                f"Error: There are invalid geometries ({len(invalid_geom)}).",
                end="\n" * 2
            )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(invalid_geom) 


def check_validity_postgis_all(schema_name: str, export_invalid: bool = False) -> None:
    """Check geometry validity for all PostGIS tables.

    Check geometry validity for all PostGIS tables in particular schema
    by specifying schema name. For exporting invalid geometries as
    shapefiles (invalid polygons and error locations), put True within
    second parameter.

    Parameters
    ----------
    schema_name : str
        A string representing schema of PostGIS database from which
        will be all table geometries tested.
    export_invalid : str
        A boolean value for exporting invalid geometries of certain
        PostGIS tables. Default value is set up as False, so do not
        export these invalid geometries. To export these invalid
        ones, put True.
    """
    # Start time of checking process.
    start_time = time()
    # Inspect the database.
    inspector = inspect(engine)
    # Create list of tables in certain schema.
    tables = [
        table_name for table_name in inspector.get_table_names(schema=schema_name)
    ]
    # Create unique separator for printing purposes.
    single_sep = "-" * 70
    # Check all geometries for each table in particular PostGIS schema.
    for table in tables:
        # Converted PostGIS table into WKT.
        table_to_check = postgis_to_wkt(schema_name, table)
        # Number of invalid geometries in particular table.
        invalid_count = 0
        # List of invalid geometries in particular table.
        invalid_geom = []
        # Print overview of invalid geometries (cause and coordinates).
        invalidity = []
        print(f"Checking Validity Table: '{table}'")
        # Check geometry for each record (row).
        for geometry in table_to_check.geometry:
            # If geometry is not valid, print cause with coordinates,
            # put it into list with invalid geometries and add it into
            # counting.
            if not explain_validity(geometry) == "Valid Geometry":
                inv_reason = explain_validity(geometry)
                print(inv_reason)
                invalidity.append(inv_reason)
                invalid_geom.append(to_wkt(geometry))
                invalid_count += 1
            # If geometry is valid, pass.
            else:
                pass
        # If all geometries are valid, print statement about it.
        if invalid_count == 0:
            print(f"All geometries in table '{table}' are valid.", single_sep, sep="\n")
        # If there are some invalid geometries and these geometries need to be
        # exported, they will be saved as shapefiles. Also print number ot them
        # and destination of exported shapefiles.
        elif invalid_count > 0 and export_invalid is True:
            # Convert infromation about geometry from WKT into GeoSeries.
            geom_col = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="EPSG:5514")
            # Set up a new column with values stored in list above.
            inv_col = {"invalidity": invalidity}
            # Create GeoDataFrame from 'geom_col' as geometry and 'inv_col' as a
            # invalidity reason containg reason and coordinates.
            gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col, crs="EPSG:5514")
            # Path of destination directory (where will be invalid data saved).
            dest_dir_path = "./src/models/data/zc3_up_hrabisin/output/"
            # Save these invalid data as shapefiles.
            gdf.to_file(f"{dest_dir_path}{table}_invalid.shp", driver="ESRI Shapefile")
            # Stored path of each invalid shapefile.
            abs_path = os.path.abspath(f"{dest_dir_path}/{table}_invalid.shp")
            # Export point layer that include error locations.
            # Step 1 -> String containing characters to remove.
            to_remove_1 = (
                "RingSelf-intersectionSelf-intersectionToofewpointsingeometrycomponent "
            )
            # Step 2 -> Remove characters stored in 'to_remove' variable (error causes).
            stripped_1 = [w.strip(to_remove_1) for w in invalidity]
            # Step 3 -> String containing square brackets to remove.
            to_remove_2 = "[]"
            # Step 4 -> Remove square brackets and create list of strings including
            # coordinates of each error.
            stripped_2 = [w.strip(to_remove_2) for w in stripped_1]
            # Step 5 -> replace space separator by comma separator.
            sep_replaced = [b.replace(" ", ", ") for b in stripped_2]
            # Step 6 -> Convert list of string into list of tuples including
            # float coordinates prepared for exporting as points coordinates.
            coords_tuple = [tuple(map(float, i.split(","))) for i in sep_replaced]
            # Step 7 -> Create point geometry in WKT format.
            geom = [Point(v) for v in coords_tuple]
            # Step 8 -> Create GeoDataFrame including geometry column and column with
            # error causes.
            points_gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom, crs="EPSG:5514")
            # Step 9 -> Export GeoDataFrame as shapefile.
            points_gdf.to_file(
                f"{dest_dir_path}{table}_invalid_location.shp",
            )
            # Save absolute path of exported shapefile.
            abs_path_2 = os.path.abspath(
                (f"{dest_dir_path}/{table}_invalid_location.shp")
            )
            # Print infaromation about: which table contains invalid geometries,
            # number of invalid geometries and where these shapefiles were
            # saved (geometries with error and error locations).
            print(
                f"Number of invalid geometries: {invalid_count}.",
                f"Invalid geometries from table '{table} were saved to {abs_path}.",
                f"Invalid geometry locations from table '{table}' were saved to {abs_path_2}.",
                single_sep,
                sep="\n",
            )
        # If I do not need export invalied geometries, only print their number.
        else:
            print(
                f"Number of invalid geometries: {invalid_count}.", single_sep, sep="\n"
            )
    # In the end, print checking time.
    duration = time() - start_time
    print(f"Checking time: {duration:.2f} s.")
