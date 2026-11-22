from django.urls import path
from . import views

urlpatterns = [
    # PPC-04
    path('initial/', views.initial_qc_list, name='initial_qc_list'),
    path('initial/new/', views.initial_qc_create, name='initial_qc_create'),
    path('initial/<int:pk>/', views.initial_qc_detail, name='initial_qc_detail'),

    # PPC-05
    path('final/', views.final_qc_list, name='final_qc_list'),
    path('final/new/', views.final_qc_create, name='final_qc_create'),
    path('final/<int:pk>/', views.final_qc_detail, name='final_qc_detail'),
]