import os
from time import time

import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame, GeoSeries
from sqlalchemy import inspect
from shapely import from_wkt, to_wkt
from shapely.validation import explain_validity

from config import engine


def postgis_to_wkt(schema_name: str, table_name: str) -> GeoDataFrame:
    """Convert PostGIS table into a WKT.

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
        crs="epsg:5514", sql=sql, con=engine, geom_col="geometry"
    )
    # Return geometry attribute in WKT.
    return from_wkt(gdf_from_postgis.to_wkt())


def shp_to_wkt(shp_path: str) -> GeoSeries:
    """Convert ESRI Shapefile intp a WKT.

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


def check_validity_postgis(schema_name: str, table_name: str) -> list:
    """Check gaometry validity of PostGIS table.

    Check geometry validity of PostGIS table that was converted
    into WKT format using postgis_to_wkt() user funtion. Need to
    specify schema name and table name as parameters for function
    converting PostGIS table into WKT. Returns list of invalid
    geometries.

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
    return invalid_geom


def check_validity_postgis_all(schema_name: str, export_invalid: bool = False) -> None:
    """Check geometry validity for all PostGIS tables.

    Check geometry validity for all PostGIS tables in particular schema
    by specifying schema name. For exporting invalid geometries as
    shapefiles, put True within second parameter.

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
        print(f"Checking Validity Table: '{table}'")
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
            print(f"All geometries in table '{table}' are valid.", single_sep, sep="\n")
        # If there are some invalid geometries and these geometries need to be
        # exported, they will be saved as shapefiles. Also print number ot them
        # and destination of exported shapefiles.
        elif invalid_count > 0 and export_invalid is True:
            gdf = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="epsg:5514")
            dest_dir_path = "./src/models/data/zc3_up_hrabisin/output/"
            gdf.to_file(f"{dest_dir_path}{table}_invalid.shp")
            abs_path = os.path.abspath(f"{dest_dir_path}/{table}.shp")
            print(
                f"Number of invalid geometries: {invalid_count}.",
                f"Invalid geometries from table '{table} were saved to {abs_path}",
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
