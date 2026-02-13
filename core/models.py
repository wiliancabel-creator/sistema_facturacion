# core/models.py - VERSIÓN CORREGIDA
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group


# 1. Usuario personalizad
class Usuario(AbstractUser):
    def get_roles():
        return [(g.name.lower(), g.name) for g in Group.objects.all()]

    
    def __str__(self):
        return self.username

   
 
 


