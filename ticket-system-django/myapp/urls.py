from django.contrib import admin
from django.urls import path, re_path

from . import view

urlpatterns = [
    path('ticket', view.ticket ,name = 'ticket'),
    # re_path('load_edit_form/<pk>/', view.edit_view, name='load_edit_form')
]