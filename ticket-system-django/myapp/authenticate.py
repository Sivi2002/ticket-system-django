from django.contrib.auth.backends import BaseBackend
from .models import LoginDetails  # Import your User model

class ModelBackend(BaseBackend):
    def authenticate(request, username=None, password=None):
        try:
            user = LoginDetails.objects.filter(username=username).values()[0]
            if user.get('password') == password:
                return user
            else:
                return None
        except LoginDetails.DoesNotExist:
            return None