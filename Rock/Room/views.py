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
        user = request.user
        
        if Room.objects.filter(member = user).exists():
            return Response({'error':'user is already in these room'})
        
        try :
            Room.objects.create(host=user)
            Room.members.add(user)

            return  Response(
                {
                    "room_id": room.id,
                    "room_code": room.room_code,
                    "host": user.username
                },
                status=status.HTTP_201_CREATED
            )
        except:
            return Response({'error':'user already a host'})


class JoinRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RoomJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        room = serializer.validated_data['room']
        user = request.user

        if Room.objects.filter(members = user).exists():
            return Response({
                'error':'you already exist in room'
            },status=status.HTTP_400_BAD_REQUEST)

        room.members.add(user)

        return Response(
            {
                "room_id": room.id,
                "room_code": room.room_code
            },
            status=status.HTTP_200_OK
        )


class LeaveRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        room = Room.objects.filter(members = user).first()
        if not room:
            return Response({
                'error':'User is not in any room'
            },status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            if room.host_id == user.id:
                room.delete()
                return Response({
                    'message':'host leave the room so room closed'
                },status=status.HTTP_200_OK)
            
            room.members.remove(user)
        
        return Response({
            'message':'room leaved succesfulky'
        })
            

class DetailRoom(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        room = Room.objects.filter(members = user).first()

        if not room:
            return Response({'detail':'user not in any room'},status=status.HTTP_400_BAD_REQUEST)
        
        return Response(RoomSerializer(room).data,status=status.HTTP_200_OK)

class SongAddToQueue(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UrlExtractserializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_id = serializer.video_id
        room = request.user.current_room

        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )

        try:
            resp = requests.get(oembed_url, timeout=5)
            resp.raise_for_status()
            meta = resp.json()
        except Exception:
            return Response({"error": "Invalid YouTube video"}, status=400)

        if Song.objects.filter(
            room=room,
            video_id=video_id,
            played_at__isnull=True
        ).exists():
            return Response(
                {"error": "Song already in queue"},
                status=400
            )

        song = Song.objects.create(
            room=room,
            title=meta.get("title"),
            video_id=video_id,
            thumbnail=meta.get("thumbnail_url"),
            added_by=request.user
        )

        return Response({"id": song.id}, status=201)

class RoomSongs(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = request.user.current_room
        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        songs = (
            Song.objects
            .filter(room=room)
            .annotate(vote_count=Count('votes', filter=Q(votes__room=room)))
            .order_by("-vote_count", "created_at")
        )

        return Response([
            {
                "id": s.id,
                "title": s.title,
                "video_id": s.video_id,
                "thumbnail": s.thumbnail,
                "vote_count": s.vote_count,
                "played_at": s.played_at,
            }
            for s in songs
        ])


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


class PlayedSongView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room = request.user.current_room
        if not room:
            return Response({"error": "You are not in a room"}, status=400)

        songs = (
            Song.objects
            .filter(room=room)
            .annotate(vote_count=Count("votes"))
            .order_by("-vote_count", "created_at")
        )

        for song in songs:
            if song.was_played_within(10):
                continue

            with transaction.atomic():
                song.mark_played()
                Vote.objects.filter(song=song).delete()

            return Response({
                "id": song.id,
                "title": song.title,
                "video_id": song.video_id,
                "thumbnail": song.thumbnail,
                "added_by": song.added_by.username,
            })

        return Response(
            {"message": "No playable song (cooldown active)"},
            status=200
        )
