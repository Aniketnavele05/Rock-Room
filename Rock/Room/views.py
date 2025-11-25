from django.shortcuts import render, redirect, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializer import RegistrationSerializer
# Create your views here.
def index(request):
    return render(request,'index.html')

class Registration(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect('/')
        return Response(serializer.errors, status=400)