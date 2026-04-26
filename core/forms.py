# from core.models import Question, Answer
from django import forms
from django.contrib.auth.models import User
from core.models import Tag


class AnswerForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class Question_Form(forms.Form):
    title = forms.CharField(max_length=200)
    text = forms.CharField(max_length=1024, widget=forms.Textarea)
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), widget=forms.CheckboxSelectMultiple)

class Search_Form(forms.Form):
    title_search = forms.CharField(max_length=200)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']
