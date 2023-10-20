from datetime import datetime

import geopandas as gpd

from src.models.output_tables import js_tables, mandatory_tables
from src.models.values import values

from src.controllers.check_relationships import (
    shp_info,
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


@timer
def check_standardized_layers(
    zip_dir: str, dest_dir_path: str, mun_code: int, export: bool = False
):
    shp_info(zip_dir, mun_code)
    indent_30 = "-" * 30
    indent_20 = "-" * 20
    spaces = " "
    print(indent_30, " CHECKING PROCESS ", indent_30)
    print(spaces, spaces, sep="\n")
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
    status = 0
    for shp in shps_to_check:
        errors = 0
        warnings = 0
        print(indent_20, f" CHECKING – {shp} layer", indent_20)
        e = check_validity_shp_zip(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = shp_within_mun(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = check_gaps(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = check_overlaps(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = vu_within_uses(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = p_within_zu(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = k_outside_zu(zip_dir, dest_dir_path, mun_code, shp)
        errors += e
        e = mandatory_attrs_exist(zip_dir, mun_code, shp)
        errors += e
        e = mandatory_attrs_type(zip_dir, mun_code, shp)
        errors += e
        e = allowed_values(zip_dir, dest_dir_path, mun_code, shp)
        errors += e

        if errors == 0 and warnings == 0:
            print("Status: Ok")
        elif errors == 0 and warnings > 0:
            print("Status: Warning")
        else:
            status += 1
            print("Status: Error")
        print(spaces)

    print(indent_20, "CHECKING RELATIONSHIPS BETWEEN LAYERS", indent_20)
    print(spaces)
    if "PlochyRZV_p" and "KoridoryP_p" in shps_to_check:
        covered_mun_both(zip_dir, dest_dir_path, mun_code)
        check_gaps_covered(zip_dir, dest_dir_path, mun_code)
        overlaps_covered_mun(zip_dir, dest_dir_path, mun_code)
    elif "PlochyRZV_p" in shps_to_check and "KoridoryP_p" not in shps_to_check:
        covered_mun_przv(zip_dir, dest_dir_path, mun_code)
        print(
            "Warning: KoridoryP_p layer is missing, gaps in PlochyRZV_p were already checked."
        )
        print(
            "Warning: KoridoryP_p layer is missing, overlaps in PlochyRZV_p were already checked."
        )
    print(spaces)
    print(indent_30, " CHECKING FINISHED ", indent_30)
    time_info = datetime.today().isoformat(sep=" ", timespec="seconds")
    print(
        spaces,
        f"Importing spatial plan of municipality with code {mun_code} was finished at {time_info}",
        spaces,
        sep="\n",
    )
    if status == 0:
        print("Status: Ok")
    else:
        print("Status: Error")


def check_non_standardized_layers():
    pass
