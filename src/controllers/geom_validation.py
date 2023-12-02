import os
import re

import geopandas as gpd
from geopandas.geodataframe import GeoSeries
from shapely import from_wkt, to_wkt
from shapely.geometry import Point
from shapely.validation import explain_validity


def shp_to_wkt(shp_path: str) -> GeoSeries:
    """Convert ESRI Shapefile into a WKT.

    Convert single ESRI Shapefile into a WKT format by specifying
    path to this shapefile.

    Parameters
    ----------
    sha_path : str
        A string representing path to the single
        ESRI Shapefile. Need to import abosolute path.
    """
    # GeoSeries from shp.
    gdf_from_shp = gpd.read_file(shp_path)
    # Convert shp attribute (geometry) into wkt.
    return from_wkt(gdf_from_shp.geometry.to_wkt())


def check_validity_shp(shp_path: str) -> None:
    """Checking geometry validity of single ESRI Shapefile.

    Check geometry validity of single ESRI Shapefile that was converted
    into WKT format using shp_to_wkt() user function. Need to specify 
    path to shapefile as parameter for function converting shapefile 
    into WKT. It prints information about geometry validity within 
    particular shapefile.

    Parameters
    ----------
    shp_path : str
        A string representing path to this single 
        ESRI Shapefile. Need to import aboslute path.
    """

    # Converted shapefile into WKT.
    shp_to_check = shp_to_wkt(shp_path)
    # List of invalid geometries.
    invalid_geom = []
    # Print overview of invalid geometries (cause and coordinates).
    print("Checking Validity Details:")
    # Check geometry for each record (row).
    for geometry in shp_to_check:
        # If geometry is not valid, print cause with coordinates,
        # put it into list with invalid geometries. 
        if not explain_validity(geometry) == "Valid Geometry":
            print(explain_validity(geometry))
            invalid_geom.append(to_wkt(geometry))
        # If geometry is valid, pass.
        else:
            pass
    # If all geometries are valid.
    if len(invalid_geom) == 0:
        print("All geometries are valid.")
    # If there are some invalid geometries.
    else:
        invalid_msg = f"Number of invalid geometries: {len(invalid_geom)}."
        print("-" * 50, invalid_msg, sep="\n")


