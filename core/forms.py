from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Pin, Board, Profile

# Новая форма регистрации
class RegisterForm(UserCreationForm):
    display_name = forms.CharField(
        max_length=100,
        label="Ник (отображаемое имя)",
        help_text="Как вас будут видеть другие (можно на русском, с эмодзи)"
    )
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']  # Только поля User!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем display_name в форму (оно не в Meta)
        self.fields['username'].label = "Логин (имя пользователя)"
        self.fields['username'].help_text = "Только латиница, цифры и символы _ . @ + -"

        # Упрощаем правила пароля
        self.fields['password1'].help_text = "Придумайте любой пароль"
        self.fields['password1'].validators = []
        self.fields['password2'].help_text = "Повторите пароль"

        # Переставляем порядок полей для красоты
        self.order_fields(['username', 'display_name', 'email', 'password1', 'password2'])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Создаём/обновляем профиль с ником
            Profile.objects.update_or_create(
                user=user,
                defaults={'display_name': self.cleaned_data['display_name']}
            )
        return user

# Верни старые формы — они нужны для загрузки пинов и досок
class PinForm(forms.ModelForm):
    class Meta:
        model = Pin
        fields = ['title', 'description', 'image', 'video', 'tags']
        widgets = {
            'tags': forms.TextInput(attrs={'placeholder': 'Введите теги через запятую, например: осень, природа'}),
        }


class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['title', 'pins']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'bio', 'avatar']  # Добавил display_name для редактирования