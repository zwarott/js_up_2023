import warnings

import geopandas as gpd
from shapely.geometry import Polygon 

from src.models.output_tables import js_tables
from src.models.attributes import column_info
from src.controllers.geom_validation import validity_shp_zip


def shp_within_mun(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    verbose: bool = False,
    export: bool = False,
) -> int:
    """Checking shapefile within ReseneUzemi_p shapefile.

    Check, if shapefile is within ReseneUzemi_p shapefile.
    If not, create difference of certain shapefile and ReseneUzemi_p
    shapefile and if needed, export these as new shapefile. For more 
    details about errors, set up verbose mode as True.

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
        A shapefile name (within zip dir), for which are these 
        relationships tested.
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
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

    geom_out = []
    try:
        # If shapefile is valid, run process below.
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            # Input shapefile.
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp",
            )
            # Create GeoDataFrame from ReseneUzemi_p shapefile.
            mun_borders_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ReseneUzemi_p.shp",
            )
            # Create Polygon geometry from GeoDataFrame coordinates.
            borders_polygon = Polygon(mun_borders_gdf.geometry.get_coordinates())
            # Create list with attribute names from GeoDataFrame.
            attrs_to_check = shp_gdf.columns.tolist()
            # If GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [attr for attr in attrs_to_check if attr.lower() == column_info[shp.lower()]]
            # For each geometry check if is within ReseneUzemi_p. If so, append this feature into the list (info + geom).
            column_export = []
            # If mandatory attribute is included.
            if shp in js_tables and len(mandatory_col_info) > 0:
                for i in range(shp_gdf.geometry.count()):  
                # If geometry is not fully within ReseneUzemi_p.
                    if shp_gdf.geometry[i].within(borders_polygon) is False:
                        column_export.append(shp_gdf[mandatory_col_info[0]][i])
                        geom_out.append(shp_gdf.geometry[i].difference(borders_polygon))
                    else:
                        pass
            # If mandatory attribute is not included.
            else:
                for i in range(shp_gdf.geometry.count()):  
                    if shp_gdf.geometry[i].within(borders_polygon) is False:
                        # Append info from first attribute.
                        column_export.append(shp_gdf.iloc[:, 0][i])
                    else:
                        pass

            # If all geometries are within ReseneUzemi_p.
            if len(geom_out) == 0:
                print(
                    f"Ok: All geometries are within ReseneUzemi_p.",
                    end="\n" * 2
                )
            # If there are some geometries outside and need to export errors.
            elif len(geom_out) > 0 and export is True:
                # Prepare info attribute for exporting.
                info_col = {"info": column_info}
                # Filter polygon geometry type only.
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
                
                if verbose is True:
                    # If mandatory attribute is missing.
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            f"- These geometries were saved as {shp.lower()}_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        ) 
                    else:
                        print(
                f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}) near features:",
                            *column_export,
                            f"- These geometries were saved as {shp.lower()}_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        )
                    
                else:
                    print(
                        f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}).",
                        f"- These geometries were saved as {shp.lower()}_outside.shp.",
                        sep="\n",
                        end="\n" * 2
                    )
                    
            # If I do not need export errors, but print number of features outside only.
            elif len(geom_out) > 0 and export is False:
                if verbose is True:
                    # If mandatory attribute is missing.
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            end="\n" * 2
                        ) 
                    else:
                        print(
                            f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}) near features:", 
                            *column_export,
                            sep="\n",
                            end="\n" * 2
                        )
                else:
                    print(
                        f"Error: There are geometries outside ReseneUzemi_p ({len(geom_out)}).",
                        end="\n" * 2
                    )

        # If invalid geometries occur.
        else:
            print(
                "Error: Checking features within ReseneUzemi_p cannot be run due to invalid geometries.",
                  end="\n" * 2
            )
    
    # If any type of error occurs.
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(geom_out) 


def check_gaps(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int, 
    shp: str, 
    verbose: bool = False,
    export: bool = False
) -> int:
    """Checking gaps within certain shapefile.

    Check gaps between geometries within certain shapefile
    stored in zip file.

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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
       A boolean value for exporting gaps within certain shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.
    
    Returns
    -------
    int
        Number of gaps within certain shapefile.
    """

    errors = 0
    try:
        # If input shapefile is valid.
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            )
            # Dissolve all rows (geometries) into one.
            dissolved = shp_gdf.dissolve()
            # Ignore UserWarning.
            warnings.filterwarnings("ignore", "Only Polygon objects", UserWarning)
            # Create list of interior geometries, if exist.
            # interiors method creates Series of list representing the inner rings
            # of each polygon in the GeoSeries. tolist() method converts Series into
            # list. We need to specify 0 index, because we have these inner rings already
            # listed.
            interior = dissolved.geometry.interiors.tolist()[0]
            
            # Create list with attribute names from GeoDataFrame.
            attrs_to_check = shp_gdf.columns.tolist()
            # If GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [col for col in attrs_to_check if col.lower() == column_info[shp.lower()]]
            # Export info from geometry that touches interiors. 
            column_export = []
            # If mandatory attribute exists.
            if shp in js_tables and len(mandatory_col_info) > 0:
                for i in range(shp_gdf.geometry.count()):  
                    if shp_gdf.geometry[i].touches(interior):
                        column_export.append(shp_gdf[mandatory_col_info[0]][i])
                    else:
                        pass

            else:
                for i in range(shp_gdf.geometry.count()):  
                    if shp_gdf.geometry[i].touches(interior):
                        column_export.append(shp_gdf[mandatory_col_info[0]][i])
                    else:
                        pass
            
            # If there are not any gaps.
            if interior is None or len(interior) == 0:
                print(f"Ok: There are no gaps.",
                      end="\n" * 2
                      )
            # If there are gaps and I need export them.
            elif len(interior) > 0 and export is True:
                # Append 1 to errors variable for status purposes.
                errors += 1
                # Prepare info attribute for exporting.
                info_col = {"info": column_export}
                gaps_polygons = [Polygon(a) for a in interior]
                interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="EPSG:5514")
                interior_gdf = gpd.GeoDataFrame(data=info_col, geometry=interior_geom, crs="EPSG:5514")
                interior_gdf.to_file(
                    f"{dest_dir_path}/{shp.lower()}_gaps.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                if verbose is True:
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are gaps ({len(interior)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            f"- Gaps were saved as {shp.lower()}_gaps.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are gaps ({len(interior)}) near features:",
                            *column_export,
                            f"- Gaps were saved as {shp.lower()}_gaps.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are gaps ({len(interior)}).",
                        f"- Gaps were saved as {shp.lower()}_gaps.shp.",
                        sep="\n",
                        end="\n" * 2,
                    )
            # If there are gaps, but I need to print info about them only.
            elif len(interior) > 0 and export is False:
                errors += 1
                if verbose is True:
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are gaps ({len(interior)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            end="\n" * 2,
                            )
                    else:
                        print(
                            f"Error: There are gaps ({len(interior)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2
                        )
                else:
                    print(
                        f"Error: There are gaps ({len(interior)}).",
                        end="\n" * 2
                    )
        else:
            errors += 1
            print(
                "Error: Checking gaps cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors


def check_overlaps(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    verbose: bool = False,
    export: bool = False,
) -> int:
    """Checking overlaps within certain shapefile.

    Check overlaps between geometries within each shapefile stored in
    zipped file. 

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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
       A boolean value for exporting overlapping geometries of certain
       shapefile. Default value is set up as False (for not exporting
       these overlapping geometries). For exporting overlaps, put True.

    Returns
    -------
    int
        Number of overlapping geometries within certain shapefile.
    """
    try:
        intersected = []
        # If input shapefile si valid.
        if validity_shp_zip(zip_dir, mun_code, shp) == 0:
            # Create GeoDataFrame
            shp_gdf = gpd.read_file(
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
            )
            # Ignore RuntimeWarning.
            warnings.filterwarnings("ignore", "invalid value encountered", RuntimeWarning)
            # Create list with attribute names from GeoDataFrame.
            attrs_to_check = shp_gdf.columns.tolist()
            # If GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [col for col in attrs_to_check if col.lower() == column_info[shp.lower()]]
            
            column_export = []
            # If mandatory attribute exists.
            if shp in js_tables and len(mandatory_col_info) > 0:
                for i in range(shp_gdf.geometry.count()):  
                    if shp_gdf.geometry[i].overlaps(shp_gdf.geometry).any():
                        column_export.append(shp_gdf[mandatory_col_info[0]][i])
                    else:
                        pass

            else:
                for i in range(shp_gdf.geometry.count()):  
                    if shp_gdf.geometry[i].overlaps(shp_gdf.geometry).any():
                        # If mandatory attributes do not exist, export info
                        # from first attribute.
                        column_export.append(shp_gdf.iloc[:, 0][i])
                    else:
                        pass

            # Create list with overlapping geometries.
            overlapping_geom = [row for row in shp_gdf.geometry if row.overlaps(shp_gdf.geometry).any()]
            # For each feature stored in list (overlapping) export
            # overlapping parts and store them into list (intersected).
            for part_f in overlapping_geom:
                for sing_f in [oth_f for oth_f in overlapping_geom if oth_f != part_f]:
                    if part_f.overlaps(sing_f):
                        intersected.append(part_f.intersection(sing_f))
            # Create Geoseries from intersected geometries.
            inters_geom = gpd.GeoSeries(intersected)
            # Convert GeometryCollections and Multipolygons into Polygons, Polylines and Points.
            # If index_parts = True, column with index parts will be created.
            geom_exploded = inters_geom.explode(index_parts=True)
            # Filter Polygons only.
            polyg_only = [x for x in geom_exploded if x.geom_type == "Polygon"]
            
            # If there are no overlaps (polygon parts), print statement.
            if len(polyg_only) == 0:
                print("Ok: There are no overlaps.",
                      end="\n" * 2)
            # If there are overlaps and I need to export them.
            elif len(polyg_only) > 0 and export is True:
                info_col = {"info": column_export}
                gdf_overlaps = gpd.GeoDataFrame(geometry=polyg_only, crs="EPSG:5514")
                gdf_overlaps.to_file(
                    f"{dest_dir_path}/{shp.lower()}_overlaps.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                
                if verbose is True:
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are overlaps ({len(polyg_only)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            f"- Overlaps were saved as {shp.lower()}_overlaps.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )

                    else:
                        print(
                            f"Error: There are overlaps ({len(polyg_only)}) near features:",
                            *column_export,
                            f"- Overlaps were saved as {shp.lower()}_overlaps.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )

                else:
                    print(
                        f"Error: There are overlaps ({len(polyg_only)}).",
                        f"- Overlaps were saved as {shp.lower()}_overlaps.shp.",
                        sep="\n",
                        end="\n" * 2,
                    )
            # If there are overlaps, but I do not need to export them.
            elif len(polyg_only) > 0 and export is False:
                if verbose is True:
                    if len(mandatory_col_info) == 0 and shp in js_tables:
                        print(
                            f"Error: There are overlaps ({len(polyg_only)}) with missing mandatory attribute {column_info[shp.lower()]}.",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are overlaps ({len(polyg_only)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2,
                        )
    
                else:
                    print(
                        f"Error: There are overlaps ({len(polyg_only)}).",
                        end="\n" * 2,
                    )

        else:
            print(
                "Error: Checking overlaps cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(intersected)
