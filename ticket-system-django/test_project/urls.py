"""
URL configuration for test_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

from myapp.view import edit_view
from test_project import view

urlpatterns = [
    path('', view.index,name = 'index'),
    path('new', view.index_new,name = 'index_new'),
    path('api/load_edit_form/<pk>/', edit_view, name='load_edit_form'),
    re_path(r'^api/', include('myapp.urls')),
    path('admin/', admin.site.urls),
    path('userdata', view.userdata),
    path('login', view.login_view, name='login'),
    path('updatedelete', view.updateDelete),
    path('ticket_list', view.ticket_list, name='ticket_list')
]
