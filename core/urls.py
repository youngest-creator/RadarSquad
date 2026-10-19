from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_select, name='game_select'),
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('game/<str:game_slug>/', views.dashboard, name='dashboard'),
    path(
        'game/<str:game_slug>/create-post/',
        views.create_party_post,
        name='create_party_post',
    ),
    path(
        'join-room/<int:room_id>/', views.join_party_room, name='join_party_room'
    ),
    path('vote/<int:target_user_id>/', views.vote_reputation, name='vote_reputation'),
    path('save-settings/', views.save_user_settings, name='save_user_settings'),
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
    path('staff-panel/', views.admin_dashboard, name='admin_dashboard'),
    path(
        'staff-panel/delete/<str:item_type>/<int:item_id>/',
        views.admin_action,
        name='admin_action',
    ),
]