import zipfile
from datetime import date

import pandas as pd
import geopandas as gpd

from src.models.attributes import attributes
from src.models.values import values


def allowed_values(
    zip_dir: str,
    dest_dir_path: str,
    mun_code: int,
    shp: str,
    export_values: bool = False,
):
    """Check for permissible values within shapefile.

    Check for permissible values within each shapefile in zipped file.
    If file contains shapefiles that has unknown name, checking process
    will be for this shapefile skipped.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    dest_dir_path : str
        A path to directory, where will be wrong values saved.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    export_values : bool
        A boolean value for exporting features with wrong values.
        Default value is set up as False (for not exporting these
        wrong values). For exporting these values, put True.
    """
    spaces = " " * 150
    try:
        # Create GeoDataFrame.
        shp_gdf = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Replace "NaN" values by "None" values.
        shp_gdf = shp_gdf.where(pd.notnull(shp_gdf), None)
        # Create list of attribute names.
        attrs_to_check = shp_gdf.columns.tolist()
        # Create list of attribute names that are specified in attributes
        # dictionary (attributes.py module).
        included = [
            attr for attr in attrs_to_check if attr.lower() in attributes[shp.lower()]
        ]
        missing = set(attributes[shp.lower()]).difference(set(included))
        wrong_values_info = []
        wrong_values_geom = []
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
                    if (
                        shp_gdf[attr][row] == mun_code
                        and shp_gdf[attr][row] is not None
                    ):
                        pass
                    else:
                        wrong_values_info.append(shp_gdf[attr][row])
                        wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "uzemniprvkyrp_p" and attr not in missing:
                for row in range(shp_gdf[attr].count()):
                    if (
                        shp_gdf[attr][row] in values["uzemniprvkyrp_p"]["id"]
                        and shp_gdf[attr][row] is not None
                    ):
                        pass
                    else:
                        wrong_values_info.append(shp_gdf[attr][row])
                        wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "plochyrzv_p" and attr not in missing:
                if attr == "cash":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["obecne"]["cash"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["obecne"]["typ"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "index":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] is not None and shp_gdf["Typ"] == "AP":
                            if shp_gdf[attr][row] in ["p", "t"]:
                                pass
                            else:
                                wrong_values_info.append(shp_gdf[attr][row])
                                wrong_values_geom.append(shp_gdf.geometry[row])
                        elif shp_gdf[attr][row] is not None and shp_gdf["Typ"] == "LU":
                            if shp_gdf[attr][row] in ["h", "o", "z"]:
                                pass
                            else:
                                wrong_values_info.append(shp_gdf[attr][row])
                                wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "uzemnirezervy_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row][:2] in values["uzemnirezervy_p"]["id"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["obecne"]["typ"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "koridoryp_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row][:4] in values["koridoryp_p"]["id"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "koridoryn_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row][:4] in values["koridoryn_p"]["id"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "plochyzmen_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row][:2] in values["plochyzmen_p"]["id"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "etapizace":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["plochyzmen_p"]["etapizace"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "plochypodm_p" and attr not in missing:
                if attr == "id":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] is None:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                        elif shp_gdf[attr][row][:3] in values["plochypodm_p"]["id"]:
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "datum":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] == date.today().strftime("%Y-%m-%d")
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower().startswith("vpsvpoas") and attr not in missing:
                for row in range(shp_gdf[attr].count()):
                    if shp_gdf[attr][row] is None:
                        wrong_values_info.append(shp_gdf[attr][row])
                        wrong_values_geom.append(shp_gdf.geometry[row])
                    elif (
                        shp_gdf[attr][row][:3] in values["vpsvpoas"]["id"]
                        or shp_gdf[attr][row][:4] in values["vpsvpoas"]["id"]
                    ):
                        pass
                    else:
                        wrong_values_info.append(shp_gdf[attr][row])
                        wrong_values_geom.append(shp_gdf.geometry[row])
            elif shp.lower() == "uses_p" and attr not in missing:
                if attr == "cash":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["obecne"]["cash"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "typ":
                    for row in range(shp_gdf[attr].count()):
                        if (
                            shp_gdf[attr][row] in values["uses_p"]["typ"]
                            and shp_gdf[attr][row] is not None
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                elif attr == "oznaceni":
                    for row in range(shp_gdf[attr].count()):
                        if shp_gdf[attr][row] is None:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])
                        elif (
                            shp_gdf[attr][row][:4] in values["uses_p"]["oznaceni"]
                            or shp_gdf[attr][row][:5] in values["uses_p"]["oznaceni"]
                            or shp_gdf[attr][row][:7] in values["uses_p"]["oznaceni"]
                            or shp_gdf[attr][row][:8] in values["uses_p"]["oznaceni"]
                        ):
                            pass
                        else:
                            wrong_values_info.append(shp_gdf[attr][row])
                            wrong_values_geom.append(shp_gdf.geometry[row])

        if len(wrong_values_geom) > 0 and export_values is False:
            print(
                f"Error: There are {len(wrong_values_geom)} feature(s) in {shp}.shp that do(es) not respect(s) convention.",
            )
        elif len(wrong_values_geom) > 0 and export_values is True:
            wrong_values_geom_col = gpd.GeoSeries(
                data=wrong_values_geom, crs="EPSG:5514"
            )
            gdf_wrong_values = gpd.GeoDataFrame(
                data=wrong_values_info,
                geometry=wrong_values_geom_col,
                crs="EPSG:5514",
            )
            gdf_wrong_values.rename(columns={0: "id"}, inplace=True)
            gdf_wrong_values.to_file(
                f"{dest_dir_path}/{shp.lower()}_wrong_values.shp",
                crs="EPSG:5514",
                driver="ESRI Shapefile",
            )
            print(
                f"Error: There are {len(wrong_values_info)} feature(s) in {shp} that do(es) not respect(s) convention.",
                f"       - These parts were saved as '{shp.lower()}_wrong_values.shp'.",
                sep="\n",
            )
        else:
            print(f"Ok: Feature(s) in {shp} respect(s) convention.")

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    print(spaces)

    return len(wrong_values_geom)
