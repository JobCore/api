from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Employer)
admin.site.register(Employee)
admin.site.register(Shift)

class ShiftInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'employee', 'status')
    list_per_page = 100
admin.site.register(ShiftInvite, ShiftInviteAdmin)
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
admin.site.register(UserToken)
admin.site.register(Notification)
admin.site.register(JobCoreInvite)
