from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.contrib import messages
from .models import Pin, Board, Profile, ForbiddenTag, User
from .forms import PinForm, BoardForm, ProfileForm, RegisterForm  # Импорты форм
from .models import SearchHistory


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


@login_required
def home(request):
    query = request.GET.get('q')

    # Сохраняем поиск в историю, если есть query
    if query:
        SearchHistory.objects.create(user=request.user, query=query)

    # Стандартный поиск (если есть query)
    pins = Pin.objects.exclude(user=request.user)
    boards = Board.objects.exclude(user=request.user)
    users = User.objects.exclude(pk=request.user.pk)

    if query:
        users = users.filter(username__icontains=query)
        pins = pins.filter(
            Q(tags__name__icontains=query) | Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()
        boards = boards.filter(title__icontains=query).distinct()
    else:
        # Рекомендации без query: все пины/доски, кроме своих
        pins = pins.all()
        boards = boards.all()

    # Собираем интересы из истории поиска
    history = SearchHistory.objects.filter(user=request.user).order_by('-timestamp')[:20]  # Последние 20 запросов
    interest_tags = set()
    interest_users = set()

    for hist in history:
        q = hist.query.strip().lower()
        if q.startswith('#'):  # Если как тег
            interest_tags.add(q[1:])  # Добавляем без #
        else:
            # Проверяем, если query — логин пользователя
            matching_users = User.objects.filter(username__icontains=q)
            for u in matching_users:
                interest_users.add(u.id)

    # Сортировка пинов: сначала релевантные (по тегам или от интересных пользователей), потом остальные
    if not query:  # Только для рекомендаций (без активного поиска)
        relevant_pins = pins.filter(
            Q(tags__name__in=interest_tags) | Q(user__id__in=interest_users)
        ).distinct()

        other_pins = pins.exclude(pk__in=relevant_pins.values_list('pk', flat=True))

        pins = list(relevant_pins) + list(other_pins)  # Сверху релевантные

    # Аналогично для досок (если нужно, можно добавить похожую сортировку)

    context = {
        'pins': pins,
        'boards': boards,
        'users': users,
        'query': query,
    }
    return render(request, 'core/home.html', context)
@login_required
def profile(request, username=None):
    # 1. Находим пользователя
    if username:
        viewed_user = get_object_or_404(User, username=username)
    else:
        viewed_user = request.user

    # 2. Получаем профиль (используем get_or_create, чтобы избежать 404, если профиль не создался при регистрации)
    profile_obj, created = Profile.objects.get_or_create(user=viewed_user)
    is_own_profile = (viewed_user == request.user)

    # 3. Обработка сохранения формы (только для владельца)
    form = None
    if is_own_profile:
        if request.method == 'POST':
            # ВАЖНО: передаем request.FILES для обработки изображений!
            form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
            if form.is_valid():
                form.save()
                return redirect('profile') # Перезагрузка, чтобы увидеть изменения
        else:
            form = ProfileForm(instance=profile_obj)

    # 4. Данные для отображения
    user_pins = Pin.objects.filter(user=viewed_user)
    user_boards = Board.objects.filter(user=viewed_user)

    context = {
        'form': form,
        'profile_user': viewed_user,
        'profile': profile_obj,
        'pins': user_pins,
        'boards': user_boards,
        'is_own_profile': is_own_profile,
    }
    return render(request, 'core/profile.html', context)


@login_required
def upload_pin(request):
    if request.method == 'POST':
        form = PinForm(request.POST, request.FILES)
        if form.is_valid():
            pin = form.save(commit=False)
            pin.user = request.user
            pin.save()
            form.save_m2m()
            return redirect('profile')
    else:
        form = PinForm()
    return render(request, 'core/upload_pin.html', {'form': form})


# В views.py для upload_board передайте user в форму
@login_required
def upload_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST, user=request.user)
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            form.save_m2m()  # Сохраняем связи Many-to-Many (выбранные пины)
            return redirect('profile')  # Переходим в профиль, чтобы увидеть новую доску
        else:
            # Если форма невалидна, вы увидите ошибки в терминале PyCharm
            print("Ошибки формы:", form.errors)
    else:
        form = BoardForm(user=request.user)

    return render(request, 'core/upload_board.html', {'form': form})

def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile_obj, created = Profile.objects.get_or_create(user=request.user)
        profile_obj.avatar = request.FILES['avatar']
        profile_obj.save()
    return redirect('profile')


# 1. Обновленный upload_board (убрано ограничение в 2 пина)
@login_required
def upload_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST, user=request.user)
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            form.save_m2m()
            return redirect('profile')
    else:
        form = BoardForm(user=request.user)
    return render(request, 'core/upload_board.html', {'form': form})


# 2. Добавление пина в доску (для главной страницы)
@login_required
def add_to_board(request, pin_id):
    if request.method == 'POST':
        board_id = request.POST.get('board_id')
        pin = get_object_or_404(Pin, id=pin_id)
        board = get_object_or_404(Board, id=board_id, user=request.user)

        if pin in board.pins.all():
            messages.warning(request, "Этот пин уже есть в данной доске.")
        else:
            board.pins.add(pin)
            messages.success(request, f"Пин добавлен в доску '{board.title}'.")

    return redirect('home')


# 3. Удаление пина из доски
@login_required
def remove_from_board(request, board_id, pin_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    pin = get_object_or_404(Pin, id=pin_id)
    board.pins.remove(pin)
    return redirect('profile')


# 4. Полное удаление пина (только владельцем)
@login_required
def delete_pin(request, pin_id):
    pin = get_object_or_404(Pin, id=pin_id, user=request.user)
    pin.delete()
    return redirect('profile')

@login_required
def board_detail(request, board_id):
    # Получаем доску. Если доска чужая — смотреть можно, если приватная (по желанию) — можно ограничить
    board = get_object_or_404(Board, id=board_id)
    return render(request, 'core/board_detail.html', {
        'board': board,
        'is_own_board': board.user == request.user
    })

@login_required
def delete_board(request, board_id):
    # Удалять может только владелец
    board = get_object_or_404(Board, id=board_id, user=request.user)
    board.delete()
    messages.success(request, "Доска успешно удалена.")
    return redirect('profile')


@login_required
def edit_pin(request, pin_id):
    # Находим пин, проверяя, что он принадлежит текущему пользователю
    pin = get_object_or_404(Pin, id=pin_id, user=request.user)

    if request.method == 'POST':
        # Передаем request.FILES, чтобы можно было загрузить новое фото
        form = PinForm(request.POST, request.FILES, instance=pin)
        if form.is_valid():
            form.save()
            messages.success(request, "Пин успешно обновлен!")
            return redirect('profile')
    else:
        form = PinForm(instance=pin)

    return render(request, 'core/edit_pin.html', {'form': form, 'pin': pin})