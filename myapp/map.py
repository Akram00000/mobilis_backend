def create_map_from_geojson(geojson_path, map_path="cluster_zone_map_from_geojson.html"):
    """Create an interactive map from a GeoJSON file containing cluster information
    that was exported using the export_clusters_to_geojson function.
    
    Parameters:
    -----------
    geojson_path : str
        Path to the GeoJSON file containing cluster information
    map_path : str
        Path where the HTML map file will be saved
        
    Returns:
    --------
    None (saves map to disk)
    """
    import folium
    import numpy as np
    import geopandas as gpd
    import json
    from shapely.geometry import shape
    
    # Load the GeoJSON file
    try:
        with open(geojson_path, 'r') as f:
            raw_data = json.load(f)
        
        # Check if the GeoJSON is nested under a "geojson" key
        if "geojson" in raw_data:
            geojson_data = raw_data["geojson"]
        else:
            geojson_data = raw_data
            
        print(f"Loaded GeoJSON data from {geojson_path}")
    except Exception as e:
        print(f"Error loading GeoJSON file: {e}")
        return None
    
    # Extract metadata
    metadata = geojson_data.get('metadata', {})
    summary = metadata.get('summary', {})
    rep_assignments = metadata.get('representative_assignments', {})
    
    # Convert to GeoDataFrame for easier processing
    gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
    
    # Calculate map center
    if len(gdf) > 0:
        # Get the centroid of all geometries combined
        all_geometries = gdf.geometry.unary_union
        map_center = [all_geometries.centroid.y, all_geometries.centroid.x]
    else:
        # Default center if no geometries
        map_center = [0, 0]
    
    # Create map
    m = folium.Map(location=map_center, zoom_start=12)
    
    # Helper function to generate distinct colors
    def generate_distinct_colors(n):
        """Generate n visually distinct colors"""
        import colorsys
        
        colors = []
        for i in range(n):
            hue = i / n
            # Use golden ratio to get well-distributed hues
            hue = (hue + 0.618033988749895) % 1
            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue, 0.7, 0.95)
            # Convert to hex
            hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            colors.append(hex_color)
        return colors
    
    # Extract the unique representative IDs
    rep_ids = set()
    for feature in geojson_data["features"]:
        rep_id = feature["properties"].get("representative_id")
        if rep_id is not None:
            rep_ids.add(rep_id)
    rep_ids = sorted(list(rep_ids))
    
    # Create distinct colors for representatives
    rep_colors = {}
    colors = generate_distinct_colors(len(rep_ids))
    for i, rep_id in enumerate(rep_ids):
        rep_colors[rep_id] = colors[i % len(colors)]
    
    # Collect workloads from the metadata or feature properties
    workloads = {}
    for rep_id in rep_ids:
        # Try to get workload from metadata first
        rep_key = f"rep_{rep_id}"
        if rep_key in rep_assignments:
            workloads[rep_id] = rep_assignments[rep_key].get("workload_km", 0)
        else:
            # If not in metadata, try to get it from feature properties
            for feature in geojson_data["features"]:
                if feature["properties"].get("representative_id") == rep_id:
                    workloads[rep_id] = feature["properties"].get("rep_workload_km", 0)
                    break
    
    # Extract cluster to representative mapping
    rep_cluster_ids = {}
    for rep_key, rep_data in rep_assignments.items():
        rep_id = int(rep_key.replace("rep_", ""))
        rep_cluster_ids[rep_id] = rep_data.get("cluster_ids", [])
    
    # If metadata doesn't have cluster assignments, build them from features
    if not rep_cluster_ids:
        for feature in geojson_data["features"]:
            rep_id = feature["properties"].get("representative_id")
            cluster_id = feature["properties"].get("cluster_id")
            if rep_id is not None and cluster_id is not None:
                if rep_id not in rep_cluster_ids:
                    rep_cluster_ids[rep_id] = []
                if cluster_id not in rep_cluster_ids[rep_id]:
                    rep_cluster_ids[rep_id].append(cluster_id)
    
    # Process each feature and add to map
    for feature in geojson_data["features"]:
        properties = feature["properties"]
        geometry = feature["geometry"]
        
        cluster_id = properties.get("cluster_id")
        rep_id = properties.get("representative_id")
        points_count = properties.get("points_count", 0)
        commune = properties.get("commune", "Unknown")
        
        # Skip if no representative ID
        if rep_id is None:
            continue
        
        # Get color for this representative
        color = rep_colors.get(rep_id, '#808080')
        
        # Process geometry to folium format based on type
        if geometry["type"] == "Polygon":
            # For each polygon, convert coordinates to the format folium expects
            # GeoJSON Polygon coordinates are: [[[lon1, lat1], [lon2, lat2], ...]]
            # Folium expects: [[lat1, lon1], [lat2, lon2], ...]
            folium_coords = []
            for ring in geometry["coordinates"]:
                folium_ring = []
                for coord in ring:
                    # Reverse to [lat, lon] for folium
                    folium_ring.append([coord[1], coord[0]])
                folium_coords.append(folium_ring)
            
            folium.Polygon(
                locations=folium_coords,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.2,
                popup=f"Cluster {cluster_id} - Rep {rep_id} - Commune: {commune} - {points_count} points"
            ).add_to(m)
            
            # Add centroid marker
            poly_shape = shape(geometry)
            centroid = poly_shape.centroid
            
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=8,
                color='black',
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=f"Cluster: {cluster_id}<br>Rep: {rep_id}<br>Points: {points_count}<br>Area: {commune}"
            ).add_to(m)
            
            # Add cluster number as marker label
            folium.map.Marker(
                location=[centroid.y, centroid.x],
                icon=folium.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                    html=f'<div style="font-size: 10pt; color: white; font-weight: bold; text-align: center;">{cluster_id}</div>'
                )
            ).add_to(m)
            
        elif geometry["type"] == "MultiPolygon":
            # For each multi-polygon, convert coordinates
            # GeoJSON MultiPolygon coordinates are: [[[[lon1, lat1], [lon2, lat2], ...]], ...]
            for polygon in geometry["coordinates"]:
                folium_coords = []
                for ring in polygon:
                    folium_ring = []
                    for coord in ring:
                        # Reverse to [lat, lon] for folium
                        folium_ring.append([coord[1], coord[0]])
                    folium_coords.append(folium_ring)
                
                folium.Polygon(
                    locations=folium_coords,
                    color=color,
                    weight=2,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.2,
                    popup=f"Cluster {cluster_id} - Rep {rep_id} - Commune: {commune} - {points_count} points"
                ).add_to(m)
            
            # Add centroid marker for the overall multipolygon
            multi_poly_shape = shape(geometry)
            centroid = multi_poly_shape.centroid
            
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=8,
                color='black',
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=f"Cluster: {cluster_id}<br>Rep: {rep_id}<br>Points: {points_count}<br>Area: {commune}"
            ).add_to(m)
            
            # Add cluster number as marker label
            folium.map.Marker(
                location=[centroid.y, centroid.x],
                icon=folium.DivIcon(
                    icon_size=(20, 20),
                    icon_anchor=(10, 10),
                    html=f'<div style="font-size: 10pt; color: white; font-weight: bold; text-align: center;">{cluster_id}</div>'
                )
            ).add_to(m)
    
    # Add commune boundaries if they exist in the GeoJSON data
    # Look for features with type "CommuneBoundary"
    for feature in geojson_data.get("features", []):
        if feature.get("properties", {}).get("type") == "CommuneBoundary":
            geometry = feature["geometry"]
            commune_name = feature["properties"].get("commune", "Unknown")
            
            if geometry["type"] == "Polygon":
                folium_coords = []
                for ring in geometry["coordinates"]:
                    folium_ring = []
                    for coord in ring:
                        folium_ring.append([coord[1], coord[0]])
                    folium_coords.append(folium_ring)
                
                folium.Polygon(
                    locations=folium_coords,
                    color='black',
                    weight=1,
                    fill=False,
                    popup=f"Commune: {commune_name}"
                ).add_to(m)
            
            elif geometry["type"] == "MultiPolygon":
                for polygon in geometry["coordinates"]:
                    folium_coords = []
                    for ring in polygon:
                        folium_ring = []
                        for coord in ring:
                            folium_ring.append([coord[1], coord[0]])
                        folium_coords.append(folium_ring)
                    
                    folium.Polygon(
                        locations=folium_coords,
                        color='black',
                        weight=1,
                        fill=False,
                        popup=f"Commune: {commune_name}"
                    ).add_to(m)
    
    # Add legend showing representative assignments and colors
    legend_html = '''
    <div style="position: fixed; 
         top: 50px; right: 50px; width: 320px; height: auto;
         border:2px solid grey; z-index:9999; font-size:12px;
         background-color: white; padding: 10px;
         border-radius: 5px; overflow-y: auto; max-height: 500px;">
    <p><b>Representatives and their clusters:</b></p>
    '''
    
    for rep_id in sorted(rep_colors.keys()):
        color = rep_colors[rep_id]
        cluster_ids = rep_cluster_ids.get(rep_id, [])
        
        if not cluster_ids:
            continue
            
        # Count total points for this representative
        total_points = 0
        for feature in geojson_data["features"]:
            if feature["properties"].get("representative_id") == rep_id:
                total_points += feature["properties"].get("points_count", 0)
        
        workload = workloads.get(rep_id, 0)
        
        legend_html += f'''
        <div style="margin-bottom: 8px;">
            <span style="background-color:{color}; width:15px; height:15px; display:inline-block; margin-right:5px; border:1px solid black;"></span>
            <b>Rep {rep_id}:</b> {workload:.2f} km, {total_points} points, {len(cluster_ids)} clusters
        </div>
        <div style="margin-left: 20px; margin-bottom: 5px; font-size: 11px;">
            Clusters: {', '.join([str(cid) for cid in sorted(cluster_ids)])}
        </div>
        '''
    
    legend_html += '''
    </div>
    '''
    
    # Add second legend showing workload statistics
    stats_legend_html = '''
    <div style="position: fixed; 
         bottom: 50px; left: 50px; width: 320px; height: auto;
         border:2px solid grey; z-index:9999; font-size:12px;
         background-color: white; padding: 10px;
         border-radius: 5px; overflow-y: auto; max-height: 300px;">
    <p><b>Workload Statistics (km):</b></p>
    '''
    
    # Calculate statistics for workloads (use summary if available, otherwise calculate)
    if summary and workloads:
        avg_workload = summary.get("workload_avg_km", 0)
        std_dev = summary.get("workload_std_dev_km", 0)
        min_workload = summary.get("workload_min_km", 0)
        max_workload = summary.get("workload_max_km", 0)
    else:
        workload_values = list(workloads.values())
        if workload_values:
            avg_workload = sum(workload_values) / len(workload_values)
            std_dev = np.std(workload_values) if len(workload_values) > 1 else 0
            min_workload = min(workload_values)
            max_workload = max(workload_values)
        else:
            avg_workload = std_dev = min_workload = max_workload = 0
    
    max_min_ratio = (max_workload/min_workload) if min_workload > 0 else 0
    
    stats_legend_html += f'''
    <div><b>Average:</b> {avg_workload:.2f} km</div>
    <div><b>Std Dev:</b> {std_dev:.2f} km</div>
    <div><b>Min:</b> {min_workload:.2f} km</div>
    <div><b>Max:</b> {max_workload:.2f} km</div>
    <div><b>Max/Min Ratio:</b> {max_min_ratio:.2f} (if min > 0)</div>
    <hr>
    '''
    
    # Show table of all rep workloads
    stats_legend_html += '<table style="width:100%; font-size:11px;">'
    stats_legend_html += '<tr><th>Rep</th><th>Workload (km)</th><th>% Deviation</th></tr>'
    
    for rep_id, workload in sorted(workloads.items()):
        deviation = workload - avg_workload
        dev_percent = (deviation / avg_workload * 100) if avg_workload > 0 else 0
        
        # Color code by workload (red for high, green for low)
        color = "green" if deviation < -std_dev/2 else "red" if deviation > std_dev/2 else "black"
        
        stats_legend_html += f'''
        <tr style="color:{color};">
            <td>{rep_id}</td>
            <td>{workload:.2f}</td>
            <td>{dev_percent:+.1f}%</td>
        </tr>'''
        
    stats_legend_html += '</table>'
    stats_legend_html += '</div>'
    
    # Add legends to map
    m.get_root().html.add_child(folium.Element(legend_html))
    m.get_root().html.add_child(folium.Element(stats_legend_html))
    
    # Save the map
    m.save(map_path)
    print(f"Map saved to {map_path}")
    
    return m

create_map_from_geojson(r"C:\Users\benam\OneDrive\Desktop\group_project\backend\project\myapp\geijson.json",map_path="map.html")