# views.py

from datetime import datetime
from django.utils import timezone
import uuid
from django.db import transaction
from flask import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from rest_framework.permissions import IsAuthenticated
from myapp.authentication import CustomJWTAuthentication
from myapp.PdvSerializers import PointOfSaleSerializer
from myapp.ZoneSerializer import ZoneSerializer
from myapp.ZoningModel import cluster_communes, update_commune_geojson
from myapp.models import Commune, PointOfSale, User, Wilaya, Zone
from myapp.zoning import assign_communes_from_geojson

# class Pdv_To_supabase(APIView):
#     authentication_classes = [CustomJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
        
#         wilaya_id = request.data.get('wilaya_id')
#         num_reps = int(request.data.get('num_reps', 15))
        
#         # Load data from CSV
#         csv_file = request.FILES.get('csv_file')
#         # Validate required parameters
#         if not csv_file:
#             return Response({'error': 'CSV file is required'}, status=status.HTTP_400_BAD_REQUEST)
            
#         if not wilaya_id:
#             return Response({'error': 'Wilaya ID is required'}, status=status.HTTP_400_BAD_REQUEST)
#         # Validate wilaya exists
#         try:
#             wilaya = Wilaya.objects.get(id=wilaya_id)
#         except Wilaya.DoesNotExist:
#             return Response({'error': f'Wilaya with ID {wilaya_id} not found'}, status=status.HTTP_404_NOT_FOUND)
#         except ValueError:
#             return Response({'error': 'Invalid Wilaya ID format'}, status=status.HTTP_400_BAD_REQUEST)
        
#         df = load_data_from_csv(csv_file, "Latitude", "Longitude")
        
#         # Assign communes using GeoJSON if needed
#         if not ('Commune' in df.columns and df['Commune'].notna().all()):
#             df = assign_communes_from_geojson(df, "https://qlluxlhcvjnlicxzxwry.supabase.co/storage/v1/object/sign/communes/geoBoundaries-DZA-ADM3.geojson?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjb21tdW5lcy9nZW9Cb3VuZGFyaWVzLURaQS1BRE0zLmdlb2pzb24iLCJpYXQiOjE3NDQ0NzYzOTMsImV4cCI6MzMyODA0NzYzOTN9.zEbNpeH6f2gp-n3Jrue20cC3cHAq4wZ00Duy6IeEsGs", "Latitude", "Longitude")
        
        
#         # Create a dictionary of clusters (starting with commune-based clusters)
#         clusters_dict = {}
#         for i, (commune_name, commune_df) in enumerate(df.groupby('Commune')):
#             clusters_dict[i] = commune_df.copy()
        
#         # Initialize the assignment with optimized algorithm
#         rep_clusters = optimize_cluster_assignments(clusters_dict, num_reps)
#         std_dev, max_min_ratio, workloads = evaluate_workload_balance(clusters_dict, rep_clusters)
      
#         # Parameters for iterative improvement
#         max_iterations = 30
#         target_std_dev = 10  # Target standard deviation in km
#         target_max_min_ratio = 1.1  # Target max/min ratio
#         next_cluster_id = len(clusters_dict)  # For assigning IDs to new clusters
        
#         # Track clusters that have already been split and how many times
#         already_split = {}
        
#         # Iteratively improve workload balance by splitting overloaded clusters
#         iteration = 0
#         while (iteration < max_iterations and 
#             (std_dev > target_std_dev or max_min_ratio > target_max_min_ratio)):
#             iteration += 1
            
#             # Find cluster to split, considering history of splits
#             rep_to_split, cluster_to_split = find_cluster_to_split(clusters_dict, rep_clusters, workloads, already_split)
            
#             if rep_to_split is None or cluster_to_split is None:
#                 break
            
#             # Update split history
#             already_split[cluster_to_split] = already_split.get(cluster_to_split, 0) + 1
#             split_count = already_split[cluster_to_split]
            
#             # Split the cluster with potentially more sub-clusters for clusters that have been split before
#             if cluster_to_split in clusters_dict:
#                 # Determine number of sub-clusters based on split history and size
#                 cluster_size = len(clusters_dict[cluster_to_split])
#                 base_num_clusters = 2
                
