from django import forms


class Question_Form(forms.Form):
    title = forms.CharField(max_length=200)
    text = forms.CharField(max_length=1024)
class Search_Form(forms.Form):
    title_search = forms.CharField(max_length=200)
