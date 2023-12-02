import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon 

from src.controllers.geom_validation import validity_shp_zip


def covered_mun_both(
    zip_dir: str, 
    dest_dir_path: str, 
    mun_code: int,
    verbose: bool = False,
    export: bool = False
) -> int:
    """Checking covering whole ReseneUzemi_p area.

    Check, if whole ReseneUzemi_p shapefile is covered by merged shapefiles 
    (PlochyRZV_p and KoridoryP_p shapefiles) - no gaps, no overlaps. Returns 
    number of geometries that do not cover ReseneUzemi_p.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    verbose : bool
        A boolean value for printing statements in verbose mode 
        (near which features errors occur). Default values is 
        set up as False (for not printing statements in verbose mode). 
        To do so, put True.
    export : bool
       A boolean value for exporting area differences between ReseneUzemi_p
       shapefile and merged PlochyRZV_p and KoridoryP_p shapefiles. Default value
       is set up as False (for not exporting these differences). For exporting
       these differences, put True.

    Returns
    -------
    int
        Integer that indicates error occurrences (0 -> no errors, 1 -> errors occur).
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
            # Explode multiparts geometries into single geometries (list to rows).
            exploded = gdf_diff.explode(index_parts=False)

            # Create list with attribute names from GeoDataFrame.
            attrs_to_check = merged.columns.tolist()
            # If merged GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [attr for attr in attrs_to_check if attr.lower() in ["typ", "id"]]
            # Replace NaN values in merged GeoDataFrame by None ones.
            merged_mod = merged.where(pd.notnull(merged), None) 
            column_export = []
            # If mandatory attribute is included.
            if len(mandatory_col_info) == 2:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(exploded.geometry).any():
                        if merged_mod[mandatory_col_info[0]][i] is None:
                            column_export.append(merged_mod[mandatory_col_info[1]][i])
                        else:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                    else:
                        pass

            elif len(mandatory_col_info) == 1:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(exploded.geometry).any():
                        if merged_mod[mandatory_col_info[0]][i] is not None:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                        else:
                            column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass

            else:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(exploded.geometry).any():
                        column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass

            if diff is None:
                print(
                    f"Ok: All geometries from PlochyRZV_p and KoridoryP_p cover ReseneUzemi_p.",
                    end="\n" * 2
                )
            # If there are some differences and export = True, export them
            # as shapefile and print statements about differences.
            elif diff is not None and export is True:
                errors += 1
                # Prepare info attribute for exporting.
                info_col = {"info": column_export}
                gdf_error = gpd.GeoDataFrame(data=info_col, geometry=exploded.geometry, crs="EPSG:5514")
                gdf_error.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="EPSG:5514",
                )
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attributes id and typ.",
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attribute {missing_attr[0]}.",
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are geomeries not covering ReseneUzemi_p ({len(exploded.geometry)}) near features:",
                            *mandatory_col_info,
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}).",
                        "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                        sep="\n",
                        end="\n" * 2,
                    )


            # If export = False, print info about differences only.
            elif diff is not None and export is False:
                errors += 1
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attributes id and typ.",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attribute {missing_attr[0]}.",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) near features:",
                            *mandatory_col_info,
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}).",
                        end="\n" * 2,
                    )

        else:
            errors += 1
            print(
                "Error: Checking covering ReseneUzemi_p by PlochyRZV_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors 


def covered_mun_przv(
    zip_dir: str, 
    dest_dir_path: str, 
    mun_code: int, 
    verbose: bool = False,
    export: bool = False
    ) -> int: 
    """Checking covering ReseneUzemi_p by PlochyRZV_p.

    Check, if whole ReseneUzemi_p shapefile is covered by PlochyRZV_p 
    shapefile - no gaps, no overlaps. Returns number of geometries 
    that do not cover ReseneUzemi_p.
    
    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
       A unique code of particular municipality, for which
       are these relationships tested.
    verbose : bool
        A boolean value for printing statements in verbose mode 
        (near which features errors occur). Default values is 
        set up as False (for not printing statements in verbose mode). 
        To do so, put True.
    export : bool
       A boolean value for exporting area differences between ReseneUzemi_p
       shapefile and geometries from PlochyRZV_p that do not cover
       ReseneUzemi_p. Default value is set up as False (for not exporting 
       these differences). For exporting these differences, put True.
    
    Returns
    -------
    int
        Integer that indicates error occurrences (0 -> no errors, 1 -> errors occur).
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
            # Explode multiparts geometries into single geometries (list to rows).
            exploded = gdf_diff.explode(index_parts=False)

            # Create list with attribute names from GeoDataFrame.
            attrs_to_check = plochy_rzv.columns.tolist()
            # If merged GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [attr for attr in attrs_to_check if attr.lower() in ["typ"]]
            column_export = []
            # If mandatory attribute is included.
            if len(mandatory_col_info) == 1:
                for i in range(plochy_rzv.geometry.count()):  
                    if plochy_rzv.geometry[i].touches(exploded.geometry).any():
                        column_export.append(plochy_rzv[mandatory_col_info[0]][i])
                    else:
                        pass
            else:
                for i in range(plochy_rzv.geometry.count()):  
                    if plochy_rzv.geometry[i].touches(exploded.geometry).any():
                        column_export.append(plochy_rzv.iloc[:, 0][i])
                    else:
                        pass

            # If there is no differences, print statement only.
            if diff is None:
                print(
                    "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                    "Ok: All geometries in PlochyRZV_p cover ReseneUzemi_p.",
                    sep="\n",
                    end="\n" * 2,
                )
            # If there are some differences and export = True, export them
            # as shapefile and print statements about differences.
            elif diff is not None and export is True:
                errors += 1
                # Prepare info attribute for exporting.
                info_col = {"info": column_export}
                gdf_error = gpd.GeoDataFrame(data=info_col, geometry=exploded.geometry, crs="EPSG:5514") 
                gdf_error.to_file(
                    f"{dest_dir_path}/not_cover_reseneuzemi_p.shp",
                    driver="ESRI Shapefile",
                    crs="5514",
                )
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attribute typ.",
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) near features:",
                            *column_export,
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                        f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}).",
                        "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                        sep="\n",
                        end="\n" * 2,
                    )
            # If export = false, print info about differences only.
            elif diff is not None and export is False:
                errors += 1
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) with missing attribute typ.",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                            f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        "Warning: Covering ReseneUzemi_p was checked with PlochyRZV_p layer only, because KoridoryP_p layer is missing.",
                        f"Error: There are geometries not covering ReseneUzemi_p ({len(exploded.geometry)}) near features:",
                        sep="\n",
                        end="\n" * 2,
                    )
        else:
            errors += 1
            print(
                "Error: Checking covering ReseneUzemi_p by PlochyRZV_p cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors 


def check_gaps_covered(
    zip_dir: str, 
    dest_dir_path: str,
    mun_code: int, 
    verbose: bool = False,
    export: bool = False
) -> int:
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
    verbose : bool
        A boolean value for printing statements in verbose mode 
        (near which features errors occur). Default values is 
        set up as False (for not printing statements in verbose mode). 
        To do so, put True.
    export : bool
       A boolean value for exporting gaps of certain shapefile.
       Default value is set up as False (for not exporting
       these gaps). For exporting these gaps, put True.

    Returns
    -------
    int 
        Integer that indicates error occurrences (0 -> no errors, 1 -> errors occur).
    """
    try:
        errors = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "KoridoryP_p") == 0
        ):
            # Path to PlochyRZV_p.shp.
            plochy_rzv_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Path to KoridoryP_p.shp.
            koridory_p_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/KoridoryP_p.shp"
            )
            # Create GeoDataFrames from shapefiles above.
            plochy_rzv_gdf = gpd.read_file(plochy_rzv_path)
            koridory_p_gdf = gpd.read_file(koridory_p_path)
            # Merge noth GeoDataFrames.
            merged = plochy_rzv_gdf.sjoin(koridory_p_gdf)
            # Dissolve merged GeoDataFrames.
            dissolved = merged.dissolve()
            # Create list of interior geometries, if exist.
            # interiors method creates Series of list representing the inner rings
            # of each polygon in the GeoSeries. tolist() method converts Series into
            # list. We need specify 0 index, because we have these inner rings already
            # listed. See interiors and tolist() method for more info.
            interior = dissolved.geometry.interiors.tolist()[0]
            # Create list with attribute names from merged GeoDataFrame.
            attrs_to_check = merged.columns.tolist()
            # If merged GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [attr for attr in attrs_to_check if attr.lower() in ["typ", "id"]]
            # Replace NaN values in merged GeoDataFrame by None ones.
            merged_mod = merged.where(pd.notnull(merged), None) 
            # For each geometry check if touches any gaps. If so, append this feature into list empty list.
            column_export = []
            # If both mandatory attributes are included.
            if len(mandatory_col_info) == 2:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(interior).any():
                        if merged_mod[mandatory_col_info[0]][i] is None:
                            column_export.append(merged_mod[mandatory_col_info[1]][i])
                        else:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                    else:
                        pass

            elif len(mandatory_col_info) == 1:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(interior).any():
                        if merged_mod[mandatory_col_info[0]][i] is not None:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                        else:
                            column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass

            else:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].touches(interior).any():
                        column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass

            # If there are no inner rings, print info about it only.
            if interior is None or len(interior) == 0:
                print(
                    "OK: There is no gaps between PlochyRZV_p and KoridoryP_p.",
                    end="\n" * 2,
                )
            # If there are some inner rings, exported them as shapefile and print
            # number of inner rings and where these inner rings are stored.
            elif len(interior) > 0 and export is True:
                errors += 1
                # Prepare info attribute for exporting.
                info_col = {"info": column_export}
                gaps_polygons = [Polygon(a) for a in interior]
                interior_geom = gpd.GeoSeries(data=gaps_polygons, crs="EPSG:5514")
                interior_gdf = gpd.GeoDataFrame(data=info_col, geometry=interior_geom, crs="EPSG:5514")
                interior_gdf.to_file(
                    f"{dest_dir_path}/covered_gaps.shp",
                    driver="ESRI Shapefile",
                    crs="ESPG:5514",
                )
                
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p {len(interior)} with missing mandatory attributes typ and id.",
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}) with missing attribute {missing_attr[0]}.",
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}) near features:",
                            *column_export,
                            "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}).",
                        "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                        sep="\n",
                        end="\n" * 2,
                    )

            # If export = False, print number of inner rings only.
            elif len(interior) > 0 and export is False:
                errors += 1
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p {len(interior)} with missing mandatory attributes typ and id.",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}) with missing attribute {missing_attr[0]}.",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are gaps between PlochyRZV_p and KoridoryP_p ({len(interior)}).",
                        end="\n" * 2,
                    )

        else:
            errors += 1
            print(
                "Error: Gaps between PlochyRZV_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors


def overlaps_covered_mun(
    zip_dir: str, 
    dest_dir_path: str,
    mun_code: int, 
    verbose: bool = False,
    export: bool = False
) -> int:
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
    verbose : bool
        A boolean value for printing statements in verbose mode 
        (near which features errors occur). Default values is 
        set up as False (for not printing statements in verbose mode). 
        To do so, put True.
    export : bool
       A boolean value for exporting overlapping geometries of certain
       shapefile. Default value is set up as False (for not exporting
       these overlapping geometries). For exporting these overlaps, put True.
    
    Returns
    -------
    int
        Integer that indicates error occurrences (0 -> no errors, 1 -> errors occur).
    """
    try:
        errors = 0
        if (
        validity_shp_zip(zip_dir, mun_code, "PlochyRZV_p") == 0
        and validity_shp_zip(zip_dir, mun_code, "KoridoryP_p") == 0
        ):
            # Path to PlochyRZV_p shapefile.
            plochy_rzv_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyRZV_p.shp"
            )
            # Path to KoridoryP_p shapefile.
            koridory_p_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/KoridoryP_p.shp"
            )
            # Create GeoDataFrames from these shapefiles.
            plochy_rzv_gdf = gpd.read_file(plochy_rzv_path)
            koridory_p_gdf = gpd.read_file(koridory_p_path)
            # Merge both GeoDataFrames for info purposes.
            merged = plochy_rzv_gdf.sjoin(koridory_p_gdf)
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
            # Explode multiparts geometries into single geometries (list to rows).
            # If index_parts = False, index_parts will be not exported as a new column.
            exploded = gdf_inter.explode(index_parts=False)
            polyg_only = [x for x in exploded if x.geom_type == "Polygon"]
            
            # Create list with attribute names from merged GeoDataFrame.
            attrs_to_check = merged.columns.tolist()
            # If merged GeoDataFrame includes mandatory attribute for exporting info, put it into list.
            mandatory_col_info = [attr for attr in attrs_to_check if attr.lower() in ["typ", "id"]]
            # Replace NaN values in merged GeoDataFrame by None ones.
            merged_mod = merged.where(pd.notnull(merged), None) 

            column_export = []
            # If both mandatory attributes are included.
            if len(mandatory_col_info) == 2:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].overlaps(polyg_only).any():
                        if merged_mod[mandatory_col_info[0]][i] is None:
                            column_export.append(merged_mod[mandatory_col_info[1]][i])
                        else:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                    else:
                        pass

            elif len(mandatory_col_info) == 1:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].overlaps(polyg_only) is True:
                        if merged_mod[mandatory_col_info[0]][i] is not None:
                            column_export.append(merged_mod[mandatory_col_info[0]][i])
                        else:
                            column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass

            else:
                for i in range(merged_mod.geometry.count()):  
                    if merged_mod.geometry[i].overlaps(polyg_only) is True:
                        column_export.append(merged_mod.iloc[:, 0][i])
                    else:
                        pass
            
            # If there are not any overlaps.
            if len(polyg_only) == 0:
                print(
                    "Ok: There are no overlaps between PlochyRZV_p and KoridoryP_p.",
                    end="\n" * 2
                )
            # If there are some intersections and export_inter = True, export them
            # as shapefile and print statements about intersections.
            elif len(polyg_only) > 0 and export is True:
                errors += 1
                exploded.to_file(
                    f"{dest_dir_path}/plochy_rzv_koridory_p_overlaps.shp",
                    driver="ESRI Shapefile",
                    crs="ESPG:5514",
                )
                
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p {len(polyg_only)} with missing mandatory attributes typ and id.",
                            "- These geometries were saved as plochy_rzv_koridory_p_overlaps.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}) with missing attribute {missing_attr[0]}.",
                            "- These geometries were saved as plochy_rzv_koridory_p_overlaps.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}) near features:",
                            *column_export,
                            "- These geometries were saved as plochy_rzv_koridory_p_overlaps.shp",
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}).",
                        "- These geometries were saved as not_cover_reseneuzemi_p.shp",
                        sep="\n",
                        end="\n" * 2,
                    )

            # If export = False, print statement about differences.
            elif len(polyg_only) > 0 and export is False:
                errors += 1
                if verbose is True:
                    if len(mandatory_col_info) == 0:
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p {len(polyg_only)} with missing mandatory attributes typ and id.",
                            end="\n" * 2,
                        )
                    elif len(mandatory_col_info) == 1:
                        missing_attr = [attr for attr in ["typ", "id"] if attr not in mandatory_col_info]
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}) with missing attribute {missing_attr[0]}.",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2,
                        )
                else:
                    print(
                        f"Error: There are overlaps between PlochyRZV_p and KoridoryP_p ({len(polyg_only)}).",
                        end="\n" * 2,
                    )
        else:
            errors += 1
            print(
                "Error: Overlaps between KoridoryP_p and KoridoryP_p cannot be run due to invalid geometries.",
                  end="\n" * 2
            )

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    return errors
