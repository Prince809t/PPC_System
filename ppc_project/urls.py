# from django.contrib import admin
# from django.urls import path, include
# from django.views.generic import RedirectView

# urlpatterns = [
#     path('admin/', admin.site.urls),

#     # Khali path (/) pe aane wale ko login pe bhejo
#     path('', RedirectView.as_view(url='/login/', permanent=False)),

#     path('', include('accounts.urls')),
# ]



from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Khali path ko login pe bhejo
    path('', RedirectView.as_view(url='/login/', permanent=False)),

    # Apps ke URLs
    path('', include('accounts.urls')),
    path('teams/', include('teams.urls')),

    path('planning/', include('planning.urls')),

    path('production/', include('production.urls')),

    path('quality/', include('quality.urls')),

    path('reports/', include('reports.urls')),
]

