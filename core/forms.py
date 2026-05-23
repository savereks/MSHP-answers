from django import forms
from django.contrib.auth.models import User
from core.models import ProfileImage
from core.constants import ALL_TAGS


class AnswerForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class CommentForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Напишите комментарий...',
            'class': 'comment-textarea'
        }),
        label=''
    )


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Дополнительная валидация
        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError('Неверное имя пользователя или пароль')
        return cleaned_data


class Question_Form(forms.Form):
    title = forms.CharField(max_length=200, label='Заголовок')
    text = forms.CharField(max_length=1024, widget=forms.Textarea, label='Текст вопроса')
    tags = forms.MultipleChoiceField(
        choices=[(tag['id'], tag['name']) for tag in ALL_TAGS],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Теги'
    )


class Search_Form(forms.Form):
    title_search = forms.CharField(max_length=200)


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = ProfileImage
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'avatar': forms.FileInput(attrs={
                'accept': 'image/*'
            })
        }
        labels = {
            'avatar': 'Загрузить новую аватарку',
            'bio': 'О себе'
        }
        help_texts = {
            'avatar': 'Поддерживаемые форматы: JPG, PNG, GIF. Максимальный размер: 5MB',
            'bio': 'Максимум 500 символов'
        }