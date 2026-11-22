from django.urls import path
from . import views

urlpatterns = [
    # Allocation
    path('allocation/', views.allocation_list, name='allocation_list'),
    path('allocation/new/', views.allocation_create, name='allocation_create'),
    path('allocation/<int:pk>/delete/', views.allocation_delete, name='allocation_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
]