import urllib.parse
import urllib.request
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Message, PartyPost, PlayerCard, ReputationVote, SquadRoom, UserProfile

# Настройки Telegram-бота (ссылка на бота в приложении + токен для уведомлений)
TELEGRAM_BOT_USERNAME = (
    'RadarSquadNotifyBot'  # Замени на юзернейм своего бота из @BotFather
)
TELEGRAM_BOT_URL = f'https://t.me/{TELEGRAM_BOT_USERNAME}'
TELEGRAM_BOT_TOKEN = ''  # Сюда можно вставить токен от @BotFather


def send_telegram_alert(user, text):
    """Отправляет уведомление игроку в Telegram, если он указал свой Chat ID в настройках"""
    profile = getattr(user, 'profile', None)
    if not profile or not profile.telegram_chat_id or not TELEGRAM_BOT_TOKEN:
        return
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = urllib.parse.urlencode(
            {'chat_id': profile.telegram_chat_id, 'text': text}
        ).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass


# Дисциплины без стикеров, со строгими киберспортивными тегами и лимитом команды
GAMES_INFO = {
    'cs2': {
        'slug': 'cs2',
        'name': 'Counter-Strike 2',
        'tag': '5V5 TACTICAL SHOOTER',
        'max_players': 5,
        'rating_label': 'Premier / Faceit Elo / Звание',
        'role_placeholder': 'Снайпер (AWP), Рифлер, Люркер, Капитан (IGL)',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/730/library_hero.jpg',
        'accent': '#de9b35',
    },
    'pubg': {
        'slug': 'pubg',
        'name': 'PUBG: Battlegrounds',
        'tag': 'SQUAD BATTLE ROYALE (4 MAX)',
        'max_players': 4,
        'rating_label': 'Ранг (Бронза — Выживший) / ADR',
        'role_placeholder': 'Снайпер, Штурмовик, Разведчик, Саппорт',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/578080/library_hero.jpg',
        'accent': '#f2a900',
    },
    'dota2': {
        'slug': 'dota2',
        'name': 'Dota 2',
        'tag': '5V5 MOBA STRATEGY',
        'max_players': 5,
        'rating_label': 'MMR / Ранг (Рекрут — Титан)',
        'role_placeholder': 'Керри (Pos 1), Мидер (Pos 2), Хард (3), Саппорт (4/5)',
        'is_steam': True,
        'banner': 'https://cdn.cloudflare.steamstatic.com/steam/apps/570/library_hero.jpg',
        'accent': '#e3392b',
    },
    'brawlstars': {
        'slug': 'brawlstars',
        'name': 'Brawl Stars',
        'tag': '3V3 MOBILE ARENA',
        'max_players': 3,
        'rating_label': 'Количество кубков (Трофеи) / Ранг',
        'role_placeholder': 'Танк, Убийца, Стрелок, Поддержка, Контроль',
        'is_steam': False,
        'banner': (
            'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=1400&q=80'
        ),
        'accent': '#ffbe0b',
    },
    'standoff2': {
        'slug': 'standoff2',
        'name': 'Standoff 2',
        'tag': '5V5 COMPETITIVE ACTION',
        'max_players': 5,
        'rating_label': 'MMR / Звание (Bronze — The Legend)',
        'role_placeholder': 'Авапер, Энтри-фрагер, Люркер, Саппорт',
        'is_steam': False,
        'banner': (
            'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1400&q=80'
        ),
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

    return render(request, 'core/auth.html', {'bot_url': TELEGRAM_BOT_URL})


def logout_view(request):
    logout(request)
    return redirect('auth')


@login_required(login_url='auth')
def game_select(request):
    UserProfile.objects.get_or_create(user=request.user)
    return render(
        request,
        'core/games.html',
        {'games': GAMES_INFO, 'bot_url': TELEGRAM_BOT_URL},
    )


@login_required(login_url='auth')
def dashboard(request, game_slug):
    if game_slug not in GAMES_INFO:
        return redirect('game_select')

    UserProfile.objects.get_or_create(user=request.user)
    game_data = GAMES_INFO[game_slug]
    cards = PlayerCard.objects.filter(game=game_slug).select_related(
        'user', 'user__profile'
    )

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

    # Все комнаты пользователя в этой игре, где еще есть свободные места
    my_rooms = SquadRoom.objects.filter(
        members=request.user, game=game_slug
    ).distinct()
    party_posts = (
        PartyPost.objects.filter(game=game_slug)
        .select_related('author', 'room', 'author__profile')
        .all()[:12]
    )

    return render(
        request,
        'core/dashboard.html',
        {
            'game': game_data,
            'cards': cards,
            'my_rooms': my_rooms,
            'party_posts': party_posts,
            'search_q': search_q,
            'mic_only': mic_only,
            'bot_url': TELEGRAM_BOT_URL,
        },
    )


@login_required(login_url='auth')
def create_party_post(request, game_slug):
    """Создает объявление 'Ищу 2-3 игроков в команду' и открытую комнату под эту игру"""
    if game_slug not in GAMES_INFO:
        return redirect('game_select')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        needed_roles = request.POST.get('needed_roles', '').strip()
        max_p = GAMES_INFO[game_slug]['max_players']

        if title:
            room_name = f"[{GAMES_INFO[game_slug]['name']}] {title}"
            room = SquadRoom.objects.create(
                name=room_name,
                game=game_slug,
                creator=request.user,
                max_players=max_p,
            )
            room.members.add(request.user)

            PartyPost.objects.create(
                author=request.user,
                game=game_slug,
                room=room,
                title=title,
                needed_roles=needed_roles or 'Любая роль / Адекватность',
            )
            Message.objects.create(
                room=room,
                sender=request.user,
                text=(
                    f'Создал сбор команды: «{title}». Ждем игроков (макс.'
                    f' {max_p} чел.)!'
                ),
            )
            messages.success(
                request,
                'Объявление опубликовано! Игроки теперь могут нажать «Вступить в команду».',
            )

    return redirect('dashboard', game_slug=game_slug)


@login_required(login_url='auth')
def join_party_room(request, room_id):
    """Кнопка 'Вступить в команду' под объявлением"""
    room = get_object_or_404(SquadRoom, id=room_id)
    max_limit = GAMES_INFO.get(room.game, {}).get(
        'max_players', room.max_players
    )

    if request.user in room.members.all():
        return redirect('room_chat', room_id=room.id)

    if room.members.count() >= max_limit:
        messages.error(
            request,
            f'В этой команде уже максимум игроков ({max_limit}/{max_limit})!',
        )
        return redirect('dashboard', game_slug=room.game)

    room.members.add(request.user)
    Message.objects.create(
        room=room,
        sender=request.user,
        text=(
            f'Игрок {request.user.username} вступил в команду по объявлению!'
            f' ({room.members.count()}/{max_limit})'
        ),
    )
    send_telegram_alert(
        room.creator,
        f'RadarSquad: Игрок {request.user.username} вступил в твою команду «{room.name}»!',
    )
    messages.success(request, f'Ты успешно вступил в команду «{room.name}»!')
    return redirect('room_chat', room_id=room.id)


@login_required(login_url='auth')
def invite_player(request, target_user_id, game_slug):
    """Приглашение игрока в команду с поддержкой до 3, 4 или 5 человек в зависимости от игры"""
    target_user = get_object_or_404(User, id=target_user_id)
    if target_user == request.user:
        messages.warning(request, 'Нельзя пригласить самого себя!')
        return redirect('dashboard', game_slug=game_slug)

    max_limit = GAMES_INFO.get(game_slug, {}).get('max_players', 5)
    room_id = request.POST.get('room_id')

    if room_id:
        room = get_object_or_404(SquadRoom, id=room_id, members=request.user)
    else:
        # Ищем последнюю комнату пользователя по этой игре, где еще есть свободные места
        user_rooms = SquadRoom.objects.filter(
            game=game_slug, members=request.user
        ).order_by('-created_at')
        room = None
        for r in user_rooms:
            if r.members.count() < max_limit:
                room = r
                break

        # Если свободной комнаты нет — создаем новый сквад с лимитом игры
        if not room:
            game_name = GAMES_INFO.get(game_slug, {}).get('name', game_slug)
            room = SquadRoom.objects.create(
                name=f'Сквад {game_name} (Лидер: {request.user.username})',
                game=game_slug,
                creator=request.user,
                max_players=max_limit,
            )
            room.members.add(request.user)

    if target_user in room.members.all():
        messages.info(
            request, f'Игрок {target_user.username} уже состоит в этой команде!'
        )
        return redirect('room_chat', room_id=room.id)

    if room.members.count() >= max_limit:
        messages.error(
            request,
            f'Команда «{room.name}» уже заполнена ({max_limit}/{max_limit} чел.)! Выбери «Создать новый сквад».',
        )
        return redirect('dashboard', game_slug=game_slug)

    room.members.add(target_user)
    Message.objects.create(
        room=room,
        sender=request.user,
        text=(
            f'Пригласил игрока {target_user.username} в команду! Состав:'
            f' {room.members.count()}/{max_limit}.'
        ),
    )
    send_telegram_alert(
        target_user,
        f'RadarSquad: Игрок {request.user.username} пригласил тебя в команду «{room.name}»!',
    )
    messages.success(
        request,
        f'Игрок {target_user.username} добавлен в команду ({room.members.count()}/{max_limit})!',
    )
    return redirect('room_chat', room_id=room.id)


@login_required(login_url='auth')
def vote_reputation(request, target_user_id):
    """Система репутации: +1 (Лайк) или -1 (Дизлайк)"""
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=target_user_id)
        if target_user == request.user:
            messages.warning(request, 'Нельзя менять репутацию самому себе!')
            return redirect(request.META.get('HTTP_REFERER', 'game_select'))

        vote_type = request.POST.get('vote')  # 'up' или 'down'
        is_pos = vote_type == 'up'

        target_profile, _ = UserProfile.objects.get_or_create(user=target_user)
        existing_vote = ReputationVote.objects.filter(
            from_user=request.user, to_user=target_user
        ).first()

        if existing_vote:
            if existing_vote.is_positive != is_pos:
                existing_vote.is_positive = is_pos
                existing_vote.save()
                target_profile.reputation += 2 if is_pos else -2
                target_profile.save()
                messages.success(
                    request, f'Отзыв об игроке {target_user.username} обновлен!'
                )
            else:
                messages.info(
                    request, 'Ты уже оценивал этого игрока таким образом.'
                )
        else:
            ReputationVote.objects.create(
                from_user=request.user, to_user=target_user, is_positive=is_pos
            )
            target_profile.reputation += 1 if is_pos else -1
            target_profile.save()
            messages.success(
                request, f'Репутация игрока {target_user.username} изменена!'
            )

    return redirect(request.META.get('HTTP_REFERER', 'game_select'))


@login_required(login_url='auth')
def save_user_settings(request):
    """Сохранение Telegram Chat ID из модального окна настроек"""
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.telegram_chat_id = request.POST.get(
            'telegram_chat_id', ''
        ).strip()
        profile.save()
        messages.success(
            request, 'Настройки и привязка Telegram успешно сохранены!'
        )
    return redirect(request.META.get('HTTP_REFERER', 'game_select'))


@login_required(login_url='auth')
def cabinet(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            profile.steam_url = request.POST.get('steam_url', '').strip()
            profile.discord_tag = request.POST.get('discord_tag', '').strip()
            profile.telegram_chat_id = request.POST.get(
                'telegram_chat_id', ''
            ).strip()
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
            'bot_url': TELEGRAM_BOT_URL,
        },
    )


