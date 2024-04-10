from django.db import models

class Ticket(models.Model):
    subject = models.CharField(max_length=255, null=False, blank=False, default=None)
    discription = models.CharField(max_length=2000, null=False, blank=False, default=None)
    ticket_type = models.CharField(max_length=255, null=False, blank=False, default=None)
    comment = models.CharField(max_length=255, null=False, blank=False, default=None)
    active = models.BooleanField(default=True)
    file = models.FileField(upload_to='public/')

class Employee(models.Model):
    empcode = models.CharField(max_length=255, null=False, blank=False, default=None)
    fullname = models.CharField(max_length=255, null=False, blank=False, default=None)
    designation = models.CharField(max_length=500, null=False, blank=False, default=None)

class LoginDetails(models.Model):
    username = models.CharField(max_length=255, null=False, blank=False, default=None)
    password = models.CharField(max_length=255, null=False, blank=False, default=None)
    active = models.BooleanField(default=True)