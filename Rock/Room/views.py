import requests
from django.conf import settings
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Room, Song, User   # ✅ FIXED HERE
from rest_framework import status
from .serializer import (
    RegistrationSerializer, RoomCreateSerializer,
    RoomJoinSerializer, RoomLeaveSerializer,
    RoomSerializer, UrlExtractserializer
)

def index(request):
    return render(request, 'Auth.html')

def home(request):
    return render(request, 'home.html')

def room(request):
    return render(request, 'room.html')


class Registration(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect('/')
        return Response(serializer.errors, status=400)


class CreateRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RoomCreateSerializer(data={}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()

        request.user.current_room = room
        request.user.save()

        return Response(RoomCreateSerializer(room).data, status=202)


class JoinRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RoomJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['room_code']
        room = Room.objects.get(room_code=code)

        request.user.current_room = room
        request.user.save()

        return Response(RoomJoinSerializer(room).data)


class LeaveRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RoomLeaveSerializer(data={}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "left the room"})


class DetailRoom(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = request.user.current_room
        if not room:
            return Response({"detail": "no room"})
        return Response(RoomSerializer(room).data)


class SongAddToQueue(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UrlExtractserializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_id = serializer.video_id

        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )

        try:
            resp = requests.get(oembed_url, timeout=5)
            if resp.status_code != 200:
                return Response({"error": "Could not fetch YouTube metadata"}, status=400)
            meta = resp.json()
        except Exception:
            return Response({"error": "Invalid YouTube video or YouTube API error"}, status=400)

        title = meta.get("title")
        thumbnail = meta.get("thumbnail_url")

        room = request.user.current_room
        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        song = Song.objects.create(
            room=room, title=title,
            video_id=video_id,
            thumbnail=thumbnail,
            added_by=request.user
        )

        return Response({
            "id": song.id,
            "title": song.title,
            "video_id": song.video_id,
            "thumbnail": song.thumbnail
        }, status=201)


class RoomSongs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            room = request.user.current_room
            if not room:
                return Response({"error": "You are not in a room"}, status=400)

            songs = Song.objects.filter(room=room).order_by('id')

            data = [{
                "id": s.id,
                "title": s.title,
                "video_id": s.video_id,
                "thumbnail": s.thumbnail,
                "added_by": s.added_by.username
            } for s in songs]

            return Response(data)

        except Exception as e:
            print("ROOM SONG ERROR:", e)
            return Response({"error": str(e)}, status=500)
