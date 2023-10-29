from datetime import datetime

import geopandas as gpd

from src.models.output_tables import js_tables 
from src.controllers.check_relationships import (
    shp_info_standardized,
    shp_info_non_standardized,
    shps_in_zip,
    shp_within_mun,
    check_gaps,
    check_overlaps,
    vu_within_uses,
    p_within_zu,
    k_outside_zu,
    covered_mun_both,
    covered_mun_przv,
    check_gaps_covered,
    overlaps_covered_mun,
)

from src.controllers.check_attributes import mandatory_attrs_exist, mandatory_attrs_type
from src.controllers.check_records import allowed_values
from src.controllers.check_geometry import check_validity_shp_zip
from src.controllers.decorators import timer


# Implement timer decorator for checking duration of this checking process.
@timer
def check_layers(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
):
    """Run checking process including several subprocesses.

    Check geometry, spatial relationships and existence of certain
    attributes and records within each shapefile stored in zip file.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    dest_dir_path : str
        A path to directory, where will be differences saved.
    mun_code : int
        A unique code of particular municipality, for which
        are these data tested.
    export : bool
        A boolean value for exporting all features that do not
        respect conventions defined within each function. Default
        values is set up as False. For exporting these features, 
        put True.
    """
    # Print info about standardized layers.
    shp_info_standardized(zip_dir, mun_code)
    indent_30 = "-" * 30
    indent_20 = "-" * 20
    spaces = " "
    print(spaces)
    # Start checking proess.
    print(indent_30, " CHECKING PROCESS ", indent_30)
    print(spaces, spaces, sep="\n")
    #Create list of all shapefiles included in zipped file.
    shps_from_zip = shps_in_zip(zip_dir, mun_code)
    # Create list of standardized shapefiles that are not empty.
    shps_to_check = [
        shp
        for shp in js_tables
        if shp in shps_from_zip
        and gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        ).empty
        is False
    ]
    # Default status.
    # Status == 0 -> there are no errors.
    # Status > 0 -> some errors occurr.
    status = 0
    # Boolean value if errors will be exported.
    exp = export

    # For each standardized shapefile check if geometries are valid and other
    # spatial relationships.
    # If any error occurs int will be appended to errors variable.
    for shp in shps_to_check:
        errors = 0
        print(indent_20, f" CHECKING – {shp} layer", indent_20)
        e = check_validity_shp_zip(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = shp_within_mun(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = check_gaps(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = check_overlaps(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = vu_within_uses(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = p_within_zu(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = k_outside_zu(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e
        e = mandatory_attrs_exist(zip_dir, mun_code, shp)
        errors += e
        e = mandatory_attrs_type(zip_dir, mun_code, shp)
        errors += e
        e = allowed_values(zip_dir, dest_dir_path, mun_code, shp, exp)
        errors += e

        if errors == 0: 
            print("Status: Ok")
        else:
            status += 1
            print("Status: Error")
        print(spaces)
    
    # Check relationships between layers such as ReseneUzemi_p, PlochyRZV_p
    # and KoridoryP_p.
    print(indent_20, "CHECKING RELATIONSHIPS BETWEEN LAYERS", indent_20)
    print(spaces)
    # Check if any errors and warnings occurr.
    errors = 0
    warnings = 0
    if "PlochyRZV_p" and "KoridoryP_p" in shps_to_check:
        e = covered_mun_both(zip_dir, dest_dir_path, mun_code, exp)
        errors += e
        e, w = check_gaps_covered(zip_dir, dest_dir_path, mun_code, exp)
        errors += e
        warnings += w
        e, w = overlaps_covered_mun(zip_dir, dest_dir_path, mun_code, exp)
        errors += e
        warnings += w
    elif "PlochyRZV_p" in shps_to_check and "KoridoryP_p" not in shps_to_check:
        e = covered_mun_przv(zip_dir, dest_dir_path, mun_code, exp)
        errors += e
        print(
            "Warning: KoridoryP_p layer is missing, gaps in PlochyRZV_p were already checked."
        )
        print(spaces)
        print(
            "Warning: KoridoryP_p layer is missing, overlaps in PlochyRZV_p were already checked."
        )
    print(spaces)
    if errors == 0 and warnings == 0:
        print("Status: Ok")
    elif errors == 0 and warnings > 0:
        print("Status: Warning")
    else:
        status += 1
        print("Status: Error")
    
    # Print info about non-standardized layers.
    shp_info_non_standardized(zip_dir, mun_code)
    # Create list of non-standardized layers that respect naming convention.
    shps_to_check = [
        shp for shp in shps_to_check if shp not in js_tables and shp.startswith("X")
    ]
    # If there are any non-standardized layers, run checking process.
    if len(shps_to_check) > 0:
        for shp in shps_to_check:
            exp = export
            errors = 0
            e = check_validity_shp_zip(zip_dir, dest_dir_path, mun_code, shp, exp)
            errors += e
            e = shp_within_mun(zip_dir, dest_dir_path, mun_code, shp, exp)
            errors += e
            e = check_gaps(zip_dir, dest_dir_path, mun_code, shp, exp)
            errors += e
            e = check_overlaps(zip_dir, dest_dir_path, mun_code, shp, exp)
            errors += e

            if errors == 0: 
                print("Status: Ok")
            else:
                status += 1
                print("Status: Error")
            print(spaces)
    else:
        print("There are not any non-standardized layers.")

    print(spaces)
    print(indent_30, " CHECKING WAS FINISHED ", indent_30)
    print(spaces)

    # Print info about checking status -> if input data are ok or some errors occurr.
    if status == 0:
        print("Status: Ok")
    else:
        print("Status: Error")
    time_info = datetime.today().isoformat(sep=" ", timespec="seconds")
    print(
        spaces,
        f"Importing spatial plan of municipality with code {mun_code} was finished at {time_info}.",
        spaces,
        sep="\n",
    )
