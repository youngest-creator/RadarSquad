from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Message, PlayerCard, SquadRoom, UserProfile

# Настройки и оформление под каждую игру
GAMES_INFO = {
    'cs2': {
        'slug': 'cs2',
        'name': 'Counter-Strike 2',
        'rating_label': 'Premier / Faceit Elo / Звание',
        'role_placeholder': 'Снайпер (AWP), Рифлер, Люркер, Капитан (IGL)',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/730/library_hero.jpg',
        'icon': '🔫',
        'accent': '#de9b35',
    },
    'pubg': {
        'slug': 'pubg',
        'name': 'PUBG: Battlegrounds',
        'rating_label': 'Ранг (Бронза — Выживший) / ADR',
        'role_placeholder': 'Снайпер, Штурмовик, Разведчик, Саппорт',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/578080/library_hero.jpg',
        'icon': '🪂',
        'accent': '#f2a900',
    },
    'dota2': {
        'slug': 'dota2',
        'name': 'Dota 2',
        'rating_label': 'MMR / Ранг (Рекрут — Титан)',
        'role_placeholder': 'Керри (Pos 1), Мидер (Pos 2), Хард (3), Саппорт (4/5)',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/570/library_hero.jpg',
        'icon': '⚔️',
        'accent': '#e3392b',
    },
    'brawlstars': {
        'slug': 'brawlstars',
        'name': 'Brawl Stars',
        'rating_label': 'Количество кубков (Трофеи) / Ранг',
        'role_placeholder': 'Танк, Убийца, Стрелок, Поддержка, Контроль',
        'is_steam': False,
        'banner': (
            'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=1400&q=80'
        ),
        'icon': '⭐',
        'accent': '#ffbe0b',
    },
    'standoff2': {
        'slug': 'standoff2',
        'name': 'Standoff 2',
        'rating_label': 'MMR / Звание (Bronze — The Legend)',
        'role_placeholder': 'Авапер, Энтри-фрагер, Люркер, Саппорт',
        'is_steam': False,
        'banner': (
            'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1400&q=80'
        ),
        'icon': '🔪',
        'accent': '#3a86ff',
    },
}


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('game_select')

    if request.method == 'POST':
        action = request.POST.get('action')
        u_name = request.POST.get('username', '').strip()
        p_word = request.POST.get('password', '').strip()

        if action == 'login':
            user = authenticate(request, username=u_name, password=p_word)
            if user:
                login(request, user)
                return redirect('game_select')
            else:
                messages.error(request, 'Неверный логин или пароль!')

        elif action == 'register':
            if not u_name or not p_word:
                messages.error(request, 'Заполните все поля!')
            elif User.objects.filter(username=u_name).exists():
                messages.error(request, 'Такой ник уже занят!')
            else:
                user = User.objects.create_user(
                    username=u_name, password=p_word
                )
                UserProfile.objects.create(user=user)
                login(request, user)
                messages.success(
                    request,
                    'Добро пожаловать в RadarSquad! Заполни карточку игрока в Личном кабинете.',
                )
                return redirect('cabinet')

    return render(request, 'core/auth.html')


def logout_view(request):
    logout(request)
    return redirect('auth')


@login_required(login_url='auth')
def game_select(request):
    return render(request, 'core/games.html', {'games': GAMES_INFO})


@login_required(login_url='auth')
def dashboard(request, game_slug):
    if game_slug not in GAMES_INFO:
        return redirect('game_select')

    game_data = GAMES_INFO[game_slug]
    cards = PlayerCard.objects.filter(game=game_slug).select_related(
        'user', 'user__profile'
    )

    # Поиск и фильтр по микрофону
    mic_only = request.GET.get('mic')
    search_q = request.GET.get('q', '').strip()
    if mic_only == '1':
        cards = cards.filter(has_mic=True)
    if search_q:
        cards = (
            cards.filter(role__icontains=search_q)
            | cards.filter(rating__icontains=search_q)
            | cards.filter(nickname__icontains=search_q)
        )

    my_rooms = SquadRoom.objects.filter(
        members=request.user, game=game_slug
    ).distinct()

    return render(
        request,
        'core/dashboard.html',
        {
            'game': game_data,
            'cards': cards,
            'my_rooms': my_rooms,
            'search_q': search_q,
            'mic_only': mic_only,
        },
    )


