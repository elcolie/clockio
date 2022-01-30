import datetime

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Memory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    clock_in = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.clock_in.isoformat()}"

    @property
    def current_clock(self):
        return datetime.datetime.now().isoformat()


class MemoryClockOut(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    clock_out = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.clock_out.isoformat()}"
