import os

import geopandas as gpd
import fiona


def export_gpkg_to_shp(gpkg_path, output_dir):
    """
    Export each layer in a GeoPackage file to individual Shapefiles.

    Parameters:
    gpkg_path (str): Path to the GeoPackage file.
    output_dir (str): Directory to save the Shapefiles.
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    layers = fiona.listlayers(gpkg_path)

    # Iterate over each layer in the GeoPackage
    for layer_name in layers:
        # Select each layer by its name
        gdf = gpd.read_file(gpkg_path, layer=layer_name)

        # Define the output Shapefile path
        shp_path = os.path.join(output_dir, f"{layer_name}.shp")

        # Export the GeoDataFrame to a Shapefile
        gdf.to_file(shp_path)
        print(f"Exported {layer_name} to {shp_path}")
