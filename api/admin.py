from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Employer)
admin.site.register(Employee)
admin.site.register(Shift)

class ShiftInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'employee', 'status')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'shift__position__title', 'shift__venue__title')
    list_filter = ('status',)
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


class ClockinAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'started_at', 'ended_at', 'shift')
    list_per_page = 100
admin.site.register(Clockin, ClockinAdmin)

admin.site.register(UserToken)
admin.site.register(Notification)
admin.site.register(JobCoreInvite)
admin.site.register(BankAccount)
admin.site.register(Document)
admin.site.register(PaymentDeduction)
