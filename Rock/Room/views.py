import requests
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.conf import settings
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Room, Song, User, Vote
from rest_framework import status
from .serializer import (
    RegistrationSerializer, RoomCreateSerializer,
    RoomJoinSerializer, RoomLeaveSerializer,
    RoomSerializer, UrlExtractserializer,
    VoteSerializer,
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
            return Response({"detail": "no room"}, status=400)
        return Response(RoomSerializer(room).data)


class SongAddToQueue(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UrlExtractserializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_id = serializer.video_id
        room = request.user.current_room

        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        # Call YouTube oEmbed API
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

        # 1. Song already in queue (room-scoped)
        if Song.objects.filter(room=room, video_id=video_id, played_at__isnull=True).exists():
            return Response({"error": "Song already in queue"}, status=400)

        # 2. Check recently played (room-scoped)
        recent = Song.objects.filter(room=room, video_id=video_id, played_at__isnull=False)
        for s in recent:
            if not s.can_played_again():  # uses your 10-min window
                return Response({
                    "error": "This song was played recently. Try again later."
                }, status=400)

        # 3. Add song to queue
        song = Song.objects.create(
            room=room,
            title=title,
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
        room = request.user.current_room
        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        # Room-scoped vote_count using a filtered Count
        songs = (
            Song.objects.filter(room=room, played_at__isnull=True)
                        .annotate(vote_count=Count('votes', filter=Q(votes__room=room)))
                        .order_by("-vote_count", "created_at")
        )

        data = [{
            "id": s.id,
            "title": s.title,
            "video_id": s.video_id,
            "thumbnail": s.thumbnail,
            "added_by": s.added_by.username,
            "vote_count": getattr(s, "vote_count", 0)
        } for s in songs]

        return Response(data)


class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, song_id):
        user = request.user
        room = user.current_room
        if not room:
            return Response({'error': 'You are not in a room'}, status=400)

        try:
            song = Song.objects.get(id=song_id, room=room)
        except Song.DoesNotExist:
            return Response({'error': 'Song not found in this room'}, status=404)

        try:
            with transaction.atomic():
                vote = Vote.objects.create(song=song, user=user, room=room)
        except IntegrityError:
            return Response({'error': 'You already voted for this song'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = VoteSerializer(vote)
        vote_count = Vote.objects.filter(song=song, room=room).count()
        return Response({"vote": serializer.data, "vote_count": vote_count}, status=status.HTTP_201_CREATED)

    def delete(self, request, song_id):
        user = request.user
        room = user.current_room
        if not room:
            return Response({'error': 'You are not in a room'}, status=400)

        try:
            song = Song.objects.get(id=song_id, room=room)
        except Song.DoesNotExist:
            return Response({'error': 'Song not found in this room'}, status=404)

        vote = Vote.objects.filter(song=song, user=user, room=room).first()
        if not vote:
            return Response({'error': 'You have not voted for this song'}, status=status.HTTP_400_BAD_REQUEST)

        vote.delete()
        vote_count = Vote.objects.filter(song=song, room=room).count()
        return Response({'message': 'Vote removed', 'vote_count': vote_count}, status=status.HTTP_200_OK)


class VoteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, song_id):
        user = request.user
        room = user.current_room
        if not room:
            return Response({'error': 'You are not in a room'}, status=400)

        try:
            song = Song.objects.get(id=song_id, room=room)
        except Song.DoesNotExist:
            return Response({'error': 'Song not found in this room'}, status=404)

        existing = Vote.objects.filter(song=song, user=user, room=room).first()
        if existing:
            existing.delete()
            action = "removed"
        else:
            try:
                with transaction.atomic():
                    Vote.objects.create(song=song, user=user, room=room)
                action = "added"
            except IntegrityError:
                return Response({"error": "You already voted"}, status=status.HTTP_400_BAD_REQUEST)

        vote_count = Vote.objects.filter(song=song, room=room).count()
        return Response({"action": action, "vote_count": vote_count}, status=status.HTTP_200_OK)
