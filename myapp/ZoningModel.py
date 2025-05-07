import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPoint
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.spatial.distance import cdist
import json
import alphashape
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
import numpy as np


def compute_alpha_shape(points):
    """Compute the Alpha Shape (concave hull) of a set of points."""
    if len(points) < 3:
        return MultiPoint(points).convex_hull.buffer(0.0001)
    return MultiPoint(points).convex_hull

def hierarchical_clustering(points, n_clusters):
    """Perform Hierarchical Clustering using the 'average' linkage."""
    clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='average', metric='euclidean')
    labels = clustering.fit_predict(points)
    return labels

def optimize_hierarchical_clustering(points, min_clusters=1, max_clusters=15):
    """Find the best clustering using Silhouette Score with Hierarchical Clustering."""
    max_clusters = min(max_clusters, len(points) - 1)  
    if max_clusters < 2:
        return np.zeros(len(points), dtype=int) 

    best_k = min_clusters
    best_score = -1

    for k in range(min_clusters, max_clusters + 1):
        labels = hierarchical_clustering(points, k)
        if len(set(labels)) > 1:  # Ensure at least 2 clusters
            score = silhouette_score(points, labels)
            if score > best_score:
                best_score = score
                best_k = k

    return hierarchical_clustering(points, best_k)

def assign_lone_points(df, gdf):
    """Assign lone points to the nearest existing cluster in the same commune."""
    lone_points = df.groupby('Cluster').filter(lambda x: len(x) == 1)

    for idx, row in lone_points.iterrows():
        commune = row['commune_id']
        cluster_point = np.array([[row['latitude'], row['longitude']]])

        # Get clusters in the same commune
        commune_clusters = df[(df['commune_id'] == commune) & (df['Cluster'] != row['Cluster'])]

        if commune_clusters.empty:
            continue  # No other clusters to merge into

        # Find the nearest cluster
        cluster_centroids = commune_clusters.groupby('Cluster')[['latitude', 'longitude']].mean()
        nearest_cluster = cluster_centroids.index[np.argmin(cdist(cluster_point, cluster_centroids.values))]

        # Assign lone point to nearest cluster
        df.at[idx, 'Cluster'] = nearest_cluster

    return df

def cluster_communes(df,max=15):
    """Cluster each commune separately using Hierarchical Clustering and Silhouette optimization."""
    df = df.copy()
    cluster_boundaries = []

    for commune in df['commune_id'].unique():
        commune_df = df[df['commune_id'] == commune].copy()
        points = commune_df[['latitude', 'longitude']].values

        if len(points) < 3:
            df.loc[commune_df.index, 'Cluster'] = f"{commune}_0"
            cluster_boundaries.append((f"{commune}_0", MultiPoint(points).convex_hull.buffer(0.0001)))
            continue

        # Apply hierarchical clustering with silhouette optimization
        labels = optimize_hierarchical_clustering(points, 2, 15)

        # Assign clusters
        commune_df['Cluster'] = [f"{commune}_{l}" for l in labels]
        df.loc[commune_df.index, 'Cluster'] = commune_df['Cluster']

        # Compute boundaries
        for cluster_label in np.unique(labels):
            cluster_points = points[labels == cluster_label]
            polygon = compute_alpha_shape(cluster_points)
            cluster_boundaries.append((f"{commune}_{cluster_label}", polygon))

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(cluster_boundaries, columns=['Cluster', 'geometry'])

    # Assign lone points to nearest cluster
    df = assign_lone_points(df, gdf)

    return df, gdf





def cluster_single_commune(df, commune_id, max_clusters=15):
    """Clusters a single commune using hierarchical clustering and silhouette optimization."""
    df = df.copy()
    cluster_boundaries = []

    # Extract points for the specific commune
    commune_df = df[df['commune_id'] == commune_id].copy()
    points = commune_df[['latitude', 'longitude']].values

    if len(points) < 3:
        # Assign all points to one cluster if less than 3 points
        df.loc[commune_df.index, 'Cluster'] = f"{commune_id}_0"
        cluster_boundaries.append((f"{commune_id}_0", MultiPoint(points).convex_hull.buffer(0.0001)))
    else:
        # Apply hierarchical clustering with silhouette optimization
        labels = optimize_hierarchical_clustering(points, 2, max_clusters)

        # Assign clusters
        commune_df['Cluster'] = [f"{commune_id}_{l}" for l in labels]
        df.loc[commune_df.index, 'Cluster'] = commune_df['Cluster']

        # Compute boundaries for each cluster
        for cluster_label in np.unique(labels):
            cluster_points = points[labels == cluster_label]
            polygon = compute_alpha_shape(cluster_points)
            cluster_boundaries.append((f"{commune_id}_{cluster_label}", polygon))

    # Convert cluster boundaries to a GeoDataFrame
    gdf = gpd.GeoDataFrame(cluster_boundaries, columns=['Cluster', 'geometry'])

    # Assign lone points to nearest cluster
    df = assign_lone_points(df, gdf)

    return df, gdf






import geopandas as gpd
import numpy as np
import json
from shapely.geometry import MultiPolygon, Polygon, Point
import alphashape
from shapely.ops import unary_union

import alphashape
import numpy as np
from shapely.geometry import Point, Polygon

