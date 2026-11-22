from django.urls import path
from . import views

urlpatterns = [
    # Output
    path('output/', views.my_output_list, name='my_output_list'),
    path('output/new/', views.output_create, name='output_create'),

    # Downtime
    path('downtime/', views.downtime_list, name='downtime_list'),
    path('downtime/new/', views.downtime_create, name='downtime_create'),

    # QC
    path('qc/pending/', views.qc_pending_list, name='qc_pending_list'),
    path('qc/check/<int:pk>/', views.qc_mark_checked, name='qc_mark_checked'),
]