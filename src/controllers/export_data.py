import os
import shutil
from time import time

from sqlalchemy import inspect
import geopandas as gpd

from src.models.output_tables import js_tables
from config import engine


def export_shp(
    schema_name: str, table_name: str, dest_dir_path: str, create_dest_dir: bool = False
) -> None:
    """Export single PostGIS table as a shapefile.

    Export single PostGIS table as a shapefile by
    specifying schema name, table name and path
    to destination diretory. If destination directory
    does not exist, put True.

    Parameters
    ----------
    schema_name : str
        A string representing schema name from which will be
        shapefile exported.
    table_name : str
        A string representing table name which will be exported
        as shapefile.
    dest_dir_path : str
        A String representing path to destination directory where
        output shapefile will be saved.
    create_dest_dir : bool
        Default values is False (do not create). If destination
        directory does not exist, put True.
    """
    # Start time of importing process.
    start_time = time()
    try:
        # Create destination directory.
        if create_dest_dir is True:
            # Set up destination directory.
            dir_path = f"{dest_dir_path}"
            # Create this destinaton directory.
            os.mkdir(dir_path)
        # Do not create destination directory.
        else:
            pass
        # SQL command for selecting particular table from particular schema.
        sql = f"SELECT * FROM {schema_name}.{table_name};"
        # Create GeoDataFrame from PostGIS table.
        gdf = gpd.GeoDataFrame.from_postgis(sql=sql, con=engine, geom_col="geometry")
        # Set up output shapefile names.
        if table_name == "reseneuzemi_p":
            output = js_tables[0]
        elif table_name == "uzemniprvkyrp_p":
            output = js_tables[1]
        elif table_name == "zastaveneuzemi_p":
            output = js_tables[2]
        elif table_name == "plochyrzv_p":
            output = js_tables[3]
        elif table_name == "uzemnirezervy_p":
            output = js_tables[4]
        elif table_name == "koridoryp_p":
            output = js_tables[5]
        elif table_name == "koridoryn_p":
            output = js_tables[6]
        elif table_name == "plochyzmen_p":
            output = js_tables[7]
        elif table_name == "plochypodm_p":
            output = js_tables[8]
        elif table_name == "vpsvpoas_p":
            output = js_tables[9]
        elif table_name == "vpsvpoas_l":
            output = js_tables[10]
        elif table_name == "uses_p":
            output = js_tables[11]
        elif table_name == "systemsidelnizelene_p":
            output = js_tables[12]
        else:
            output = js_tables[13]
        # Export GeoDataFrame as Shapefile.
        gdf.to_file(f"{dest_dir_path}/{output}.shp")
        # Create absolute path where exported Shapefile will be saved.
        abs_path = os.path.abspath(f"{dest_dir_path}/{output}.shp")
        # Record time of importing process.
        duration = time() - start_time
        # Print statements.
        print(
            f"Shapefile '{table_name}.shp' was succesfully exported as '{abs_path}'",
            f"Exporting time: {duration:.2f} s.",
            sep="\n",
        )
    except Exception as e:
        print(f"Exporting shapefile failed: {e}")


def export_all_shp(
    schema_name: str, dest_dir_path: str, create_dest_dir: bool = False
) -> None:
    """Export all PostGIS tables as shapefiles.

    Export all PostGIS tables as shapefiles from
    particular schema and specifying destination
    directory. If destination directory
    does not exist, put True.

    Parameters
    ----------
    schema_name : str
        A string representing schema name from which will be
        shapefile exported.
    table_name : str
        A string representing table name which will be exported
        as shapefile.
    dest_dir_path : str
        A String representing path to destination directory where
        output shapefile will be saved.
    create_dest_dir : bool
        Default values is False (do not create). If destination
        directory does not exist, put True.
    """
    start_time = time()
    # Inspect the database.
    inspector = inspect(engine)
    # Create list of tables in certain schema.
    tables = [
        table_name for table_name in inspector.get_table_names(schema=schema_name)
    ]
    try:
        # Create destination directory.
        if create_dest_dir is True:
            # Set up destination directory path with nested directory (Data).
            dir_path = f"{dest_dir_path}"
            # Create these nested directories.
            os.makedirs(dir_path)
        # Do not create destination directory.
        else:
            pass
        for table in tables:
            # SQL command for selecting particular table from particular schema.
            sql = f"SELECT * FROM {schema_name}.{table};"
            # Create GeoDataFrame from PostGIS table.
            gdf = gpd.GeoDataFrame.from_postgis(
                sql=sql, con=engine, geom_col="geometry"
            )
            # Set up output shapefile names.
            if table == "reseneuzemi_p":
                output = js_tables[0]
            elif table == "uzemniprvkyrp_p":
                output = js_tables[1]
            elif table == "zastaveneuzemi_p":
                output = js_tables[2]
            elif table == "plochyrzv_p":
                output = js_tables[3]
            elif table == "uzemnirezervy_p":
                output = js_tables[4]
            elif table == "koridoryp_p":
                output = js_tables[5]
            elif table == "koridoryn_p":
                output = js_tables[6]
            elif table == "plochyzmen_p":
                output = js_tables[7]
            elif table == "plochypodm_p":
                output = js_tables[8]
            elif table == "vpsvpoas_p":
                output = js_tables[9]
            elif table == "vpsvpoas_l":
                output = js_tables[10]
            elif table == "uses_p":
                output = js_tables[11]
            elif table == "systemsidelnizelene_p":
                output = js_tables[12]
            else:
                output = js_tables[13]
            # Export GeoDataFrame as Shapefile.
            gdf.to_file(f"{dest_dir_path}/{output}.shp")
            # Create absolute path where exported Shapefile will be saved.
            abs_path = os.path.abspath(f"{dest_dir_path}/{output}.shp")
            # Record time of importing process.
            duration = time() - start_time
            # Print statement.
            print(
                f"Shapefile '{output}.shp' was succesfully exported as '{abs_path}'",
            )

    # If some problem occurs, print error message.
    except Exception as e:
        print(f"Exporting shapefiles failed: {e}")
    # Finally, print importing time.
    finally:
        # Path of directory that wiil be zipped.
        zip_dir = f"{dest_dir_path}"
        # Create zip file (new zip file name - path, archive format, diretory path to zip)
        zipped_file = shutil.make_archive(zip_dir, "zip", zip_dir)
        # Final path of new zip file.
        zipped_file_path = f"{dest_dir_path}.zip"
        # If zip file was create, print below message.
        if os.path.exists(zipped_file_path):
            print(f"Shapefiles were zipped into {zipped_file}.")
        # If not, print error message.
        else:
            print("Zipping process failed!")
        # Record time of importing process.
        duration = time() - start_time
        # Print statement.
        print(f"Exporting time {duration:.2f} s.")
