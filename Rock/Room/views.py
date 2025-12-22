import requests
from django.db import transaction, IntegrityError
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Room, Song, RoomSong, Vote
from .serializer import (
    RegistrationSerializer,
    RoomJoinSerializer,
    RoomSerializer,
    UrlExtractSerializer,
    RoomSongSerializer
)

from django.shortcuts import render


def index(request):
    return render(request, "Auth.html")


def home(request):
    return render(request, "home.html")


def room(request):
    return render(request, "room.html")

class Registration(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered"}, status=201)

class CreateRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if Room.objects.filter(members=user).exists():
            return Response({"error": "User already in a room"}, status=400)

        try:
            with transaction.atomic():
                room = Room.objects.create(host=user)
                room.members.add(user)
        except IntegrityError:
            return Response({"error": "User already hosts a room"}, status=400)

        return Response(RoomSerializer(room, context={"request": request}).data, status=201)

class JoinRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RoomJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = serializer.validated_data["room"]
        user = request.user

        if Room.objects.filter(members=user).exists():
            return Response({"error": "Already in another room"}, status=400)

        room.members.add(user)
        return Response(RoomSerializer(room, context={"request": request}).data)


class LeaveRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        room = Room.objects.filter(members=user).first()

        if not room:
            return Response({"error": "Not in any room"}, status=400)

        with transaction.atomic():
            if room.host == user:
                room.delete()
                return Response({"message": "Room closed (host left)"})

            room.members.remove(user)

        return Response({"message": "Left room"})

class DetailRoom(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = Room.objects.filter(members=request.user).first()
        if not room:
            return Response({"error": "Not in a room"}, status=400)

        return Response(RoomSerializer(room, context={"request": request}).data)


class SongAdd(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UrlExtractSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video_id = serializer.video_id

        room = Room.objects.filter(members=request.user).first()
        if not room:
            return Response({"error": "Not in a room"}, status=400)

    
        try:
            resp = requests.get(
                f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
                timeout=5
            )
            resp.raise_for_status()
            meta = resp.json()
        except Exception:
            return Response({"error": "Invalid YouTube video"}, status=400)

        song, _ = Song.objects.get_or_create(
            video_id=video_id,
            defaults={
                "title": meta["title"],
                "thumbnail": meta["thumbnail_url"]
            }
        )

        room_song = RoomSong.objects.filter(room=room, song=song).first()

        
        if room_song and room_song.played_at is None:
            Vote.objects.get_or_create(room_song=room_song, user=request.user)
            return Response({"message": "Vote registered"}, status=200)

        
        if room_song and not room_song.can_play_again(minutes=10):
            return Response({"error": "Song cooldown active (10 min)"}, status=400)

        
        new_song = RoomSong.objects.create(
            room=room,
            song=song,
            added_by=request.user
        )

        return Response(RoomSongSerializer(new_song).data, status=201)

class RoomSongs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = Room.objects.filter(members=request.user).first()
        if not room:
            return Response({"error": "Not in room"}, status=400)

        qs = (
            RoomSong.objects
            .filter(room=room, played_at__isnull=True)
            .annotate(
                vote_count=Count("votes"),
                has_voted=Exists(
                    Vote.objects.filter(
                        room_song=OuterRef("pk"),
                        user=request.user
                    )
                )
            )
            .order_by("-vote_count", "created_at")
        )

        return Response(RoomSongSerializer(qs, many=True).data)

class VoteToggle(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_song_id):
        room_song = RoomSong.objects.get(id=room_song_id)

        if request.user not in room_song.room.members.all():
            return Response({"error": "Forbidden"}, status=403)

        vote = Vote.objects.filter(room_song=room_song, user=request.user).first()

        if vote:
            vote.delete()
            action = "removed"
        else:
            Vote.objects.create(room_song=room_song, user=request.user)
            action = "added"

        return Response({
            "action": action,
            "vote_count": room_song.votes.count()
        })

class PlayNextSong(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            room = Room.objects.get(host=request.user)
        except Room.DoesNotExist:
            return Response(
                {"detail": "Only host can play next"},
                status=status.HTTP_403_FORBIDDEN
            )

        candidates = (
            RoomSong.objects
            .filter(room=room)
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "created_at")
        )

        next_song = None
        for rs in candidates:
            if rs.can_play_again(10):
                next_song = rs
                break

        if not next_song:
            return Response(
                {"detail": "No playable songs"},
                status=status.HTTP_400_BAD_REQUEST
            )

        next_song.mark_played()

        return Response({
            "room_song_id": next_song.id,
            "video_id": next_song.song.video_id,
            "title": next_song.song.title,
        })
    

class NowPlaying(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            room = Room.objects.get(members=request.user)
        except Room.DoesNotExist:
            return Response(
                {"detail": "User not in a room"},
                status=status.HTTP_400_BAD_REQUEST
            )

        room_song = (
            RoomSong.objects
            .filter(room=room, played_at__isnull=False)
            .select_related("song")
            .order_by("-played_at")
            .first()
        )

        if not room_song:
            return Response(
                {"video_id": None},
                status=status.HTTP_200_OK
            )

        return Response({
            "room_song_id": room_song.id,
            "video_id": room_song.song.video_id,
            "title": room_song.song.title,
            "played_at": room_song.played_at,
        })