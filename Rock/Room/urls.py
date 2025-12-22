from django.urls import path
from . import views
from .views import (
    Registration,
    CreateRoom,
    JoinRoom,
    LeaveRoom,
    DetailRoom,
    SongAdd,
    RoomSongs,
    VoteToggle,
    PlayNextSong,
    NowPlaying
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # ------------------------
    # UI Pages
    # ------------------------
    path("", views.index, name="index"),
    path("home/", views.home, name="home"),
    path("room/", views.room, name="room"),

    # ------------------------
    # Auth
    # ------------------------
    path("api/register/", Registration.as_view(), name="registration"),
    path("api/login/", TokenObtainPairView.as_view(), name="login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ------------------------
    # Room Management
    # ------------------------
    path("api/room/create/", CreateRoom.as_view(), name="create_room"),
    path("api/room/join/", JoinRoom.as_view(), name="join_room"),
    path("api/room/leave/", LeaveRoom.as_view(), name="leave_room"),
    path("api/room/detail/", DetailRoom.as_view(), name="room_detail"),

    # ------------------------
    # Songs / Queue
    # ------------------------
    path("api/songs/add/", SongAdd.as_view(), name="add_song"),
    path("api/songs/queue/", RoomSongs.as_view(), name="room_songs"),
    path("api/songs/play-next/", PlayNextSong.as_view(), name="play_next"),
    path("api/songs/now-playing/", NowPlaying.as_view()),

    # ------------------------
    # Votes
    # ------------------------
    path(
        "api/songs/<int:room_song_id>/vote/",
        VoteToggle.as_view(),
        name="vote_toggle",
    ),
]
