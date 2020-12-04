from django.contrib import admin
from .models import *


class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'version', 'force_update', 'created_at', 'updated_at')


class ClockinAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'employee', 'started_at', 'ended_at', '_distance', 'shift', 'author', 'latitude_in', 'longitude_in',
    'latitude_out', 'longitude_out')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'author__user__first_name',
        'author__user__last_name')
    list_filter = ('status', 'employee',)
    list_per_page = 100

    def _distance(self, obj):
        return "In: " + str(obj.distance_in_miles) + " Out: " + str(obj.distance_out_miles)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'validates_identity', 'validates_employment', 'is_form')


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


class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'get_name', 'status', 'created_at', 'updated_at')
    search_fields = (
        'state', 'name', 'employee__user__first_name', 'employee__user__last_name', 'employee__user__email')
    list_filter = (
        'status', 'document_type__validates_identity', 'document_type__validates_employment', 'document_type__is_form')
    list_per_page = 100

    def get_name(self, obj):
        return obj.document_type.title if obj.document_type is not None else 'Missing document type'


class EmployeePaymentAdmin(admin.ModelAdmin):
    list_display = ('employer', 'payroll_period', 'employee', 'paid',)
    list_filter = ('payroll_period', 'paid')
    list_per_page = 100


class ShiftAdmin(admin.ModelAdmin):
    # list_display = ('id',  'starting_at', 'ending_at', 'application_restriction', 'maximum_allowed_employees', 'minimum_hourly_rate', 'status')
    list_display = (
        'id', '_shift', '_position', 'starting_at', 'ending_at', 'application_restriction', 'maximum_allowed_employees',
        'minimum_hourly_rate', 'status')
    search_fields = ('venue__title', 'position__title')
    list_filter = ('status', 'position', 'venue')
    list_per_page = 100

    def _shift(self, obj):
        return obj.venue.title

    def _position(self, obj):
        return obj.position.title


class PreDefinedDeductionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'value',)
    ordering = ('id',)


class ShiftInviteAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'employee', 'status')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email', 'shift__position__title',
        'shift__venue__title')
    list_filter = ('status',)
    list_per_page = 100


admin.site.register(AppVersion, AppVersionAdmin)
admin.site.register(Badge)
admin.site.register(BankAccount)
admin.site.register(Clockin, ClockinAdmin)
admin.site.register(City)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeDocument, EmployeeDocumentAdmin)
admin.site.register(EmployeePayment, EmployeePaymentAdmin)
admin.site.register(Employer)
admin.site.register(FavoriteList)
admin.site.register(FCMDevice)
admin.site.register(JobCoreInvite)
admin.site.register(Notification)
admin.site.register(PaymentDeduction)
admin.site.register(PaymentTransaction)
admin.site.register(PayrollPeriod)
admin.site.register(PayrollPeriodPayment)
admin.site.register(Position)
admin.site.register(PreDefinedDeduction, PreDefinedDeductionAdmin)
admin.site.register(Profile)
admin.site.register(Rate)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(ShiftInvite, ShiftInviteAdmin)
admin.site.register(UserToken)
admin.site.register(Venue)


class EmployerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', '_employer', '_subscription', 'status', 'due_at', 'payment_mode')
    search_fields = ('employer__title', 'subscription__title')
    list_filter = ('status', 'subscription__unique_name')
    list_per_page = 100

    def _employer(self, obj):
        return obj.employer.title

    def _subscription(self, obj):
        return obj.subscription.title


admin.site.register(SubscriptionPlan)
admin.site.register(EmployerUsers)
admin.site.register(Payrates)
admin.site.register(I9Form)
admin.site.register(EmployerSubscription, EmployerSubscriptionAdmin)
# admin.site.register(EmployerSubscription)
