import geopandas as gpd

from src.models.attributes import attributes, attribute_types


def mandatory_attrs_exist(zip_dir: str, mun_code: int, shp: str) -> int:
    """Checking existence of mandatory attributes.

    Check, if all mandatory attributes are within
    certain shapefile.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these data tested.
    shp : str
        A shapefile name, for which existence of mandatory
        attributes is tested.

    Returns
    -------
    int
        A number of missing mandatory attributes.
    """
    try:
        # Geodataframe from input shapefile.
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
            print(f"OK: All mandatory attributes are included.",
                  end="\n" * 2)
        # If any mandatory attribute is missing.
        elif len(missing) > 0:
            for attr in missing:
                print(f"Error: {attr} attribute in is missing.",
                      end="\n" * 2)
    # If any error occurs, print info about it.
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
    
    # Return number of missing attributes.
    return len(missing)


def mandatory_attrs_type(zip_dir: str, mun_code: int, shp: str) -> int:
    """Checking correct attribute types.

    Check, if all mandatory attributes within certain shapefile 
    have correct data type. Returns number of attributes that
    have wrong data type.

    Parameters
    ----------
    zip_dir : str
        A path to directory, where zip file is stored.
    mun_code : int
        A unique code of particular municipality, for which
        are these data tested.
    shp : str
        A shapefile name, for which types of mandatory 
        attributes are tested.

    Returns
    -------
    int
        Number of mandatory attributes with wrong types.
    """
    # Geodataframe from input shapefile.
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
        # List of attribute names that have wrong types.
        wrong_attr = []
        # List of wrong attribute types.
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
            print("Ok: All attributes have correct type.",
                  end="\n" * 2)
        else:
            for attr in wrong_attr:
                print(f"Error: {attr} attribute has not correct type.",
                      end="\n" * 2)

    # If any error occurs, print info about it.
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return len(wrong_types)