#                 # For larger clusters or clusters that have been split multiple times, create more sub-clusters
#                 if split_count > 1 or cluster_size > 50:
#                     base_num_clusters = min(3 + split_count, 5)  # Limit to max 5 sub-clusters
                
                
#                 # Try splitting with multiple attempts
#                 sub_clusters = split_cluster(clusters_dict[cluster_to_split], num_clusters=base_num_clusters, max_attempts=3)
                
#                 if len(sub_clusters) <= 1:
#                     # Mark as not splittable to avoid trying again
#                     already_split[cluster_to_split] = -1
#                     continue
                    
#                 # Remove original cluster from the dictionary
#                 clusters_dict.pop(cluster_to_split)
                
#                 # Add new sub-clusters to dictionary
#                 new_cluster_ids = []
#                 for sub_cluster in sub_clusters:
#                     if len(sub_cluster) > 0:  # Avoid empty clusters
#                         clusters_dict[next_cluster_id] = sub_cluster
#                         new_cluster_ids.append(next_cluster_id)
#                         next_cluster_id += 1
                
                
#                 # Remove the original cluster ID from rep assignments
#                 for rep_id in rep_clusters:
#                     if cluster_to_split in rep_clusters[rep_id]:
#                         rep_clusters[rep_id].remove(cluster_to_split)
                
#                 # Optimize assignments of all clusters
#                 rep_clusters = optimize_cluster_assignments(clusters_dict, num_reps)
                    
#                 # Re-evaluate workload balance
#                 prev_std_dev, prev_max_min_ratio = std_dev, max_min_ratio
#                 std_dev, max_min_ratio, workloads = evaluate_workload_balance(clusters_dict, rep_clusters)
                
#                 improvement = (prev_std_dev - std_dev) / prev_std_dev * 100 if prev_std_dev > 0 else 0
                
#                 # Early stopping if improvement is very small
#                 if improvement < 1.0 and iteration > 5:
#                     break
        
#         # Generate temporary file path for GeoJSON output
#         import tempfile
#         import os
#         import json
#         import uuid
        
#         temp_geojson_path = os.path.join(tempfile.gettempdir(), f"temp_geojson_{uuid.uuid4()}.geojson")
        
#         # Export clusters to GeoJSON using existing function
#         # Pass the path to commune geojson for clipping - use the same source used for assignment
#         export_clusters_to_geojson(
#             clusters_dict, 
#             rep_clusters, 
#             workloads, 
#             temp_geojson_path,
#             commune_geojson_path="https://qlluxlhcvjnlicxzxwry.supabase.co/storage/v1/object/sign/communes/geoBoundaries-DZA-ADM3.geojson?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJjb21tdW5lcy9nZW9Cb3VuZGFyaWVzLURaQS1BRE0zLmdlb2pzb24iLCJpYXQiOjE3NDQ0NzYzOTMsImV4cCI6MzMyODA0NzYzOTN9.zEbNpeH6f2gp-n3Jrue20cC3cHAq4wZ00Duy6IeEsGs"
#         )
        
#         # Create zones and update GeoJSON
#         created_zones = []
#         zone_cluster_map = {}  # Maps cluster_id to zone_id
        
#         # Create zones for each cluster
#         for cluster_id in clusters_dict.keys():
#             # Create a zone record in the database
#             zone = Zone.objects.create(
#                 id = uuid.uuid4(),
#                 name=f"Zone_{cluster_id}",
#                 created_at=timezone.now(),
#                 # Commune will be set later
#             )
            
#             # Store mapping of cluster_id to zone_id
#             zone_cluster_map[cluster_id] = str(zone.id)
#             created_zones.append(zone)
        
#         # Load the GeoJSON file
#         with open(temp_geojson_path, 'r') as f:
#             geojson_data = json.load(f)
        
#         # Update GeoJSON features to include zone_id
#         # FIX: The features key directly contains a list, not another dictionary
#         for feature in geojson_data.get('features', []):
#             properties = feature.get('properties', {})
#             cluster_id = properties.get('cluster_id')
            
#             if cluster_id is not None and cluster_id in zone_cluster_map:
#                 # Add zone_id to properties
#                 properties['zone_id'] = zone_cluster_map[cluster_id]
                
