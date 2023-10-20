import geopandas as gpd

from src.models.attributes import attributes, attribute_types


def mandatory_attrs_exist(zip_dir: str, mun_code: int, shp: str):
    """Check existence of mandatory attributes.

    Check, if all mandatory attributes within
    each shapefile exist.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    spaces = " " * 150
    try:
        shp_gdf = gpd.read_file(
            f"zip://{zip_dir}/DUP_{mun_code}.zip!DUP_{mun_code}/Data/{shp}.shp"
        )
        # Create list of attribute names.
        attrs_to_check = shp_gdf.columns.tolist()
        # Create list of attribute names that are specified in attributes
        # dictionary (attributes.py module).
        included = [
            attr.lower()
            for attr in attrs_to_check
            if attr.lower() in attributes[shp.lower()]
        ]
        # Crete set of attributes that are missing.
        # Set was created using difference method (mandatory - included).
        missing = set(attributes[shp.lower()]).difference(set(included))
        # If all mandatory attributes are include.
        if len(missing) == 0:
            print(f"OK: All mandatory attributes in {shp} are included.")
        # If any mandatory attribute is missing.
        elif len(missing) > 0:
            for attr in missing:
                print(f"Error: {attr} attribute in {shp} is missing.")

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    print(spaces)

    return len(missing)


def mandatory_attrs_type(zip_dir: str, mun_code: int, shp: str):
    """Check for correct attribute types.

    Check, if all mandatory attributes within
    each shapefile has correct data type.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where are zipped files stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these spatial data tested.
    """
    spaces = " " * 150
    try:
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
        wrong_attr = []
        wrong_types = []
        # For each included attribute:
        for attr in included:
            # If type of included attribute is equal to mandatory attribute type.
            if shp_gdf[attr].dtype == attribute_types[shp.lower()][attr.lower()]:
                pass
            # If not.
            else:
                wrong_attr.append(shp_gdf[attr].name)
                wrong_types.append(shp_gdf[attr].dtype)
        if len(wrong_types) == 0:
            print("Ok: All attributes have correct type.")
        else:
            for i in wrong_attr:
                print(f"Error: {i} attribute in {shp} has not correct type.")

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    print(spaces)

    return len(wrong_types)
