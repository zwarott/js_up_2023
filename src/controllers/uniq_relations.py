import geopandas as gpd

from src.controllers.geom_validation import validity_shp_zip
from src.controllers.general_relations import shps_in_zip
from src.models.output_tables import js_tables


def vu_within_uses(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    verbose: bool = False,
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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
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
            # Path to VpsVpoAs_p shapefile.
            vpsvpoas_p_path = (
                f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/VpsVpoAs_p.shp"
            )
            # Create GeoDataFrame from path above.
            vpsvpoas_gdf = gpd.read_file(vpsvpoas_p_path)
            # Check if vpsvpoas_p GeoDataFrame contains id mandatory attribute, If so, this mandatory attribute
            # is appended into an empty list.
            id_attr = [attr for attr in vpsvpoas_gdf.columns.tolist() if attr.lower == "id"]
            # If VpsVpoAs_p and USES_p geometries are valid, mandatory attribute and specific values are included. 
            if (
                validity_shp_zip(zip_dir, mun_code, "VpsVpoAs_p") == 0 and validity_shp_zip(zip_dir, mun_code, "USES_p") == 0 
                and id_attr == 1 and vpsvpoas_gdf[id_attr[0]].str.startswith("VU").any() 
            ):
                # Path to USES_p shapefile.
                uses_p_path = (
                    f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/USES_p.shp"
                )
                # Create GeoDataFrame from path above.
                uses_gdf = gpd.read_file(uses_p_path)
                # Filter rows with "VU" values.
                vpsvpoas_vu = vpsvpoas_gdf[vpsvpoas_gdf[id_attr[0]].str.startswith("VU")]
                vpsvpoas_vu = vpsvpoas_vu.reset_index(drop=True)
                column_export = []
                geom_out = []
                for i in range(vpsvpoas_vu.geometry.count()):  
                    if not vpsvpoas_vu.geometry[i].within(uses_gdf.geometry).any():
                        column_export.append(vpsvpoas_vu[id_attr[0]][i])
                        geom_out.append(vpsvpoas_vu.geometry[i].difference(uses_gdf.geometry))
                    else:
                        pass
                
                # If all VU features are within USES_p.
                if len(geom_out) == 0:
                    print(
                        "Ok: There are no VU geometries outside USES_p.",
                        end="\n" * 2
                    )
                # If there are some geometries outside, do:
                elif len(geom_out) > 0 and export is True:
                    errors += 1
                    # Prepare id_out for importing as a column
                    id_out_col = {"vu_outside": column_export}
                    # Converts these geometries into Geoseries.
                    geom_out_col = gpd.GeoSeries(data=geom_out, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_outside = gpd.GeoDataFrame(data=id_out_col, geometry=geom_out_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_outside.to_file(
                        f"{dest_dir_path}/vpsvpoas_p_vu_outside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    if verbose is True:
                        print(
                            f"Error: There are VU geometries outside USES_p ({len(geom_out)}) near features:",
                            *column_export,
                            "- These geometries were saved as vpsvpoas_p_vu_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        )

                    else:
                        # Print number of geometries that are not within ReseneUzemi_p.
                        print(
                            f"Error: There are VU geometries outside USES_p ({len(geom_out)}).",
                            "- These geometries were saved as vpsvpoas_p_vu_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        )

                # If export_outside = False, print number of features outside only.
                elif len(geom_out) > 0 and export is False:
                    errors += 1 
                    if verbose is True:
                        print(
                            f"Error: There are VU geometries outside USES_p ({len(geom_out)}) near feature:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2
                        )
                    else:
                        print(
                            f"Error: There are VU geometries outside USES_p ({len(geom_out)}).",
                            end="\n" * 2
                        )

            elif (
                validity_shp_zip(zip_dir, mun_code, "VpsVpoAs_p") > 0 or validity_shp_zip(zip_dir, mun_code, "USES_p") > 0 
            ):
                print(
                    "Error: Checking VU geometries within USES_p cannot be run due to invalid geometries.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "VpsVpoAs_p") == 0 and validity_shp_zip(zip_dir, mun_code, "USES_p") == 0 
                and id_attr == 0 
            ):
                print(
                    "Error: Checking VU geometries within USES_p cannot be run due to missing mandatory id attribute.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "VpsVpoAs_p") == 0 and validity_shp_zip(zip_dir, mun_code, "USES_p") == 0 
                and id_attr == 1 and not vpsvpoas_gdf[id_attr[0]].str.startswith("VU").any() 
            ):
                print(
                    "Error: Checking VU geometries within USES_p cannot be run due to missing VU values.",
                    end="\n" * 2
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
    verbose: bool = False,
    export: bool = False,
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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
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
        # Path to PlochyZmen_p shapefile.
        pz_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
        # Create GeoDataFrame from path above.
        pz_gdf = gpd.read_file(pz_path)
        # Check if pz_gdf GeoDataFrame contains id mandatory attribute, If so, this mandatory attribute
        # is appended into an empty list.
        id_attr = [attr for attr in pz_gdf.columns.tolist() if attr.lower == "id"]

        if shp == "PlochyZmen_p" and "ZastaveneUzemi_p" in shps_to_check:
            if (
                validity_shp_zip(zip_dir, mun_code, shp) == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0
                and id_attr == 1 and pz_gdf[id_attr[0]].str.startswith("K").any()
            ):

                # Path to ZastaveneUzemi_p shapefile.
                zu_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
                # Create GeoDataFrames from paths above.
                zu_gdf = gpd.read_file(zu_path)
                # Filter rows with "P" values.
                # For each row (index number) in all geometries (count) find out, which are not fully within ZastaveneUzemi_p.
                pz_p = pz_gdf[pz_gdf[id_attr[0]].str.startswith("P")]
                pz_p = pz_p.reset_index(drop=True)
                column_export = []
                geom_out = []
                for i in range(pz_p.geometry.count()):  
                    # If geometry is not within ZastaveneUzemi_p.
                    if not pz_p.geometry[i].within(zu_gdf.geometry).any():
                        column_export.append(pz_p[id_attr[0]][i])
                        # Append geometry parts that lay outside ZastaveneUzemi_p into geom_out list.
                        geom_out.append(pz_p.geometry[i].difference(zu_gdf.geometry))
                    # If this geometry is within ZastaveneUzemi_p, pass.
                    else:
                        pass

                # If all P features are within ZastaveneUzemi_p.
                if len(geom_out) == 0:
                    print(
                        "Ok: There are no P geometries outside ZastaveneUzemi_p.",
                        end="\n" * 2
                    )
                # If there are some geometries outside, do:
                elif len(geom_out) > 0  and export is True:
                    errors += 1
                    # Prepare id_out for importing as a column
                    p_out_col = {"p_outside": column_export}
                    # Converts these geometries into Geoseries.
                    geom_out_col = gpd.GeoSeries(data=geom_out, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_outside = gpd.GeoDataFrame(data=p_out_col, geometry=geom_out_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_outside.to_file(
                        f"{dest_dir_path}/plochyzmen_p_p_outside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    if verbose is True:
                    # Print number of geometries that are not within ZastaveneUzemi_p.
                        print(
                            f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)} near features:",
                            *column_export,
                            "- These geometries were saved as plochyzmen_p_p_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        )

                    else:
                        print(
                            f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)}).",
                            "- These parts were saved as plochyzmen_p_p_outside.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )

                # If export_outside = False, print number of features outside only.
                elif len(geom_out) > 0 and export is False:
                    errors += 1
                    if verbose is True:
                        print(
                            f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)} near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2
                        )
                    else:
                        print(
                            f"Error: There are P geometries outside ZastaveneUzemi_p ({len(geom_out)}).",
                            end="\n" * 2,
                        )

            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") > 0 or validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") > 0 
            ):
                print(
                    "Error: Checking P geometries within ZastaveneUzemi_p cannot be run due to invalid geometries.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0 
                and id_attr == 0 
            ):
                print(
                    "Error: Checking P geometries within ZastaveneUzemi_p cannot be run due to missing mandatory id attribute.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0 
                and id_attr == 1 and not pz_gdf[id_attr[0]].str.startswith("P").any() 
            ):
                print(
                    "Error: Checking P geometries within ZastaveneUzemi_p cannot be run due to missing P values.",
                    end="\n" * 2
                )

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
    verbose: bool = False,
    export: bool = False,
) -> int:
    """Checking K features from PlochyRZV_p outside ZastaveneUzemi_p.

    Check, if K features from VpsVpoAs_p shapefile are outside
    ZastaveneUzemi_p shapefile. If K features are missing or are empty,
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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
       A boolean value for exporting geometries of certain
       shapefile that are within ZastaveneUzemi_p. Default value 
       is set up as False (for not exporting these geometries within 
       ZastaveneUzemi_p). For exporting these geometries, put True.
    
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
        # Path to PlochyZmen_p shapefile.
        pz_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
        # Create GeoDataFrame from path above.
        pz_gdf = gpd.read_file(pz_path)
        # Check if pz_gdf GeoDataFrame contains id mandatory attribute, If so, this mandatory attribute
        # is appended into an empty list.
        id_attr = [attr for attr in pz_gdf.columns.tolist() if attr.lower == "id"]
        if shp == "PlochyZmen_p" and "ZastaveneUzemi_p" in shps_to_check:
            if (
                validity_shp_zip(zip_dir, mun_code, shp) == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0
                and id_attr == 1 and pz_gdf[id_attr[0]].str.startswith("K").any()
            ):
                # Path to ZastaveneUzemi_p shapefile.
                zu_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/ZastaveneUzemi_p.shp"
                # Path to PlochyZmen_p shapefile.
                pz_path = f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/PlochyZmen_p.shp"
                # Create GeoDataFrames from paths above.
                zu_gdf = gpd.read_file(zu_path)
                pz_gdf = gpd.read_file(pz_path)
                # Filter rows with K values.
                # For each row (index number) in all geometries (count) find out, which are not fully outside ZastaveneUzemi_p.
                pz_k = pz_gdf[pz_gdf[id_attr[0]].str.startswith("K")]
                pz_k = pz_k.reset_index(drop=True)
                column_export = []
                geom_in = []
                for i in range(pz_k.geometry.count()):  
                    # If geometry is not fully outside ZastaveneUzemi_p.
                    if pz_k.geometry[i].within(zu_gdf.geometry).any():
                        column_export.append(pz_k[id_attr[0]][i])
                        # Append geometry parts that lay inside ZastaveneUzemi_p into geom_in list.
                        geom_in.append(pz_k.geometry[i].difference(zu_gdf.geometry))
                    # If this geometry is within ZastaveneUzemi_p, pass.
                    else:
                        pass
                
                # If all K features are outside the ZastaveneUzemi_p.
                if len(geom_in) == 0:
                    print(
                        "Ok: There are no K geometries outside ZastaveneUzemi_p.",
                        end="\n" * 2,
                    )
                # If there are some geometries inside, do:
                elif len(geom_in) > 0 and export is True:
                    errors += 1
                    # Prepare id_out for importing as a column
                    k_in_col = {"k_inside": column_export}
                    # Converts these geometries into Geoseries.
                    geom_in_col = gpd.GeoSeries(data=geom_in, crs="EPSG:5514")
                    # Then create GeoDataFrame (from info list and Geoseries).
                    gdf_inside = gpd.GeoDataFrame(data=k_in_col, geometry=geom_in_col, crs="EPSG:5514")
                    # Export this GeoDataFrame as shapefile.
                    gdf_inside.to_file(
                        f"{dest_dir_path}/plochyzmen_k_p_inside.shp",
                        driver="ESRI Shapefile",
                        crs="EPSG:5514",
                    )
                    # Print number of geometries that are within ZastaveneUzemi_p.
                    if verbose is True:
                        print(
                            f"Error: There are K geometries inside ZastaveneUzemi_p ({len(geom_in)} near features:",
                            *column_export,
                            "- These geometries were saved as plochyzmen_p_p_outside.shp.",
                            sep="\n",
                            end="\n" * 2
                        )
                    else:
                        print(
                            f"Error: There are K geometries inside ZastaveneUzemi_p ({len(geom_in)}).",
                            "- These parts were saved as plochyzmen_p_p_outside.shp.",
                            sep="\n",
                            end="\n" * 2,
                        )

                # If export_inside = False, print number of features inside only.
                elif len(geom_in) > 0 and export is False:
                    errors += 1
                    if verbose is True:
                        print(
                            f"Error: There are K geometries inside ZastaveneUzemi_p ({len(geom_in)}) near features:",
                            *column_export,
                            sep="\n",
                            end="\n" * 2,
                        )
                    else:
                        print(
                            f"Error: There are K geometries inside ZastaveneUzemi_p ({len(geom_in)}).",
                            end="\n" * 2,
                        )
            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") > 0 or validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") > 0 
            ):
                print(
                    "Error: Checking K geometries outside ZastaveneUzemi_p cannot be run due to invalid geometries.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0 
                and id_attr == 0 
            ):
                print(
                    "Error: Checking K geometries outside ZastaveneUzemi_p cannot be run due to missing mandatory id attribute.",
                    end="\n" * 2
                )

            elif (
                validity_shp_zip(zip_dir, mun_code, "PlochyZmen_p") == 0 and validity_shp_zip(zip_dir, mun_code, "ZastaveneUzemi_p") == 0 
                and id_attr == 1 and not pz_gdf[id_attr[0]].str.startswith("K").any() 
            ):
                print(
                    "Error: Checking K geometries outside ZastaveneUzemi_p cannot be run due to missing K values.",
                    end="\n" * 2
                )

        else:
            pass

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return errors
