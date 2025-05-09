from django.utils import timezone
from rest_framework.response import Response
from myapp.authentication import CustomJWTAuthentication
from myapp.models import Coordinates, PointOfSale, User, Visit, Zone
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Avg, Count, F, Q
from rest_framework.permissions import IsAuthenticated

class CommerciauxActifs(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                commerciaux = User.objects.filter(role='agent')
                
                now = timezone.now()
                current_year, current_month = now.year, now.month
                
                if current_month == 1:  
                    last_year, last_month = current_year - 1, 12
                else:
                    last_year, last_month = current_year, current_month - 1

                actifs_current = commerciaux.filter(
                    id__in=Visit.objects.filter(
                        visit_time__year=current_year, visit_time__month=current_month
                    ).values_list('agent', flat=True)
                ).count()

                actifs_last = commerciaux.filter(
                    id__in=Visit.objects.filter(
                        visit_time__year=last_year, visit_time__month=last_month
                    ).values_list('agent', flat=True)
                ).count()

                if actifs_last == 0:
                    percentage_change = 100 if actifs_current > 0 else 0  
                else:
                    percentage_change = ((actifs_current - actifs_last) / actifs_last) * 100

                return Response({
                    'total': commerciaux.count(),
                    'actifs_current_month': actifs_current,
                    'actifs_last_month': actifs_last,
                    'percentage_change': round(percentage_change, 2)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

    
class pdvVisited(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                now = timezone.now()
                current_year, current_month = now.year, now.month

                if current_month == 1:
                    last_year, last_month = current_year - 1, 12
                else:
                    last_year, last_month = current_year, current_month - 1

                total_pdv = PointOfSale.objects.count()

                visited_current_month = (
                    Visit.objects.filter(visit_time__year=current_year, visit_time__month=current_month)
                    .values("pdv").distinct().count()
                )

                visited_last_month = (
                    Visit.objects.filter(visit_time__year=last_year, visit_time__month=last_month)
                    .values("pdv").distinct().count()
                )

                if visited_last_month == 0:
                    percentage_change = 100 if visited_current_month > 0 else 0
                else:
                    percentage_change = ((visited_current_month - visited_last_month) / visited_last_month) * 100

                return Response({
                    "total_pdv": total_pdv,
                    "visited_current_month": visited_current_month,
                    "visited_last_month": visited_last_month,
                    "percentage_change": round(percentage_change, 2),
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

class AverageVisitDuration(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                now = timezone.now()
                current_year, current_month = now.year, now.month
                
                if current_month == 1:  
                    last_year, last_month = current_year - 1, 12
                else:
                    last_year, last_month = current_year, current_month - 1

                avg_duration_current = Visit.objects.filter(
                    visit_time__year=current_year, visit_time__month=current_month
                ).aggregate(avg_duration=Avg("duration"))["avg_duration"] or 0

                avg_duration_last = Visit.objects.filter(
                    visit_time__year=last_year, visit_time__month=last_month
                ).aggregate(avg_duration=Avg("duration"))["avg_duration"] or 0

                if avg_duration_last == 0:
                    percentage_change = 100 if avg_duration_current > 0 else 0  
                else:
                    percentage_change = ((avg_duration_current - avg_duration_last) / avg_duration_last) * 100

                return Response({
                    "average_duration_current_month": round(avg_duration_current, 2),
                    "average_duration_last_month": round(avg_duration_last, 2),
                    "percentage_change": round(percentage_change, 2)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)


class VisitedPDVPercentage(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                now = timezone.now()
                current_year, current_month = now.year, now.month

                if current_month == 1:
                    last_year, last_month = current_year - 1, 12
                else:
                    last_year, last_month = current_year, current_month - 1

                total_pdv = PointOfSale.objects.count()

                visited_pdv_current = Visit.objects.filter(
                    visit_time__year=current_year, visit_time__month=current_month
                ).values("pdv").distinct().count()

                visited_pdv_last = Visit.objects.filter(
                    visit_time__year=last_year, visit_time__month=last_month
                ).values("pdv").distinct().count()

                percentage_visited_current = (visited_pdv_current / total_pdv * 100) if total_pdv > 0 else 0
                percentage_visited_last = (visited_pdv_last / total_pdv * 100) if total_pdv > 0 else 0

                if percentage_visited_last == 0:
                    percentage_change = 100 if percentage_visited_current > 0 else 0
                else:
                    percentage_change = ((percentage_visited_current - percentage_visited_last) / percentage_visited_last) * 100

                return Response({
                    "total_pdv": total_pdv,
                    "visited_pdv_current_month": visited_pdv_current,
                    "visited_pdv_last_month": visited_pdv_last,
                    "percentage_visited_current_month": round(percentage_visited_current, 2),
                    "percentage_visited_last_month": round(percentage_visited_last, 2),
                    "percentage_change": round(percentage_change, 2)
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
class VisitsRealizedVsGoal(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                now = timezone.now()
                current_year, current_month = now.year, now.month

                data = []

                for i in range(6):
                    month = current_month - i
                    year = current_year

                    if month <= 0:  
                        month += 12
                        year -= 1

                    realized_visits = Visit.objects.filter(
                        visit_time__year=year, visit_time__month=month
                    ).count()

                    goal_visits = PointOfSale.objects.values("zone").annotate(total_pdv=Count("id"))
                    total_goal_visits = sum(zone["total_pdv"] for zone in goal_visits)

                    # Append to result list
                    data.append({
                        "year": year,
                        "month": month,
                        "realized_visits": realized_visits,
                        "goal_visits": total_goal_visits
                    })

                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
class LastWeekVisits(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id)
            if user_profile.role == 'admin':
                now = timezone.now()
                last_week = now - timezone.timedelta(days=7)

                visits = Visit.objects.filter(visit_time__gte=last_week).select_related("agent", "pdv__commune").values(
                    "id",
                    "visit_time",
                    "duration",
                    agent_email=F("agent__email"),
                    commune_name=F("pdv__commune__name")
                )

                return Response(list(visits), status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
    
class ZoneStatsAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id) 
            
            if user_profile.role == 'admin':
                now = timezone.now()
                start_of_week = now - timezone.timedelta(days=now.weekday())  

                zones = Zone.objects.select_related("manager").annotate(
                    total_pdv=Count("pointofsale"), 
                    visited_pdv=Count(
                        "pointofsale__visit",
                        filter=Q(pointofsale__visit__visit_time__gte=start_of_week),
                        distinct=True
                    ) 
                )

                data = []
                for zone in zones:
                    data.append({
                        "zone_id": str(zone.id),
                        "zone_manager": f"{zone.manager.first_name} {zone.manager.last_name}" if zone.manager else None,
                        "total_pdv": zone.total_pdv,
                        "visited_pdv_this_week": zone.visited_pdv,
                    })

                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
class AgentCoordinatesAPIView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        try:
            user_profile = User.objects.get(id=user.id) 
            
            if user_profile.role == 'admin':
                coordinates = Coordinates.objects.filter(
                    user__role='agent'
                ).select_related('user').values(
                    'id',
                    'created_at',
                    'longitude',
                    'lattitude',
                    'user_id',  
                    user_email=F('user__email'),
                    user_phone=F('user__phone'),
                    user_last_seen=F('user__last_seen')
                ).order_by('-created_at')
                
            elif user_profile.role == 'manager':
                coordinates = Coordinates.objects.filter(
                    user__role='agent',
                    user__manager=user_profile 
                ).select_related('user').values(
                    'id',
                    'created_at',
                    'longitude',
                    'lattitude',
                    'user_id',  
                    user_email=F('user__email'),
                    user_phone=F('user__phone'),
                    user_last_seen=F('user__last_seen')
                ).order_by('-created_at')
            else:
                return Response({
                    "error": "Unauthorized role"
                }, status=status.HTTP_403_FORBIDDEN)
                
            return Response(list(coordinates), status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "error": "User profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

 