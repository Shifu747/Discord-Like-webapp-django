from email import message
from http.client import HTTPResponse
from multiprocessing import context
import re
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import HttpResponse
from .models import Message, Room, Topic, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# Create your views here.

def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect("home")
    if request.method == 'POST':

        username = request.POST.get('username')
        print(username)#.lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "User don't exist")
        
        user = authenticate(request,username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request, "username or password doesn't match")
        
    context = {
        'page' : page
    }
    return render(request,'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')

# def registerUser(request):
#     page = 'register'
#     form = UserCreationForm()

#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.username = user.username.lower()
#             user.save()
#             login(request,user)
#             return redirect('home')
#         else:
#             messages.error(request, 'An error Occured')

#     return render(request, 'base/login_register.html',{'form':form})

def registerUser(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})

#for home page
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q)
                                )
    # rooms = Room.objects.all()
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    
    context = {
        'rooms' : rooms,
        'topics' : topics,
        'room_count' : room_count,
        'room_messages' : room_messages
    }
    return render(request,  'base/home.html', context)


def room(request, id):
    room = Room.objects.get(id=id)
    roomMessages = room.message_set.all()
    participants = room.participants.all()
    
    
    if request.method == "POST":
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', id=room.id)
   
    context = {
        'room' : room,
        'roomMessages' : roomMessages,
        'participants' : participants
    }
    return render(request, 'base/room.html',context)

def userProfile(request,id):
    user = User.objects.get(id=id)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {
        'user' : user,
        'rooms' : rooms,
        'topics' : topics,
        'room_messages' : room_messages
            }
    return render(request, 'base/profile.html', context)


@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        topic_name =request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),

        )
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')
    context = {
        'form' : form,
        'topics' : topics
    }
    return render(request, 'base/room_form.html', context)

@login_required(login_url='/login')
def updateRoom(request, id):
    room = Room.objects.get(id=id)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host :
        return HttpResponse("you're not allowed")

    if request.method == "POST":
        topic_name =request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        form = RoomForm(request.POST, instance=room)
        room.name=request.POST.get('name')
        room.topic=topic
        room.description=request.POST.get('description')
        room.save()
        # if form.is_valid():
        #     form.save()
        return redirect('home')

    context = {
        'form'      : form,
        'topics'    : topics,
        'room'      : room 
    }
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def deleteRoom(request, id):
    room = Room.objects.get(id=id)

    if request.user != room.host :
        return HttpResponse("you're not allowed")


    if request.method == "POST":
        room.delete()
        return redirect('home')
    context = {
        'obj' : room
    }
    return render(request,'base/delete.html', context)


@login_required(login_url='/login')
def deleteMessage(request, id):
    message = Message.objects.get(id=id)

    if request.user != message.user :
        return HttpResponse("you're not allowed")


    if request.method == "POST":
        message.delete()
        return redirect('home')

    context = {
        'obj' : message
    }
    return render(request,'base/delete.html', context)

@login_required(login_url='/login')
def updateUser(request):
    form = UserForm(instance=request.user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',id=request.user.id)
    return render(request, 'base/update-user.html',{'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)

    return render(request, 'base/topics.html', {"topics" : topics})

def activityPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    room_messages = Message.objects.all()
    # filter(Q(room__topic__name__icontains=q))

    return render (request, 'base/activity.html', {'room_messages':room_messages})