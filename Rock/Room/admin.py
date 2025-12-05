from django.contrib import admin
from .models import Room, Song, Vote
# Register your models here.
admin.site.register(Room)
admin.site.register(Song)
admin.site.register(Vote)