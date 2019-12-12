from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Employer)

class EmployeeAdmin(admin.ModelAdmin):
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    list_display = ('id', 'get_name', 'get_email', 'get_status')
    list_filter = ('user__profile__status',)
    list_per_page = 100
    def get_name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name
    def get_email(self, obj):
        return obj.user.email
    def get_status(self, obj):
        return obj.user.profile.status
admin.site.register(Employee, EmployeeAdmin)

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
admin.site.register(City)


class ClockinAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'started_at', 'ended_at', 'shift', 'author')
    search_fields = ('employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'author__user__first_name', 'author__user__last_name')
    list_filter = ('status',)
    list_per_page = 100
admin.site.register(Clockin, ClockinAdmin)

admin.site.register(UserToken)
admin.site.register(Notification)
admin.site.register(JobCoreInvite)
admin.site.register(BankAccount)
#admin.site.register(Document)
admin.site.register(PaymentDeduction)
# admin.site.register(City)