#                 # Get the commune name from the feature properties
#                 commune_name = properties.get('commune')
#                 if commune_name and commune_name != "Unknown":
#                     # Try to find commune in database
#                     try:
#                         commune = Commune.objects.get(name=commune_name)
                        
#                         # Update zone with commune
#                         zone_id = zone_cluster_map[cluster_id]
#                         zone = Zone.objects.get(id=zone_id)
                        
#                         if zone.commune is None:  # Only set if not already set
#                             zone.commune = commune
#                             zone.save()
#                     except Commune.DoesNotExist:
#                         pass  # Skip if commune not found
        
#         # Save updated GeoJSON to wilaya
#         wilaya.geojson = json.dumps(geojson_data)
#         wilaya.save()
        
#         # Clean up temporary file
#         if os.path.exists(temp_geojson_path):
#             os.remove(temp_geojson_path)
        
#         # Return response
#         return Response({
#             'success': True,
#             'message': f'Successfully processed data and created {len(created_zones)} zones',
#             'zones': [{'id': str(zone.id), 'name': zone.name} for zone in created_zones],
#             'wilaya_id': str(wilaya.id)
#         }, status=status.HTTP_200_OK)


class GetGeojson(APIView):
    def get(self, request):
        user=request.user
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role=='manager':
            geojson=user.wilaya.geojson
            if geojson:
                return Response({'geojson':json.loads(geojson)}, status=status.HTTP_200_OK, content_type='application/json')
            else:
                return Response({'error': 'geojson not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'You are not authorized to view this page'}, status=status.HTTP_403_FORBIDDEN)


class AddPdv(APIView):
    def post(self,request):
        data=request.data
        id = data.get('id')
        latitude=data['latitude']
        longitude=data['longitude']
        commune=data['commune']
        new_pdv={}
        new_pdv['latitude']=latitude
        new_pdv['longitude']=longitude
        new_pdv['commune']=commune
        new_pdv['id']=uuid.uuid4()
        commune=Commune.objects.get(id=commune)
        if not id or not latitude or not longitude or not commune:
            return Response({'error': 'ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        existing_pdv = PointOfSale.objects.filter(latitude=latitude, longitude=longitude)
        if existing_pdv.exists():
            #existing_pdv.delete()
            return Response({'error': 'Point of sale already exists  '}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role!='admin' and user.role!='manager':
            return Response({'error': 'you can\'t insert pdv'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role=='manager':
            if commune.wilaya.id!=user.wilaya.id:
                return Response({'error': 'you can\'t insert pdv'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer=PointOfSaleSerializer(data=new_pdv)
        if serializer.is_valid():
            serializer.save()
            
            if commune.wilaya.geojson==None:
                return Response({'message: insertedsuccessfully'},status=status.HTTP_201_CREATED)
            else:
                json_data=commune.wilaya.geojson
                pdvs=list(PointOfSale.objects.filter(commune=commune.id).values())
                df=pd.DataFrame(pdvs)
                number_of_zones=df['zone_id'].unique().shape[0]
                print(number_of_zones)
                print(df['zone_id'].head())
                print(df.columns)
                zone_ids=[]
                for pdv in pdvs:
                    temp=PointOfSale.objects.get(id=pdv['id'])
                    if temp.zone==None:
                        continue
                    temp.zone=None
                    temp.save()
                    zone_ids.append(pdv['zone_id'])
                    pdv['zone_id']=None
                zone_ids=set(zone_ids)
                for id in zone_ids:
                    zone=Zone.objects.get(id=id)
                    zone.delete()
                print(df['zone_id'].head())
                df,gdf = cluster_communes(df,number_of_zones+3)
                errors=[]
                zones={}
                print("clustering")
                print(df[['zone_id','Cluster']].head())
                for zone in df['Cluster'].unique():
                    id =uuid.uuid4()
                    created_at=datetime.now()
                    new_zone_dict={'id':id,'created_at':created_at,'commune':commune.id,'zone':zone}
                    new_zone=ZoneSerializer(data=new_zone_dict)
                    if new_zone.is_valid():
                        df.loc[df['Cluster'] == zone, 'zone_id'] = id
                        new_zone.save()
                        zones[id]=new_zone.instance
                    else:
                        print('error')
                        errors.append({'errors': new_zone.errors})
                print(df[['zone_id','Cluster']].head())

                point_updates = []
                for _, row in df.iterrows():
                    pos = PointOfSale.objects.get(id=row['id'])
                    pos.zone = zones[row['zone_id']]
                    point_updates.append(pos)
                with transaction.atomic():
                    PointOfSale.objects.bulk_update(point_updates, ['zone'])
                new_geojson=update_commune_geojson(df,commune.id,json_data)
                commune.wilaya.geojson=json.dumps(new_geojson)
                commune.wilaya.save()
                return Response({'message': 'inserted successfully',
                                 'geojson':new_geojson },status=status.HTTP_201_CREATED)
            
            
        else:
            print(serializer.errors)
            return Response({'message': 'failed to insert',
                             'errors':serializer.errors},status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
class GetPdv(APIView):
    def get(self, request, format=None):
        data=request.data
        if not data.get('id'):
            return Response({'message': 'ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        user=User.objects.get(id=data.get('id'))
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role=='admin':
            pdvs = list(PointOfSale.objects.all().values())
            return Response({'pdvs': pdvs},status=status.HTTP_200_OK)     
        elif user.role=='manager':
            wilaya=user.wilaya
            communes=Commune.objects.filter(wilaya=wilaya)
            pdvs=PointOfSale.objects.filter(commune__in=communes)
            return Response({'pdvs':pdvs}, status=status.HTTP_200_OK)
        elif user.role=='agent':
            pdvs=PointOfSale.objects.filter(manager=user.id)
            return Response({'pdvs':pdvs}, status=status.HTTP_200_OK) 
        
        return Response({'error':'you are not authorized to view this page'}, status=status.HTTP_403_FORBIDDEN)
    
    
    
    
    
    
class UpdateStatusPdv(APIView):
    def post(self, request):
        data=request.data
        pdv=data.get('pdv')
        status=data.get('status')
        if not data.get('id') or not data.get('pdv'):
            return Response({'error':'id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user=User.objects.get(id=data.get('id'))
        pdv=PointOfSale.get(id=data.get('pdv'))
        commune=Commune.objects.get(id=pdv.commune)
        if not user or not pdv:
            return Response({'error':'unauthorized'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role=='manager':
            wilaya=Wilaya.objects.get(id=commune.wilaya)
            if user.wilaya!=wilaya:
                return Response({'error':'you can\'t update this pdv'}, status=status.HTTP_400_BAD_REQUEST)
            pdv.status=status
            pdv.save()
            return Response({'message':"status updated successfully"}, status=status.HTTP_200_OK)
        elif user.role=='admin':
            pdv.status=status
            pdv.save()
            return Response({'message':"status updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'error':'you can\'t update this pdv, unauthorized'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            
            
            
            
class VisitPdv(APIView):
    def post(self, request):
        data=request.data
        if not data.get('pdv') or not data.get('id'):
            return Response({'error':'missing pdv or id'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user=User.objects.get(id=data.get('id'))
            pdv=PointOfSale.objects.get(id=data.get('pdv'))
        except User.DoesNotExist or PointOfSale.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role!="agent":
            return Response({'error':"you are not an agent"},status=status.HTTP_403_FORBIDDEN)
        pdv.last_visit=datetime.now()
        pdv.save()
        return Response({'message:':"visited successfully"}, status=status.HTTP_200_OK)
    





class DeletePdv(APIView):
    def post(self, request):
        data=request.data
        pdv=data.get('pdv')
        status=data.get('status')
        if not data.get('id') or not data.get('pdv'):
            return Response({'error':'id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user=User.objects.get(id=data.get('id'))
            pdv=PointOfSale.objects.get(id=data.get('pdv'))
        except User.DoesNotExist or PointOfSale.DoesNotExist or Commune.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        commune=Commune.objects.get(id=pdv.commune)
        if user.role=='manager':
            wilaya=Wilaya.objects.get(id=commune.wilaya)
            if user.wilaya!=wilaya:
                return Response({'error':'you can\'t update this pdv'}, status=status.HTTP_400_BAD_REQUEST)
            pdv.delete()
            return Response({'message':"pdv deleted successfully"}, status=status.HTTP_200_OK)
        elif user.role=='admin':
            pdv.delete()
            return Response({'message':"deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({'error':'you can\'t delete this pdv, unauthorized'}, status=status.HTTP_400_BAD_REQUEST)
        