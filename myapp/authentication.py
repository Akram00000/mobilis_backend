# Replace your authentication.py with this:

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get('user_id')
        except KeyError:
            raise exceptions.AuthenticationFailed('Token contained no recognizable user identification')

        from .models import User
        try:
            user = User.objects.get(id=user_id)
            if not hasattr(user, 'is_authenticated'):
                user.is_authenticated = True
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        return user
        
def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user
    """
    refresh = RefreshToken()
    
    # Add custom claims
    refresh['user_id'] = str(user.id)
    refresh['role'] = user.role
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }