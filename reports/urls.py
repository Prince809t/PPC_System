from django.urls import path
from . import views

urlpatterns = [
    path('operator-performance/', views.operator_performance_list, name='operator_performance_list'),
    path('operator-performance/<int:pk>/', views.operator_performance_detail, name='operator_performance_detail'),
    path('team-performance/', views.team_performance, name='team_performance'),
    path('order-quality/', views.order_quality, name='order_quality'),
]