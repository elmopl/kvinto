from ..models import Account
from django.shortcuts import render

def main(request):
    context = {}
    return render(request, 'dashboard.html', context)
