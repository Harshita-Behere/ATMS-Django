from django.contrib import admin
from django.urls import path , include
from users.views import redirect_user
from core.views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    
    path('redirect/', redirect_user, name='redirect_user'),

    #app urls
    path('users/', include('users.urls')),
    path('academics/', include('academics.urls')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('leaves/', include('leaves.urls')),
    
    
]