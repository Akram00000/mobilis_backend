# UserViews.py
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .Userserializers import UserAssignSerializer, UserLoginSerializer, UserSignupSerializer
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication, get_tokens_for_user

class SignupView(APIView):
    authentication_classes = []  # No authentication required for signup
    permission_classes = []      # No permissions required for signup
    
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'User created successfully!',
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user_id': str(user.id),
                'role': user.role,
                'tokens': tokens
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignZoneView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Add the authenticated user as the assigner if not provided
        data = request.data.copy()
        if 'assigner' not in data:
            data['assigner'] = str(request.user.id)
            
        serializer = UserAssignSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Zone assigned successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)