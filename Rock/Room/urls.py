from django.urls import path, include
from . import views
from .views import Registration
from rest_framework_simplejwt.views import TokenObtainPairView ,TokenRefreshView

urlpatterns = [
    path('',views.index,name='home'),
    path('api/register/',Registration.as_view(),name='registration'),
    path('login/',TokenObtainPairView.as_view(),name='login'),
    path('refresh/',TokenRefreshView.as_view(),name='token_refresh'),
]