from turfpy import boolean, meta

feature_a = {
    "type": "Feature",
    "properties": {},
    "geometry": {"type": "MultiPoint", "coordinates": [[0, 0], [12, 12]]},
}

feature_b = {
    "type": "Feature",
    "properties": {},
    "geometry": {"type": "MultiPoint", "coordinates": [[1, 1], [12, 12]]},
}


print(boolean.boolean_intersects(feature_a, feature_b))
