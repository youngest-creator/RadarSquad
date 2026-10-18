from django.contrib import admin
from .models import Message, PlayerCard, SquadRoom, UserProfile

admin.site.register(UserProfile)
admin.site.register(PlayerCard)
admin.site.register(SquadRoom)
admin.site.register(Message)