def generate_geojson(df):
    """Generates a GeoJSON structure where each commune contains its respective zones."""
    communes = {}

    gdf = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.longitude, df.latitude)])

    for commune_id in df['commune_id'].unique():
        commune_features = []
        cluster_polygons = {}

        commune_df = gdf[gdf['commune_id'] == commune_id]

        for zone_id in commune_df['zone_id'].unique():
            cluster_points = commune_df[commune_df['zone_id'] == zone_id].geometry.tolist()
            coordinates = list(set([(point.x, point.y) for point in cluster_points]))  # Remove duplicates

            polygon = None
            if len(coordinates) > 2:
                polygon = alphashape.alphashape(coordinates, 0.3)
            elif len(coordinates) == 2:
                # Create a circular buffer
                p1, p2 = cluster_points
                midpoint = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
                radius = np.linalg.norm([p1.x - p2.x, p1.y - p2.y]) / 2
                polygon = midpoint.buffer(radius)  # Create a circular area

            # Ensure polygon validity
            if polygon:
                if isinstance(polygon, Polygon):
                    polygons = [polygon]
                elif isinstance(polygon, MultiPolygon):
                    polygons = list(polygon.geoms)
                else:
                    polygons = []

                # Avoid overlapping with previous clusters
                existing_polygons = unary_union(list(cluster_polygons.values())) if cluster_polygons else None
                for poly in polygons:
                    if existing_polygons:
                        poly = poly.difference(existing_polygons)

                    if not poly.is_empty:
                        cluster_polygons[zone_id] = poly
                        feature = {
                            "type": "Feature",
                            "properties": {
                                "zone_id": str(zone_id),
                                "commune_id": str(commune_id),
                                "type": "zone"
                            },
                            "geometry": json.loads(gpd.GeoSeries([poly]).to_json())['features'][0]['geometry']
                        }
                        commune_features.append(feature)

            # Add individual points
            for point in cluster_points:
                point_feature = {
                    "type": "Feature",
                    "properties": {
                        "zone_id": str(zone_id),
                        "commune_id": str(commune_id),
                        "type": "point"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [point.x, point.y]
                    }
                }
                commune_features.append(point_feature)

        # Store commune data
        communes[str(commune_id)] = {
            "type": "FeatureCollection",
            "features": commune_features
        }

    return communes


def update_commune_geojson(df, commune_id, existing_geojson):
    """
    Updates the GeoJSON for a specific commune with new zone data.
    
    Parameters:
    - df: DataFrame containing updated data for the commune.
    - commune_id: The commune to update.

    Returns:
    - Updated GeoJSON dictionary.
    """

    existing_geojson = json.loads(existing_geojson)
    # Generate new features
    new_features = []
    cluster_polygons = {}
    
    # Filter the dataframe for this specific commune
    commune_df = df[df['commune_id'] == commune_id]
    gdf = gpd.GeoDataFrame(commune_df, geometry=[Point(xy) for xy in zip(commune_df.longitude, commune_df.latitude)])

    for zone_id in commune_df['zone_id'].unique():
        cluster_points = gdf[gdf['zone_id'].astype(str) == str(zone_id)].geometry.tolist()

        # Create the zone polygon
        polygon = None
        if len(cluster_points) > 2:
            coordinates = [(point.x, point.y) for point in cluster_points]
            polygon = alphashape.alphashape(coordinates, 0.3)

        # Handle clusters of size 2 by creating a circular boundary
        elif len(cluster_points) == 2:
            p1, p2 = cluster_points
            midpoint = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
            radius = np.linalg.norm([p1.x - p2.x, p1.y - p2.y]) / 2
            polygon = midpoint.buffer(radius)

        # Ensure correct polygon handling
        if polygon:
            if isinstance(polygon, Polygon):
                polygons = [polygon]
            elif isinstance(polygon, MultiPolygon):
                polygons = list(polygon.geoms)
            else:
                polygons = []

            # Ensure no overlaps with previous clusters
            existing_polygons = unary_union(list(cluster_polygons.values())) if cluster_polygons else None
            for poly in polygons:
                if existing_polygons:
                    poly = poly.difference(existing_polygons)

                if not poly.is_empty:
                    cluster_polygons[zone_id] = poly
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "zone_id": str(zone_id),
                            "commune_id": str(commune_id),
                            "type": "zone"
                        },
                        "geometry": json.loads(gpd.GeoSeries([poly]).to_json())['features'][0]['geometry']
                    }
                    new_features.append(feature)

        # Add individual points
        for point in cluster_points:
            point_feature = {
                "type": "Feature",
                "properties": {
                    "zone_id": str(zone_id),
                    "commune_id": str(commune_id),
                    "type": "point"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                }
            }
            new_features.append(point_feature)

    # Update the existing GeoJSON with new features
    existing_geojson["features"] = new_features

    # Save the updated GeoJSON

    return existing_geojson






import json

def merge_geojsons(geojson_list):
    """
    Merges multiple GeoJSON objects into a single structured dictionary,
    preserving the 'commune_id' structure.

    :param geojson_list: List of GeoJSON dictionaries to merge.
    :return: Merged GeoJSON dictionary.
    """
    merged_communes = {}

    for geojson in geojson_list:
        if isinstance(geojson, str):  # Convert from string if necessary
            geojson = json.loads(geojson)

        for commune_id, commune_data in geojson.items():
            if commune_id not in merged_communes:
                merged_communes[commune_id] = {
                    "type": "FeatureCollection",
                    "features": []
                }
            merged_communes[commune_id]["features"].extend(commune_data.get("features", []))

    return merged_communes
