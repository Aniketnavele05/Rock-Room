from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import string


class User(AbstractUser):
    pass


class Room(models.Model):
    room_code = models.CharField(max_length=6, unique=True)
    host = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_room"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="rooms",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(chars, k=6))
            if not Room.objects.filter(room_code=code).exists():
                return code

    def __str__(self):
        return f"Room {self.room_code}"


class Song(models.Model):
    title = models.CharField(max_length=250)
    video_id = models.CharField(max_length=50, unique=True)
    thumbnail = models.URLField()

    def __str__(self):
        return f"{self.title} ({self.video_id})"


class RoomSong(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="room_songs"
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="room_songs"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    played_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("room", "song")
        indexes = [
            models.Index(fields=["room", "created_at"]),
        ]

    def mark_played(self):
        self.played_at = timezone.now()
        self.save(update_fields=["played_at"])

    def was_played_within(self, minutes: int) -> bool:
        if not self.played_at:
            return False
        return timezone.now() - self.played_at < timedelta(minutes=minutes)

    def can_play_again(self, minutes: int = 10) -> bool:
        return not self.was_played_within(minutes)

    def __str__(self):
        return f"{self.song.title} in {self.room.room_code}"


class Vote(models.Model):
    room_song = models.ForeignKey(
        RoomSong,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room_song", "user")
        indexes = [
            models.Index(fields=["room_song"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Vote: {self.user_id} → {self.room_song_id}"
