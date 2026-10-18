from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True, verbose_name='Аватарка'
    )
    steam_url = models.URLField(
        max_length=255, blank=True, verbose_name='Ссылка на Steam'
    )
    discord_tag = models.CharField(
        max_length=100, blank=True, verbose_name='Discord (ник или ссылка)'
    )

    def __str__(self):
        return self.user.username


class PlayerCard(models.Model):
    GAME_CHOICES = [
        ('cs2', 'Counter-Strike 2'),
        ('pubg', 'PUBG: Battlegrounds'),
        ('dota2', 'Dota 2'),
        ('brawlstars', 'Brawl Stars'),
        ('standoff2', 'Standoff 2'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='cards'
    )
    game = models.CharField(
        max_length=20, choices=GAME_CHOICES, verbose_name='Игра'
    )
    nickname = models.CharField(max_length=100, verbose_name='Ник в игре')
    rating = models.CharField(max_length=100, verbose_name='Рейтинг / Очки')
    role = models.CharField(max_length=100, verbose_name='Роль / Позиция')
    language = models.CharField(
        max_length=50, default='Русский', verbose_name='Язык общения'
    )
    has_mic = models.BooleanField(default=True, verbose_name='Есть микрофон')
    hours_played = models.PositiveIntegerField(
        default=0, verbose_name='Часов в игре'
    )
    description = models.TextField(
        blank=True, verbose_name='О себе / Кого ищу в пати'
    )

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f'{self.nickname} ({self.get_game_display()})'


class SquadRoom(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название комнаты')
    game = models.CharField(
        max_length=20, choices=PlayerCard.GAME_CHOICES, verbose_name='Игра'
    )
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_rooms'
    )
    members = models.ManyToManyField(User, related_name='squad_rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.get_game_display()})'


class Message(models.Model):
    room = models.ForeignKey(
        SquadRoom, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']