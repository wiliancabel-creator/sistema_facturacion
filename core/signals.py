# core/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario

@receiver(post_save, sender=Usuario)
def notificar_nuevo_usuario(sender, instance, created, **kwargs):
    if created:
        # tu lógica aquí
        print(f"Se creó un nuevo usuario: {instance.username}")
