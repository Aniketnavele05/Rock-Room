from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.conf import settings
import random, string
from django.utils import timezone
from datetime import timedelta
# Create your models here.

class Room(models.Model):
    room_code = models.CharField(unique=True,max_length=6)
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        char = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(char,k=6))
            if not Room.objects.filter(room_code = code).exists():
                return  code
            
class User(AbstractUser):
    current_room = models.ForeignKey(Room, null=True, on_delete=models.SET_NULL)

class Song(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    video_id = models.CharField(max_length=50)
    thumbnail = models.URLField()
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    played_at = models.DateTimeField(null=True,blank=True)

    class Meta:
        unique_together = ('room', 'video_id')
        indexes = [
            models.Index(fields=['video_id']),
            models.Index(fields=['room', 'played_at']),
        ]
    
    def mark_played(self):
        self.played_at = timezone.now()
        self.save(update_fields=['played_at'])

    def was_played_within(self,minutes:int) -> bool:
        if not self.played_at:
            return False
        return (timezone.now()-self.played_at) < timedelta(minutes=minutes)
    
    def can_played_again(self,minutes:int=10) -> bool:
        return not self.was_played_within(minutes)

class Vote(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('song', 'user')  # one vote per user per song
        indexes = [
            models.Index(fields=['song']),
            models.Index(fields=['user']),
        ]