@login_required(login_url='auth')
def cabinet(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile.steam_url = request.POST.get('steam_url', '').strip()
            profile.discord_tag = request.POST.get('discord_tag', '').strip()
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
            messages.success(
                request, 'Общие данные профиля и аватарка сохранены!'
            )

        elif form_type == 'card':
            game_slug = request.POST.get('game')
            if game_slug in GAMES_INFO:
                PlayerCard.objects.update_or_create(
                    user=request.user,
                    game=game_slug,
                    defaults={
                        'nickname': request.POST.get(
                            'nickname', request.user.username
                        ),
                        'rating': request.POST.get('rating', 'Без рейтинга'),
                        'role': request.POST.get('role', 'Универсал'),
                        'language': request.POST.get('language', 'Русский'),
                        'has_mic': request.POST.get('has_mic') == 'on',
                        'hours_played': int(
                            request.POST.get('hours_played') or 0
                        ),
                        'description': request.POST.get('description', ''),
                    },
                )
                messages.success(
                    request,
                    f"Анкета для {GAMES_INFO[game_slug]['name']} опубликована!",
                )
        return redirect('cabinet')

    user_cards = {c.game: c for c in PlayerCard.objects.filter(user=request.user)}
    return render(
        request,
        'core/cabinet.html',
        {
            'profile': profile,
            'games': GAMES_INFO,
            'user_cards': user_cards,
        },
    )


@login_required(login_url='auth')
def invite_player(request, target_user_id, game_slug):
    target_user = get_object_or_404(User, id=target_user_id)
    if target_user == request.user:
        messages.warning(request, 'Нельзя пригласить самого себя!')
        return redirect('dashboard', game_slug=game_slug)

    room_id = request.POST.get('room_id')
    if room_id:
        room = get_object_or_404(SquadRoom, id=room_id, members=request.user)
        room.members.add(target_user)
        Message.objects.create(
            room=room,
            sender=request.user,
            text=f'⚡ Пригласил игрока {target_user.username} в команду!',
        )
        messages.success(
            request,
            f'Игрок {target_user.username} добавлен в комнату «{room.name}»!',
        )
        return redirect('room_chat', room_id=room.id)
    else:
        # Проверяем, есть ли уже комната между этими игроками по этой игре
        existing_rooms = SquadRoom.objects.filter(
            game=game_slug, members=request.user
        ).filter(members=target_user)
        if existing_rooms.exists():
            return redirect('room_chat', room_id=existing_rooms.first().id)

        game_name = GAMES_INFO.get(game_slug, {}).get('name', game_slug)
        room_name = (
            f'Сквад {game_name}: {request.user.username} +'
            f' {target_user.username}'
        )
        room = SquadRoom.objects.create(
            name=room_name, game=game_slug, creator=request.user
        )
        room.members.add(request.user, target_user)
        Message.objects.create(
            room=room,
            sender=request.user,
            text=(
                f'👋 Привет, {target_user.username}! Комната создана, го'
                ' обсудим игру!'
            ),
        )
        return redirect('room_chat', room_id=room.id)


@login_required(login_url='auth')
def my_rooms(request):
    rooms = (
        SquadRoom.objects.filter(members=request.user)
        .distinct()
        .order_by('-created_at')
    )
    return render(request, 'core/rooms.html', {'rooms': rooms})


@login_required(login_url='auth')
def room_chat(request, room_id):
    room = get_object_or_404(SquadRoom, id=room_id)
    if request.user not in room.members.all():
        messages.error(request, 'Вы не состоите в этой команде!')
        return redirect('my_rooms')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(room=room, sender=request.user, text=text)
        return redirect('room_chat', room_id=room.id)

    return render(
        request,
        'core/chat.html',
        {
            'room': room,
            'chat_messages': room.messages.select_related('sender').all(),
            'members': room.members.select_related('profile').all(),
        },
    )


@login_required(login_url='auth')
def api_room_messages(request, room_id):
    room = get_object_or_404(SquadRoom, id=room_id)
    if request.user not in room.members.all():
        return JsonResponse({'error': 'Forbidden'}, status=403)
    msgs = [
        {
            'id': m.id,
            'sender': m.sender.username,
            'is_me': m.sender == request.user,
            'text': m.text,
            'time': m.created_at.strftime('%H:%M'),
        }
        for m in room.messages.select_related('sender').all()
    ]
    return JsonResponse({'messages': msgs})