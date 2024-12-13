from turfpy.measurement import area
from geojson import Feature, FeatureCollection

geometry_1 = {"coordinates": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]], "type": "Polygon"};
geometry_2 = {"coordinates": [[[2.38, 57.322], [23.194, -20.28], [-120.43, 19.15], [2.38, 57.322]]], "type": "Polygon"};
feature_1 = Feature(geometry=geometry_1)
feature_2 = Feature(geometry=geometry_2)
feature_collection = FeatureCollection([feature_1, feature_2])

print(area(feature_collection))