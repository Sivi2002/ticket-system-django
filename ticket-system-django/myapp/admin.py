from django.contrib import admin
from .models import LoginDetails, Ticket
 
# Register your models here.
admin.site.register(Ticket)
admin.site.register(LoginDetails)