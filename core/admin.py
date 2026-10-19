from django.contrib import admin
from .models import Message, PartyPost, PlayerCard, ReputationVote, SquadRoom, UserProfile

admin.site.site_header = 'Панель управления RadarSquad'
admin.site.site_title = 'RadarSquad Admin'
admin.site.index_title = 'Управление игроками, карточками, объявлениями и чатами'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'reputation',
        'discord_tag',
        'steam_url',
        'telegram_chat_id',
    )
    search_fields = ('user__username', 'discord_tag', 'steam_url')
    list_editable = ('reputation',)


@admin.register(PlayerCard)
class PlayerCardAdmin(admin.ModelAdmin):
    list_display = (
        'nickname',
        'game',
        'rating',
        'role',
        'has_mic',
        'hours_played',
        'user',
    )
    list_filter = ('game', 'has_mic', 'language')
    search_fields = ('nickname', 'role', 'rating', 'description')
    list_editable = ('rating', 'role', 'has_mic')


@admin.register(SquadRoom)
class SquadRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'creator', 'max_players', 'created_at')
    list_filter = ('game', 'created_at')
    search_fields = ('name', 'creator__username')


@admin.register(PartyPost)
class PartyPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'game', 'author', 'needed_roles', 'created_at')
    list_filter = ('game', 'created_at')
    search_fields = ('title', 'author__username', 'needed_roles')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'short_text', 'created_at')
    list_filter = ('created_at', 'room__game')
    search_fields = ('sender__username', 'text', 'room__name')

    def short_text(self, obj):
        return obj.text[:50] + ('...' if len(obj.text) > 50 else '')

    short_text.short_description = 'Текст сообщения'


admin.site.register(ReputationVote)