from django.contrib import admin
from .models import Person
from .models import Account

# Register your models here.

class AccountAdmin(admin.ModelAdmin):
    list_display = ('owner', 'name')
    list_filter = ('owner',)
    ordering = ('owner__name',)

admin.site.register(Person)
admin.site.register(Account, AccountAdmin)
