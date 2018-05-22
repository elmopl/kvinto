from django.contrib import admin
from .models import Person
from .models import Account

# Register your models here.

admin.site.register(Person)
admin.site.register(Account)
