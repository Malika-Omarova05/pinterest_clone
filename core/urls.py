from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import home, profile, upload_pin, edit_pin, upload_board, login_view, register, upload_avatar, add_to_board, remove_from_board, delete_pin, board_detail, delete_board

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/upload_avatar/', upload_avatar, name='upload_avatar'),
    path('profile/', profile, name='profile'),
    path('profile/<str:username>/', profile, name='user_profile'),
    path('upload_pin/', upload_pin, name='upload_pin'),
    path('upload_board/', upload_board, name='upload_board'),
    path('add_to_board/<int:pin_id>/', add_to_board, name='add_to_board'),
    path('remove_from_board/<int:board_id>/<int:pin_id>/', remove_from_board, name='remove_from_board'),
    path('delete_pin/<int:pin_id>/', delete_pin, name='delete_pin'),
    path('board/<int:board_id>/', board_detail, name='board_detail'),
    path('board/<int:board_id>/delete/', delete_board, name='delete_board'),
    path('pin/<int:pin_id>/edit/', edit_pin, name='edit_pin'),
]