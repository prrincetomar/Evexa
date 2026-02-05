from django.urls import path
from .views import profile, register
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('register/', register),
]