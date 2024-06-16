import re
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
)
from PyQt5.QtCore import QVariant


def error_points(layer_name):
    """
    Function to create a temporary point layer from the 'not_valid_' field
    of a given shapefile layer and add it to the QGIS project.

    Parameters:
    layer_name (str): Name of the layer in the QGIS project.
    """
    # Load the shapefile layer
    layers = QgsProject.instance().mapLayersByName(layer_name)
    if not layers:
        raise Exception(f"Layer '{layer_name}' not found in the project")

    layer = layers[0]

    # Create a temporary memory layer for the points with EPSG:5514 CRS
    point_layer = QgsVectorLayer("Point?crs=EPSG:5514", "temp_points", "memory")
    provider = point_layer.dataProvider()
    provider.addAttributes([QgsField("id", QVariant.Int)])
    point_layer.updateFields()

    # Regex pattern to extract coordinates
    pattern = re.compile(r"Self-intersection\[\s*(-?\d+\.\d+)\s*(-?\d+\.\d+)\s*\]")

    # Iterate over the features and extract coordinates
    features = layer.getFeatures()
    for feature in features:
        not_valid = feature["not_valid_"]
        match = pattern.search(not_valid)
        if match:
            x, y = map(float, match.groups())
            point = QgsPointXY(x, y)
            geom = QgsGeometry.fromPointXY(point)
            point_feature = QgsFeature(point_layer.fields())
            point_feature.setGeometry(geom)
            point_feature["id"] = feature.id()
            provider.addFeature(point_feature)

    # Add the temporary point layer to the project
    QgsProject.instance().addMapLayer(point_layer)


# Example usage:
error_points("plochyrzv_p_not_valid")
