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
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_rooms"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="rooms",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

class Song(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    video_id = models.CharField(max_length=50)
    thumbnail = models.URLField()
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    played_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('room', 'video_id')
        indexes = [
            models.Index(fields=['video_id']),
            models.Index(fields=['room', 'played_at']),
        ]

    def mark_played(self):
        self.played_at = timezone.now()
        self.save(update_fields=['played_at'])

    def was_played_within(self, minutes: int) -> bool:
        if not self.played_at:
            return False
        return timezone.now() - self.played_at < timedelta(minutes=minutes)

    def can_play_again(self, minutes: int = 10) -> bool:
        return not self.was_played_within(minutes)

    def __str__(self):
        return f"{self.title} ({self.video_id})"


class Vote(models.Model):
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('song', 'user', 'room')
        indexes = [
            models.Index(fields=['song']),
            models.Index(fields=['user']),
            models.Index(fields=['room']),
        ]

    def __str__(self):
        return f"Vote: {self.user_id} → {self.song_id}"
