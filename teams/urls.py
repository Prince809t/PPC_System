from django.urls import path
from . import views

urlpatterns = [
    path('layout/', views.team_layout_list, name='team_layout_list'),
    path('layout/<int:team_id>/', views.team_layout_detail, name='team_layout_detail'),
]