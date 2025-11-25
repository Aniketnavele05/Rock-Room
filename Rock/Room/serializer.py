from rest_framework import serializers
from .models import User

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','password']

    def create(Self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        user = User(username=username)
        user.set_password(password)
        user.save()
        return user