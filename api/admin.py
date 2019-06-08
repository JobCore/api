from django.contrib import admin
from django.contrib.auth import User
from .models import *

# Register your models here.
admin.site.register(Employer)
admin.site.register(User)
admin.site.register(Employee)
admin.site.register(Shift)
admin.site.register(Profile)
admin.site.register(Badge)
admin.site.register(Position)
admin.site.register(Venue)
admin.site.register(FavoriteList)
admin.site.register(FCMDevice)
admin.site.register(Rate)
admin.site.register(PayrollPeriodPayment)
admin.site.register(PayrollPeriod)
admin.site.register(Clockin)
