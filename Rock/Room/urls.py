from django.urls import path, include
from . import views
from .views import Registration

urlpatterns = [
    path('',views.index,name='home'),
    path('api/register/',Registration.as_view(),name='registration'),
]