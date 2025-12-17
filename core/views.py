from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
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
    if username:
        viewed_user = get_object_or_404(User, username=username)
    else:
        viewed_user = request.user

    profile = get_object_or_404(Profile, user=viewed_user)

    if request.method == 'POST' and viewed_user == request.user:
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

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
            pin.save()
            form.save_m2m()
            return redirect('home')
    else:
        form = PinForm()
    return render(request, 'core/upload_pin.html', {'form': form})


# В views.py для upload_board передайте user в форму
@login_required
def upload_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST, user=request.user)  # Передаём user
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            form.save_m2m()
            if board.pins.count() < 2:
                board.delete()
                form.add_error('pins', 'Выберите минимум 2 пина.')
            else:
                return redirect('home')
    else:
        form = BoardForm(user=request.user)  # Передаём user
    return render(request, 'core/upload_board.html', {'form': form})