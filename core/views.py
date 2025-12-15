from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Q
from .models import Pin, Board, Profile, ForbiddenTag
from .forms import PinForm, BoardForm, ProfileForm
from .forms import RegisterForm  # Добавь импорт
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User, Pin, Board

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автовход
            return redirect('home')
        else:
            # Добавим отладку: посмотри, какие ошибки
            print(form.errors)  # Временно! Посмотри в консоли сервера
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
    query = request.GET.get('q')  # Получаем поисковый запрос из URL
    pins = []
    boards = []
    users = []

    if query:
        # Поиск пользователей по username
        users = User.objects.filter(username__icontains=query).exclude(pk=request.user.pk)

        # Поиск пинов по теме (тегам, названию, описанию)
        pins = Pin.objects.filter(
            Q(tags__name__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).exclude(user=request.user).distinct()

        # Поиск досок по названию
        boards = Board.objects.filter(title__icontains=query).distinct()
    else:
        # Стандартные рекомендации (по тегам, как раньше)
        user_tags = set()
        user_pins = Pin.objects.filter(user=request.user)
        for pin in user_pins:
            user_tags.update(pin.tags.names())

        pins = Pin.objects.filter(tags__name__in=user_tags).exclude(user=request.user).distinct()
        boards = Board.objects.filter(pins__tags__name__in=user_tags).distinct()

    context = {
        'pins': pins,
        'boards': boards,
        'users': users,  # Для отображения найденных пользователей
        'query': query,
    }
    return render(request, 'core/home.html', context)


@login_required
def profile(request, username=None):
    if username:
        # Просмотр чужого профиля
        viewed_user = get_object_or_404(User, username=username)
    else:
        # Свой профиль
        viewed_user = request.user

    profile = get_object_or_404(Profile, user=viewed_user)

    if request.method == 'POST' and viewed_user == request.user:
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    # "Рекомендации" — это пины и доски этого пользователя
    user_pins = Pin.objects.filter(user=viewed_user)
    user_boards = Board.objects.filter(user=viewed_user)

    context = {
        'form': form if viewed_user == request.user else None,
        'profile_user': viewed_user,
        'pins': user_pins,
        'boards': user_boards,
        'is_own_profile': viewed_user == request.user,
    }
    return render(request, 'core/profile.html', context)
@login_required
def upload_pin(request):
    if request.method == 'POST':
        form = PinForm(request.POST, request.FILES)
        if form.is_valid():
            pin = form.save(commit=False)
            pin.user = request.user
            try:
                pin.full_clean()  # Проверяем обычные поля
                pin.save()        # Сначала сохраняем объект
                form.save_m2m()   # Теперь безопасно сохраняем теги
                return redirect('home')
            except ValidationError as e:
                # Если сработала проверка запрещённых тегов
                form.add_error('tags', e)
    else:
        form = PinForm()
    return render(request, 'core/upload_pin.html', {'form': form})

@login_required
def upload_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            form.save_m2m()  # Для пинов
            return redirect('home')
    else:
        form = BoardForm()
    return render(request, 'core/upload_board.html', {'form': form})