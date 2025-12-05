from django.urls import path
from . import views
from .views import Registration, CreateRoom, JoinRoom, LeaveRoom, DetailRoom, SearchSong
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('',views.index,name='index'),
    path('home/',views.home,name='home'),
    path('api/register/', Registration.as_view(), name='registration'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/create_room/', CreateRoom.as_view(), name='create_room'),
    path('api/join_room/', JoinRoom.as_view(), name='join_room'),
    path('api/leave_room/', LeaveRoom.as_view(), name='leave_room'),
    path('api/detail_room/', DetailRoom.as_view(), name='detail_room'),
    path('room/',views.room,name='room'),
    path('api/search_song/',SearchSong.as_view(),name='search_song'),
]
