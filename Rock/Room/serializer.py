from rest_framework import serializers
from .models import User, Room, RoomSong
import re

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        user = User(username=validated_data["username"])
        user.set_password(validated_data["password"])
        user.save()
        return user

class RoomSerializer(serializers.ModelSerializer):
    host = serializers.CharField(source="host.username")
    is_host = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["id", "room_code", "host", "is_host"]

    def get_is_host(self, obj):
        return self.context["request"].user == obj.host

class RoomJoinSerializer(serializers.Serializer):
    room_code = serializers.CharField()

    def validate(self, data):
        try:
            data["room"] = Room.objects.get(room_code=data["room_code"])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found")
        return data

class RoomSongSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="song.title")
    video_id = serializers.CharField(source="song.video_id")
    thumbnail = serializers.URLField(source="song.thumbnail")
    vote_count = serializers.IntegerField(read_only=True)
    has_voted = serializers.BooleanField(read_only=True)

    class Meta:
        model = RoomSong
        fields = [
            "id", "title", "video_id", "thumbnail",
            "vote_count", "has_voted"
        ]

class UrlExtractSerializer(serializers.Serializer):
    url = serializers.CharField()

    yt_regex = re.compile(
        r'(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})'
    )

    def validate_url(self, value):
        match = self.yt_regex.search(value)
        if not match:
            raise serializers.ValidationError("Invalid YouTube URL")
        self.video_id = match.group(1)
        return value

