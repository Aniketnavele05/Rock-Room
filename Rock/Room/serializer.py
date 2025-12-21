from rest_framework import serializers
from .models import User, Room, Vote, RoomSong
import re

class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        user = User(username=username)
        user.set_password(password)
        user.save()
        return user


class RoomSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'host', 'room_code']

    def get_host(self, obj):
        return obj.host.username
    
    def is_host(self,obj):
        request = self.context["request"]
        return request.user == obj.host


class RoomJoinSerializer(serializers.Serializer):
    room_code = serializers.CharField()

    def validate(self, data):
        code = data['room_code']
        try:
            room = Room.objects.get(room_code = code)
        except Room.DoesNotExist:
            raise serializers.ValidationError('room does not exist')
        
        data['room'] = room
        return data


class SongSerializer(serializers.Serializer):
    title = serializers.CharField()
    video_id = serializers.CharField()
    thumbnail = serializers.CharField()
    channel = serializers.CharField()

class RoomSongSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="song.title")
    video_id = serializers.CharField(source="song.video_id")
    thumbnail = serializers.URLField(source="song.thumbnail")
    vote_count = serializers.IntegerField()
    has_voted = serializers.BooleanField()

    class Meta:
        model = RoomSong
        fields = [
            "id",
            "title",
            "video_id",
            "thumbnail",
            "vote_count",
            "has_voted",
        ]

class UrlExtractserializer(serializers.Serializer):
    url = serializers.CharField()

    yt_regex = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?'
        r'(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)'
        r'([A-Za-z0-9_-]{11})'
    )

    def validate_url(self, value):
        match = self.yt_regex.search(value)
        if not match:
            raise serializers.ValidationError("Invalid YouTube URL")

        # Store in serializer instance for view
        self.video_id = match.group(1)
        return value

class VoteSerializer(serializers.ModelSerializer):
    song_id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vote
        fields = ['id','song','user','created_at']