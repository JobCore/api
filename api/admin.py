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

class ShiftAdmin(admin.ModelAdmin):
    # list_display = ('id',  'starting_at', 'ending_at', 'application_restriction', 'maximum_allowed_employees', 'minimum_hourly_rate', 'status')
    list_display = ('id', '_shift', '_position', 'starting_at', 'ending_at', 'application_restriction', 'maximum_allowed_employees', 'minimum_hourly_rate', 'status')
    search_fields = ('venue__title', 'position__title')
    list_filter = ('status', 'position', 'venue')
    list_per_page = 100

    def _shift(self, obj):
        return obj.venue.title

    def _position(self, obj):
        return obj.position.title

admin.site.register(Shift, ShiftAdmin)


class ShiftInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'employee', 'status')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'shift__position__title',
        'shift__venue__title')
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
    list_display = ('id', 'employee', 'started_at', 'ended_at', '_distance', 'shift', 'author')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'author__user__first_name',
        'author__user__last_name')
    list_filter = ('status',)
    list_per_page = 100

    def _distance(self, obj):
        return "In: "+str(obj.distance_in_miles)+ " Out: "+str(obj.distance_out_miles)


class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'get_name', 'status', 'created_at', 'updated_at')
    search_fields = (
        'state', 'name', 'employee__user__first_name', 'employee__user__last_name', 'employee__user__email')
    list_filter = ('status','document_type__validates_identity','document_type__validates_employment','document_type__is_form')
    list_per_page = 100

    def get_name(self, obj):
        return obj.document_type.title if obj.document_type is not None else 'Missing document type'
admin.site.register(EmployeeDocument, EmployeeDocumentAdmin)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'validates_identity', 'validates_employment', 'is_form')
admin.site.register(Document, DocumentAdmin)




admin.site.register(Clockin, ClockinAdmin)

admin.site.register(UserToken)
admin.site.register(Notification)
admin.site.register(JobCoreInvite)
admin.site.register(BankAccount)

class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'version', 'force_update', 'created_at', 'updated_at')
admin.site.register(AppVersion, AppVersionAdmin)

admin.site.register(PaymentDeduction)
