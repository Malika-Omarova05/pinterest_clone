from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import home, profile, upload_pin, upload_board, login_view, register

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/<str:username>/', profile, name='user_profile'),
    path('upload_pin/', upload_pin, name='upload_pin'),
    path('upload_board/', upload_board, name='upload_board'),
]