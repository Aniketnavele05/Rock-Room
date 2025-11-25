from django.db import models
from django.contrib.auth.models import User
import random, string
# Create your models here.

class Room(models.Model):
    room_code = models.CharField(unique=True,max_length=6)
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=False)

    def save(self, *args, **kwargs):
        if not self.room_code:
            self.room_code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        char = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(char,k=6))
            if not Room.objects.filter(code==self.room_code).exists:
                return 