from django.shortcuts import render

def general_context():
    context = {
        "menu": [
            ["Задать вопрос", "/create_question"],
        ]
    }
    return context

# Create your views here.
def main(request):
    return render(request, 'index.html', general_context())

def calculator(request):
    return render(request, 'calc.html', general_context())
