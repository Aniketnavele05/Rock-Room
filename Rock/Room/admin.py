from django.contrib import admin
from .models import Room, Song, RoomSong, Vote, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "is_staff", "is_active")
    search_fields = ("username",)
    ordering = ("id",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_code", "host", "created_at")
    search_fields = ("room_code", "host__username")
    list_filter = ("created_at",)
    readonly_fields = ("room_code", "created_at")
    filter_horizontal = ("members",)


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "video_id")
    search_fields = ("title", "video_id")
    readonly_fields = ("video_id",)


@admin.register(RoomSong)
class RoomSongAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "room",
        "song",
        "added_by",
        "created_at",
        "played_at",
    )
    list_filter = ("room", "played_at")
    search_fields = ("song__title", "room__room_code")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "room_song", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "room_song__song__title")
