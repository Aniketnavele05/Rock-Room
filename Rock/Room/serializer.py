from rest_framework import serializers
from .models import User,Room

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

class RoomSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()
    class Meta:
        model = Room
        fields = ['id','host','room_code']

    def get_host(self,obj):
        return obj.host.username

class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        field = ['id','room_code']
        read_only_fields = ['id','room_code']

    def create(self,validate_data):
        host = self.context['request'].user
        room = Room.objects.create(host=host)
        return room

class RoomJoinSerializer(serializers.Serializer):
    room_code = serializers.CharField()
    
    def validate(self, data):
        code = data['room_code']
        if not Room.objects.filter(room_code=code).exists():
            raise serializers.ValidationError('room is not active')
        return data
    
class RoomLeaveSerializer(serializers.Serializer):
    def save(self):
        user  = self.context['request'].user

        if not user.current_room:
            raise serializers.ValidationError('You are not in room')
        
        room = user.current_room

        if user == room.host:
            room.delete()

        user.current_room = None
        user.save()