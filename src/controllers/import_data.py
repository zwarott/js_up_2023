import os
from time import time

import geopandas as gpd
from config import engine, conn


def import_shp(shp_path: str, schema_name: str, create_schema: bool = False) -> None:
    """Import single shapefile into a PostGIS database.

    Import a single shapefile into the particular schema in
    PostGIS database specifying path to this shapefile. If
    this schema does not exist, put True to create.

    Parameters
    ----------
    shp_path : str
        A string representing path to shapefile that will be
        imported into a PostGIS database.
    schema_name : str
        A string representing schema name into that will be
        shapefile imported.
    create_schema : bool
        A boolean value, default value is set up as False ->
        do not create a new schema. If True, schema will be
        created.
    """
    # Start time of importing process.
    start_time = time()

    # Open a cursor to perform database operations.
    cur = conn.cursor()

    try:
        # Create particular schema.
        if create_schema is True:
            cur.execute(f"CREATE SCHEMA {schema_name};")
            conn.commit()
        # Do not create new schema (default state).
        else:
            pass
        # Commit changes in database.
        conn.commit()
        # Separate shapefile name only (without .shp).
        shp_to_import = os.path.basename(shp_path)[:-4]
        # Create GeoDataFrame.
        gdf = gpd.read_file(shp_path)
        # Create list of columns from created GeoDataFrame.
        col_names_old = list(gdf.columns)
        # Convert each column into lowercase.
        for col in col_names_old:
            gdf = gdf.rename(columns={str(col): str(col.lower())})
        # Set up particular CRS + EPSG for GeoDataFrame.
        gdf = gdf.set_crs(5514, "epsg:5514", allow_override=True)
        # Import GeoDataFrame into PostGIS database as a table
        # with lowercase name.
        table_name = shp_to_import.lower()
        gdf.to_postgis(name=f"{table_name}", con=engine, schema=f"{schema_name}")

        # Close communication with the database.
        cur.close()
        # Close connection with the database.
        conn.close()
        print(
            f"Shapefile was succesfully imported into the schema '{schema_name}' as '{table_name}' table."
        )

    except Exception as e:
        print(f"Importing shapefile failed: {e}.")

    finally:
        # Record time of importing process.
        duration = time() - start_time
        # Print statemenst.
        print(f"Importing time: {duration:.2f} s.")


def import_all_shp(
    dir_path: str, schema_name: str, create_schema: bool = False
) -> None:
    """Import shapefiles into a PostgreSQL.

    Import shapefiles into the selected schema in PostgreSQL
    database defining directory path and schema name.

    Parameters
    ----------
    dir_path : str
        A string representing path to direcrtory containing
        shapefiles.
    schema_name : str
        A string representing name of schema in PostgreSQL
        database.
    create_schema : bool
        A boolean value, default value is set up as False ->
        do not create a new schema. If True, schema will be
        created.
    """
    # Start time of importing process.
    start_time = time()

    # Open a cursor to perform database operations.
    cur = conn.cursor()
    try:
        # Create particular schema.
        if create_schema is True:
            cur.execute(f"CREATE SCHEMA {schema_name};")
            conn.commit()
        # Do not create new schema (default state).
        else:
            pass
        # Commit changes in database.
        conn.commit()

        # Create set of shapefiles (only *.shp needed).
        shp_to_import = set(
            shp[:-4]
            for shp in os.listdir(dir_path)
            if ".shp" in shp and "xml" not in shp
        )
        for shp in shp_to_import:
            # Read each shapefile.
            gdf = gpd.read_file(f"{dir_path}/{shp}.shp")
            # Create list of columns from each shapefile.
            col_names_old = list(gdf.columns)
            # Convert each column into lowercase.
            for col in col_names_old:
                gdf = gdf.rename(columns={str(col): str(col.lower())})
            # Set up particular CRS + EPSG for each shapefile.
            gdf = gdf.set_crs(5514, "epsg:5514", allow_override=True)
            # Export each shapefile into PostGIS database.
            table_name = shp.lower()
            gdf.to_postgis(name=f"{table_name}", con=engine, schema=f"{schema_name}")
            print(
                f"Shapefile '{shp}' was succesfully imported into the schema '{schema_name}' as '{table_name}' table."
            )

        # Close communication with the database.
        cur.close()
        # Close connection with the database.
        conn.close()

    except Exception as e:
        print(f"Importing shapefiles failed: {e}")

    finally:
        # Record time of importing process.
        duration = time() - start_time
        # Print statemenst.
        print(f"Importing time: {duration:.2f} s.")