@login_required(login_url='auth')
def my_rooms(request):
    rooms = (
        SquadRoom.objects.filter(members=request.user)
        .distinct()
        .order_by('-created_at')
    )
    return render(
        request,
        'core/rooms.html',
        {'rooms': rooms, 'bot_url': TELEGRAM_BOT_URL},
    )


@login_required(login_url='auth')
def room_chat(request, room_id):
    room = get_object_or_404(SquadRoom, id=room_id)
    if request.user not in room.members.all():
        messages.error(request, 'Вы не состоите в этой команде!')
        return redirect('my_rooms')

    max_limit = GAMES_INFO.get(room.game, {}).get(
        'max_players', room.max_players
    )

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
            'max_limit': max_limit,
            'chat_messages': room.messages.select_related('sender').all(),
            'members': room.members.select_related('profile').all(),
            'bot_url': TELEGRAM_BOT_URL,
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


@login_required(login_url='auth')
def admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Доступ разрешен только администраторам!')
        return redirect('game_select')

    stats = {
        'total_users': User.objects.count(),
        'total_cards': PlayerCard.objects.count(),
        'total_rooms': SquadRoom.objects.count(),
        'total_messages': Message.objects.count(),
        'by_game': {
            info['name']: PlayerCard.objects.filter(game=slug).count()
            for slug, info in GAMES_INFO.items()
        },
    }

    recent_cards = PlayerCard.objects.select_related('user').order_by('-id')[
        :25
    ]
    recent_rooms = SquadRoom.objects.select_related('creator').order_by(
        '-created_at'
    )[:15]
    recent_messages = Message.objects.select_related('sender', 'room').order_by(
        '-created_at'
    )[:20]

    return render(
        request,
        'core/admin_panel.html',
        {
            'stats': stats,
            'recent_cards': recent_cards,
            'recent_rooms': recent_rooms,
            'recent_messages': recent_messages,
            'bot_url': TELEGRAM_BOT_URL,
        },
    )


@login_required(login_url='auth')
def admin_action(request, item_type, item_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('game_select')

    if request.method == 'POST':
        if item_type == 'card':
            PlayerCard.objects.filter(id=item_id).delete()
            messages.success(request, 'Карточка игрока удалена!')
        elif item_type == 'room':
            SquadRoom.objects.filter(id=item_id).delete()
            messages.success(request, 'Комната и её чат удалены!')
        elif item_type == 'message':
            Message.objects.filter(id=item_id).delete()
            messages.success(request, 'Сообщение удалено!')

    return redirect('admin_dashboard')