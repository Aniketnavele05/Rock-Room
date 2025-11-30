from django.shortcuts import render, redirect, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User, Room
from .serializer import RegistrationSerializer, RoomCreateSerializer, RoomJoinSerializer, RoomLeaveSerializer, RoomSerializer
# Create your views here.
def index(request):
    return render(request,'Auth.html')

def home(request):
    return render(request,'home.html')

def room(request):
    return render(request,'room.html')

class Registration(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect('/')
        return Response(serializer.errors, status=400)
    
class CreateRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = RoomCreateSerializer(data={},context={'request':request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()

        request.user.current_room = room
        request.user.save()

        return Response(RoomCreateSerializer(room).data,status=202)

class JoinRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = RoomJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['room_code']
        room = Room.objects.get(room_code = code)

        request.user.current_room = room
        request.user.save()

        return Response(RoomJoinSerializer(room).data)
    
class LeaveRoom(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = RoomLeaveSerializer(data={},context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'left the room'})

class DetailRoom(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        room = request.user.current_room
        if not room:
            return Response({'detail':'no room'})
        return Response(RoomSerializer(room).data)