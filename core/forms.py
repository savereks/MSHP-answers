from core.models import Question, Answer
from django import forms

class AnswerForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea)

class Question_Form(forms.Form):
    title = forms.CharField(max_length=200)
    text = forms.CharField(max_length=1024)
class Search_Form(forms.Form):
    title_search = forms.CharField(max_length=200)
