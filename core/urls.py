from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_select, name='game_select'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('game/<str:game_slug>/', views.dashboard, name='dashboard'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path(
        'invite/<int:target_user_id>/<str:game_slug>/',
        views.invite_player,
        name='invite_player',
    ),
    path('rooms/', views.my_rooms, name='my_rooms'),
    path('rooms/<int:room_id>/', views.room_chat, name='room_chat'),
    path(
        'api/rooms/<int:room_id>/messages/',
        views.api_room_messages,
        name='api_room_messages',
    ),
]