import zipfile
from time import time
from datetime import date

import geopandas as gpd

from src.models.attributes import attributes
from src.models.values import values


def allowed_values(zip_dir: str, mun_code: int) -> None:
    start_time = time()
    # Create list of zip contents.
    zip_contents = zipfile.ZipFile(f"{zip_dir}/DUP_{mun_code}.zip").namelist()
    # Create set of shapefiles name only.
    shps_to_check = set(
        shp.removeprefix(f"DUP_{mun_code}/Data/").removesuffix(".shp")
        for shp in zip_contents
        if shp.endswith(".shp")
    )
    # For each shapefile:
    for shp in shps_to_check:
        print(shp)
        print("-" * 50)
        # Create GeoDataFrame.
        shp_gdf = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Create list of attribute names.
        attrs_to_check = shp_gdf.columns.tolist()
        # Create list of attribute names that are specified in attributes
        # dictionary (attributes.py module).
        included = [
            attr for attr in attrs_to_check if attr.lower() in attributes[shp.lower()]
        ]
        missing = set(attributes[shp.lower()]).difference(set(included))

        for attr in included:
            if (
                shp.lower()
                in [
                    "reseneuzemi_p",
                    "zastaveneuzemi_p",
                    "systemsidelnizelene_p",
                    "systemverprostr_p",
                ]
                and attr not in missing
            ):
                for row in range(shp_gdf[attr].count()):
                    if shp_gdf[attr][row] == mun_code:
                        pass
                    else:
                        print(f"{shp_gdf[attr][row]} is not correct.")
            elif shp.lower() == "uzemniprvkyrp_p" and attr not in missing:
                for row in range(shp_gdf[attr].count()):
                    if shp_gdf[attr][row] in values["uzemniprvkyrp_p"]["id"]:
                        pass
                    else:
                        print(
                            f"{shp_gdf[attr][row]} value does not respect convention."
                        )
            elif shp.lower() == "plochyrzv_p" and attr not in missing:
                if attr == "cash":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["obecne"]["cash"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["obecne"]["typ"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "index":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] is not None and shp_gdf["Typ"] == "AP":
                            if shp_gdf[attr][row] in ["p", "t"]:
                                pass
                            else:
                                print(
                                    f"{shp_gdf[attr][row]} value does not respect convention."
                                )
                        elif shp_gdf[attr][row] is not None and shp_gdf["Typ"] == "LU":
                            if shp_gdf[attr][row] in ["h", "o", "z"]:
                                pass
                            else:
                                print(
                                    f"{shp_gdf[attr][row]} value does not respect convention."
                                )
            elif shp.lower() == "uzemnirezervy_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["uzemnirezervy_p"]["id"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["obecne"]["typ"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
            elif shp.lower() == "koridoryp_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["koridoryp_p"]["id"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
            elif shp.lower() == "koridoryn_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["koridoryn_p"]["id"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
            elif shp.lower() == "plochyzmen_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["plochyzmen_p"]["id"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "etapizace":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["plochyzmen_p"]["etapizace"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
            elif shp.lower() == "plochypodm_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["plochypodm_p"]["id"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "datum":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] == date.today().strftime("%Y-%m-%d"):
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
            elif shp.lower().startswith("vpsvpoas_") and attr not in missing:
                for row in range(shp_gdf[attr].count()):
                    if shp_gdf[attr][row][:3] in values["vpsvpoas"]["id"]:
                        pass
                    else:
                        print(
                            f"{shp_gdf[attr][row]} value does not respect convention."
                        )
            elif shp.lower() == "uses_p" and attr not in missing:
                if attr == "cash":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["obecne"]["cash"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["uses_p"]["typ"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
                elif attr == "oznaceni":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] in values["uses_p"]["oznaceni"]:
                            pass
                        else:
                            print(
                                f"{shp_gdf[attr][row]} value does not respect convention."
                            )
