from django.urls import path
from . import views
from .views import (
    Registration, CreateRoom, JoinRoom, LeaveRoom,
    DetailRoom,
    SongAdd, RoomSongs, PlayedSongView, VoteToggleView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),

    # Auth
    path('api/register/', Registration.as_view(), name='registration'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Room
    path('api/create_room/', CreateRoom.as_view(), name='create_room'),
    path('api/join_room/', JoinRoom.as_view(), name='join_room'),
    path('api/leave_room/', LeaveRoom.as_view(), name='leave_room'),
    path('api/detail_room/', DetailRoom.as_view(), name='detail_room'),

    # UI
    path('room/', views.room, name='room'),

    # Songs
    path('api/add_song/', SongAdd.as_view(), name='add_song'),
    path('api/room_songs/', RoomSongs.as_view(), name='room_songs'),
    path('api/play_next/', PlayedSongView.as_view(), name='play_next'),

    # Votes
    path('api/vote/<int:song_id>/', VoteToggleView.as_view(), name='vote_toggle'),
]
