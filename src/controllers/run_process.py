from datetime import datetime

import geopandas as gpd

from src.models.output_tables import js_tables 
from src.controllers.general_relations import (
    unknown_shp,
    shp_info_standardized,
    shp_info_non_standardized,
    shps_in_zip,
)
from src.controllers.solo_relations import (
    shp_within_mun,
    check_gaps,
    check_overlaps,

)
from src.controllers.cover_relations import (
    covered_mun_both,
    covered_mun_przv,
    check_gaps_covered,
    overlaps_covered_mun,
)
from src.controllers.uniq_relations import (
    vu_within_uses,
    p_within_zu,
    k_outside_zu,
)

from src.controllers.attribute_rules import mandatory_attrs_exist, mandatory_attrs_type
from src.controllers.value_rules import allowed_values
from src.controllers.geom_validation import check_validity_shp_zip


def check_layers(
    zip_dir: str, dest_dir_path: str, mun_code: int, verbose: bool = False, export: bool = False,
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
    verbose : bool
        A boolean value for printing errors in more detail (near which
        features errors occur). False (for not printing statements in
        verbose mode). To do so, put True.
    export : bool
        A boolean value for exportorting all features that do not
        respect conventions defined within each function. Default
        values is set up as False. For exportorting these features, 
        put True.
    """
    # Print info about standardized layers.
    shp_info_standardized(zip_dir, mun_code)
    # Start checking proess.
    print("\n", " CHECKING PROCESS ".center(60, "-"), sep="\n", end="\n" * 3)
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
    # Status > 0 -> some errors occur.
    status = 0

    # For each standardized shapefile check if geometries are valid and other
    # spatial relationships.
    # If any error occurs int will be appended to errors variable.
    for shp in shps_to_check:
        errors = 0
        print(f" CHECKING – {shp} layer ".center(60, "-"), end="\n" * 2)
        e = check_validity_shp_zip(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        e = mandatory_attrs_exist(zip_dir, mun_code, shp, verbose)
        errors += e
        e = mandatory_attrs_type(zip_dir, mun_code, shp, verbose)
        errors += e
        e = allowed_values(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        e = shp_within_mun(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        e = check_gaps(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        # Geometries within VpsVpoAs_p and UzemniRezervy can overlap each other.
        if shp not in ["VpsVpoAs_p", "UzemniRezervy"]:
            e = check_overlaps(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
            errors += e
        else:
            pass
        e = vu_within_uses(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        e = p_within_zu(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        e = k_outside_zu(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
        errors += e
        

        if errors == 0: 
            print("Status: Ok", end="\n" * 3)
        else:
            status += 1
            print("Status: Error", end="\n" * 3)
    
    # Check relationships between layers such as ReseneUzemi_p, PlochyRZV_p
    # and KoridoryP_p.
    print(" CHECKING RELATIONSHIPS BETWEEN LAYERS ".center(60, "-"), end="\n" * 2)
    # Check if any errors and warnings occur.
    errors = 0
    warnings = 0
    if "PlochyRZV_p" and "KoridoryP_p" in shps_to_check:
        e = covered_mun_both(zip_dir, dest_dir_path, mun_code, verbose, export)
        errors += e
        e = check_gaps_covered(zip_dir, dest_dir_path, mun_code, verbose, export)
        errors += e
        e = overlaps_covered_mun(zip_dir, dest_dir_path, mun_code, verbose, export)
        errors += e
    elif "PlochyRZV_p" in shps_to_check and "KoridoryP_p" not in shps_to_check:
        e = covered_mun_przv(zip_dir, dest_dir_path, mun_code, verbose, export)
        errors += e
    else:
        print(
            "Checking relationships between layers cannot be check due to missing PlochyRZV_p.",
            end="\n" * 2
        )

    if errors == 0:
        print("Status: Ok", end="\n" * 3)
    elif errors == 0 and warnings > 0:
        print("Status: Warning", end="\n" * 3)
    else:
        status += 1
        print("Status: Error", end="\n" * 3)
    
    # Print info about non-standardized layers.
    shp_info_non_standardized(zip_dir, mun_code)
    # Create list of non-standardized layers that respect naming convention.
    shps_to_check = [
        shp for shp in shps_from_zip if shp not in js_tables and shp.startswith("X")
        and gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        ).empty
        is False
    ]
    # Create list with shapefiles, that do not respect convention.
    wrong_shp = unknown_shp(zip_dir, mun_code)
    # If there are any non-standardized layers, run checking process.
    errors = 0
    if len(shps_to_check) > 0:
        for shp in shps_to_check:
            e = check_validity_shp_zip(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
            errors += e
            e = shp_within_mun(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
            errors += e
            e = check_gaps(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
            errors += e
            e = check_overlaps(zip_dir, dest_dir_path, mun_code, shp, verbose, export)
            errors += e

            
    else:
        print("There are not any non-standardized layers.", end="\n" * 2)

    if len(wrong_shp) > 0:
        print(
            f"Error: There are unknown shapefiles ({len(wrong_shp)}):",
              *wrong_shp,
              sep="\n",
              end="\n" * 3
        )

    if errors == 0: 
        print("Status: Ok", end="\n" * 3)
    else:
        status += 1
        print("Status: Error", end="\n" * 3)

    print(" CHECKING WAS FINISHED ".center(60, "-"), end="\n" * 2)

    # Print info about checking status -> if input data are ok or some errors occur.
    if status == 0:
        print("Status: Ok", end="\n" * 2)
    else:
        print("Status: Error", end="\n" * 2)
    time_info = datetime.today().isoformat(sep=" ", timespec="seconds")
    print(
        f"Importing spatial plan of municipality with code {mun_code} was finished at {time_info}.",
        end="\n" * 2,
    )
