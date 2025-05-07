# views.py

import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import requests
from io import StringIO

from myapp.WilayaSerializer import WilayaSerializer



class Wilaya_to_supabase(APIView):
    def post(self, request):
        csv_url = request.data.get('csv_url')
        if not csv_url:
            return Response({'error': 'CSV URL is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = requests.get(csv_url)
            response.raise_for_status()
            csv_file = StringIO(response.content.decode('utf-8'))
            df = pd.read_csv(csv_file)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        errors=[]
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            row_to_save ={}
            row_to_save['name'] = row_dict['Wilaya']
            row_to_save['id']=uuid.uuid4()
            print(row_to_save)
            serializer = WilayaSerializer(data=row_to_save)
            if serializer.is_valid():
                serializer.save()
            else:
                errors.append({'row': index + 1, 'errors': serializer.errors})
        if errors:
            return Response({'message': 'Imported with some errors', 'errors': errors}, status=status.HTTP_207_MULTI_STATUS)

        return Response({'message': 'CSV imported successfully'}, status=status.HTTP_201_CREATED)



