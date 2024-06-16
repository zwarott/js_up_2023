import os

from osgeo import ogr, osr, gdal

# Enable GDAL exceptions
gdal.UseExceptions()


def list_gpkg_layers(gpkg_path):
    """
    List all layers in a GeoPackage file using GDAL.

    Parameters:
    gpkg_path (str): Path to the GeoPackage file.

    Returns:
    list: List of layer names in the GeoPackage.
    """
    gpkg = gdal.OpenEx(gpkg_path)
    if not gpkg:
        raise RuntimeError(f"Failed to open GeoPackage: {gpkg_path}")

    return [gpkg.GetLayerByIndex(i).GetName() for i in range(gpkg.GetLayerCount())]


def export_shp_from_gpkg(gpkg_path, output_dir):
    """
    Export each layer in a GeoPackage file to individual Shapefiles with CRS set to EPSG:5514.

    Parameters:
    gpkg_path (str): Path to the GeoPackage file.
    output_dir (str): Directory to save the Shapefiles.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Open the GeoPackage
    gpkg = ogr.Open(gpkg_path)
    if not gpkg:
        raise Exception(f"Unable to open GeoPackage: {gpkg_path}")

    # Get the number of layers in the GeoPackage
    layer_count = gpkg.GetLayerCount()

    # Define the target spatial reference for EPSG:5514
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(5514)

    for i in range(layer_count):
        layer = gpkg.GetLayerByIndex(i)
        layer_name = layer.GetName()

        if layer_name == "layer_styles":
            continue  # Skip the "layer_styles" layer

        # Create the output shapefile path
        shp_path = os.path.join(output_dir, f"{layer_name}.shp")

        # Create the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(shp_path):
            driver.DeleteDataSource(shp_path)

        # Create the shapefile data source
        shp_ds = driver.CreateDataSource(shp_path)
        # Create the shapefile layer with UTF-8 encoding
        shp_layer = shp_ds.CreateLayer(
            layer_name,
            srs=target_srs,
            geom_type=layer.GetGeomType(),
            options=["ENCODING=UTF-8"],
        )

        # Add fields to the shapefile layer
        layer_defn = layer.GetLayerDefn()
        for j in range(layer_defn.GetFieldCount()):
            field_defn = layer_defn.GetFieldDefn(j)
            shp_layer.CreateField(field_defn)

        # Copy features from the GeoPackage layer to the shapefile layer
        for feature in layer:
            shp_layer.CreateFeature(feature)

        # Close the shapefile data source
        shp_ds = None
        print(
            f"Exported {layer_name} to {shp_path} with CRS EPSG:5514 and UTF-8 encoding"
        )


# Example usage
gpkg_path = "/Users/zwarott/Documents/Python/Projects/js_up_2023/src/models/data/531090/zmena_c1_up_brezova/UP_v20_brezova.gpkg"
output_dir = "/Users/zwarott/Documents/Python/Projects/js_up_2023/src/models/data/531090/zmena_c1_up_brezova/output"

export_shp_from_gpkg(gpkg_path, output_dir)
# print(list_gpkg_layers(gpkg_path))