def check_validity_shp_dir(dir_path: str, verbose: bool = False, export: bool = False) -> None:
    """Checking geometry validity of all ESRI Shapefiles in directory.

    Check gometry validity of all ESRI Shapefiles in specific
    directory. Need to specify path to directory with shapefiles as 
    parameter for function converting shapefile into WKT. It prints 
    information about geometry validity within particular shapefile.

    Parameters
    ----------
    dir_path : str
        A string representing path to directory with shapefiles.
    verbose: bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export: bool
        A boolean value that specify order for exporting any invalid
        geometries, if exist. Default value is set up as False (not
        export). For exporting invalid geometries, put True.
    """
    # Create set of shapefiles (only *.shp needed).
    shps_to_check = set(
        shp.removesuffix(".shp") for shp in os.listdir(dir_path) if shp.endswith(".shp") 
    )
    for shp in shps_to_check:
        shp_to_check = shp_to_wkt(f"{dir_path}/{shp}.shp")
        # List of invalid geometries and cause.
        invalid_geom = []
        invalidity = []
        # Print overview of invalid geometries (cause and coordinates).
        print(f"Checking Validity Details: shapefile '{shp}.shp'")
        # Check geometry for each record (row).
        for geometry in shp_to_check:
            # If geometry is not valid put it into list with invalid geometries.
            if not explain_validity(geometry) == "Valid Geometry":
                inv_reason = explain_validity(geometry)
                invalidity.append(inv_reason)
                invalid_geom.append(to_wkt(geometry))

            # If geometry is valid, pass.
            else:
                pass
        
        # For each geometry extract invalidity reason only (using RegEx). 
        error_info = [re.sub(r'\[.*?]', '', f) for f in invalidity]
        # Set up a new column with values stored in list above.
        inv_col = {"invalidity": error_info}
        
        # For each geometry extract string coordinates only (using RegEx). 
        error_geom = [re.sub(r'^.*?\[|]', '', f) for f in invalidity] 
        # Convert list of string into list of tuples including
        # float coordinates prepared for exporting as points coordinates.
        coords_tuple = [tuple(map(float, f.split(" "))) for f in error_geom]
        # Crete list of Point geometries representing places where invalidity occurs
        geom_col_points = [Point(v) for v in coords_tuple]

        # If all geometries are valid, print statement about it.
        if len(invalid_geom) == 0:
            print(
                f"All geometries in shapefile {shp} are valid.",
                sep="\n",
            )
        # If there are some invalid geometries and these geometries need to be exported.
        elif len(invalid_geom) > 0 and export is True:
            # Convert information about geometry from WKT into GeoSeries.
            geom_col = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="EPSG:5514")
            # Create GeoDataFrame from 'geom_col' as geometry and 'inv_col' as a
            # invalidity reason containg reason and coordinates.
            gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col, crs="EPSG:5514")
            # Save these invalid data as shapefiles.
            gdf.to_file(f"{dir_path}/{shp.lower()}_invalid.shp")
            
            # Export point layer that include error locations.
            # Create GeoDataFrame including geometry column and column with error causes.
            points_gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col_points, crs="EPSG:5514")
            #  Export GeoDataFrame as shapefile.
            points_gdf.to_file(f"{dir_path}/{shp.lower()}_invalid_location.shp")
            if verbose is True:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) in {shp} due to:",
                    *error_info,
                    f"- Invalid geometries were saved as {shp.lower()}_invalid.shp",
                    f"- Invalid geometry locations (points) were saved as {shp.lower()}_invalid_location.shp.",
                    sep="\n",
                    end="\n" * 2,
                )
            else:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) in {shp}.",
                    f"- Invalid geometries were saved as {shp.lower()}_invalid.shp",
                    f"- Invalid geometry locations (points) were saved as {shp.lower()}_invalid_location.shp.",
                    sep="\n",
                    end="\n" * 2,
                )

        # If I do not need export invalied geometries.
        elif len(invalid_geom) > 0 and export is False:
            if verbose is True:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) in {shp} due to:",
                    *error_info,
                    sep="\n",
                    end="\n" * 2,
                )
            else:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) in {shp}.",
                    end="\n" * 2,
                )



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
    # List of invalid geometries and cause.
    invalid_geom = []
    invalidity = []
    # Check geometry for each record (row).
    for geometry in shp_to_check:
        # If geometry is not valid, print cause with coordinates,
        # and put them into list with invalid geometries.
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
    verbose: bool = False,
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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
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
        # List of invalid geometries and cause.
        invalid_geom = []
        invalidity = []
        # Check geometry for each record (row).
        for geometry in shp_to_check:
            # If geometry is not valid put it into list with invalid geometries.
            if not explain_validity(geometry) == "Valid Geometry":
                inv_reason = explain_validity(geometry)
                invalidity.append(inv_reason)
                invalid_geom.append(to_wkt(geometry))

            # If geometry is valid, pass.
            else:
                pass
        # For each geometry extract invalidity reason only (using RegEx). 
        error_info = [re.sub(r'\[.*?]', '', f) for f in invalidity]
        # Set up a new column with values stored in list above.
        inv_col = {"invalidity": error_info}
        
        # For each geometry extract string coordinates only (using RegEx). 
        error_geom = [re.sub(r'^.*?\[|]', '', f) for f in invalidity] 
        # Convert list of string into list of tuples including
        # float coordinates prepared for exporting as points coordinates.
        coords_tuple = [tuple(map(float, f.split(" "))) for f in error_geom]
        # Crete list of Point geometries representing places where invalidity occurs
        geom_col_points = [Point(v) for v in coords_tuple]

        # If all geometries are valid, print statement about it.
        if len(invalid_geom) == 0:
            print(
                f"OK: All geometries are valid.",
                end="\n" * 2
            )
        # If there are some invalid geometries and these geometries need to be
        # exported, they will be saved as shapefiles.
        elif len(invalid_geom) > 0 and export is True:
            # Convert information about geometry from WKT into GeoSeries.
            geom_col = gpd.GeoSeries.from_wkt(data=invalid_geom, crs="EPSG:5514")
            # Create GeoDataFrame from 'geom_col' as geometry and 'inv_col' as a
            # invalidity reason containg reason and coordinates.
            gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col, crs="EPSG:5514")
            # Save these invalid data as shapefiles.
            gdf.to_file(f"{dest_dir_path}/{shp.lower()}_invalid.shp")
            
            # Export point layer that include error locations.
            # Create GeoDataFrame including geometry column and column with error causes.
            points_gdf = gpd.GeoDataFrame(data=inv_col, geometry=geom_col_points, crs="EPSG:5514")
            #  Export GeoDataFrame as shapefile.
            points_gdf.to_file(f"{dest_dir_path}/{shp.lower()}_invalid_location.shp")
            # Print infaromation about: which table contains invalid geometries,
            # number of invalid geometries and output shapefile names. 
            if verbose is False:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}).",
                    f"- Invalid geometries were saved as {shp.lower()}_invalid.shp",
                    f"- Invalid geometry locations (points) were saved as {shp.lower()}_invalid_location.shp.",
                    sep="\n",
                    end="\n" * 2,
                )
            else:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) due to:",
                    *error_info,
                    f"- Invalid geometries were saved as {shp.lower()}_invalid.shp",
                    f"- Invalid geometry locations (points) were saved as {shp.lower()}_invalid_location.shp.",
                    sep="\n",
                    end="\n" * 2,
                )

        # If I do not need export invalied geometries.
        elif len(invalid_geom) > 0 and export is False:
            if verbose is False:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}).",
                    end="\n" * 2
                )
            else:
                print(
                    f"Error: There are invalid geometries ({len(invalid_geom)}) due to:",
                    *error_info,
                    sep="\n",
                    end="\n" * 2
                )
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(invalid_geom) 
