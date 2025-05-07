"""
URL configuration for mobilis_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from myapp.cviViews import CVICoordinatesAPIView, CVIDetailsAPIView, CVILastVisitsAPIView, CVIProfileAPIView, CVIVisitPerformanceAPIView, CVIVisitsRealizedVsGoal
from myapp.ZoneView import GenerateZones, GetGeojsonGlobal, GetGeojsonWilaya
from myapp.dashboardViews import AgentCoordinatesAPIView, AverageVisitDuration, CommerciauxActifs, LastWeekVisits, VisitedPDVPercentage, VisitsRealizedVsGoal, ZoneStatsAPIView, pdvVisited
from myapp.UserViews import AssignZoneView, LoginView, SignupView
from myapp.CommuneView import Commune_to_supabase
from myapp.PdvViews import AddPdv, DeletePdv, GetGeojson, GetPdv, UpdateStatusPdv, VisitPdv
from myapp.WilayaView import Wilaya_to_supabase
from rest_framework_simplejwt.views import TokenRefreshView





urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('assign/', AssignZoneView.as_view(), name='assignzonetouser'),
    path('wilaya_to_supa/', Wilaya_to_supabase.as_view(), name='wilaya_to_supa'),
    path('commune_to_supa/', Commune_to_supabase.as_view(), name='commune_to_supa'),
    path('AddPdv/', AddPdv.as_view(), name='AddPdv'),
    path('GetPdv/', GetPdv.as_view(), name='GetPdv'),
    path('UpdateStatusPdv/', UpdateStatusPdv.as_view(), name='UpdateStatusPdv'),
    path('VisitPdv/', VisitPdv.as_view(), name='VisitPdv'),
    path('DeletePdv/', DeletePdv.as_view(), name='DeletePdv'),
    path('dashboard/commerciaux_actifs/', CommerciauxActifs.as_view(), name='commerciaux_actifs'),
    path('dashboard/pdv_visited/', pdvVisited.as_view(), name='pdv_visited'),
    path('dashboard/average_visit_duration/', AverageVisitDuration.as_view(), name='average_visit_duration'),
    path('dashboard/visited_pdv/', VisitedPDVPercentage.as_view(), name='visited_pdv'),
    path('dashboard/visits_realized_vs_goal/', VisitsRealizedVsGoal.as_view(), name='visits_realized_vs_goal'),
    path('dashboard/last_week_visits/', LastWeekVisits.as_view(), name='last_week_visits'),
    path('dashboard/zone_stats/', ZoneStatsAPIView.as_view(), name='zone_stats'),
    path('dashboard/agent_coordinates/', AgentCoordinatesAPIView.as_view(), name='agent_coordinates'),
    path('GenerateZones/', GenerateZones.as_view(), name='GenerateZones'),
    path('GetGeojsonWilaya/', GetGeojsonWilaya.as_view(), name='GetGeojsonWilaya'),
    path('GetGeojson/', GetGeojsonGlobal.as_view(), name='GetGeojsonGlobal'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cvi/list/', CVIDetailsAPIView.as_view(), name='cvi_list'),
    path('cvi/<uuid:cvi_id>/profile/', CVIProfileAPIView.as_view(), name='cvi_profile'),
    path('cvi/<uuid:cvi_id>/last_visits/', CVILastVisitsAPIView.as_view(), name='cvi_last_visits'),
    path('cvi/<uuid:cvi_id>/visits_realized_vs_goal/', CVIVisitsRealizedVsGoal.as_view(), name='cvi_visits_realized_vs_goal'),
    path('cvi/<uuid:cvi_id>/visit_performance/', CVIVisitPerformanceAPIView.as_view(), name='cvi_visit_performance'),   
    path('cvi/<uuid:cvi_id>/coordinates/', CVICoordinatesAPIView.as_view(), name='cvi_coordinates'),
    path('get_geojson/', GetGeojson.as_view(), name='get_geojson'),
]

