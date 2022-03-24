from django.contrib import admin
from .models import *
from django.utils.html import mark_safe

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
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'employment_verification_status')
    list_display = ('id', 'get_name', 'get_email', 'get_status', 'employment_verification_status')
    list_filter = ('user__profile__status',)
    list_per_page = 100

    def get_name(self, obj):
        return obj.user.first_name + ' ' + obj.user.last_name

    def get_email(self, obj):
        return obj.user.email

    def get_status(self, obj):
        return obj.user.profile.status

def approve_i9(modeladmin, request, queryset):
    queryset.update(status='APPROVED')
    print(queryset[0].employee.id)
    Employee.objects.filter(pk=queryset[0].employee.id).update(employment_verification_status='APPROVED')
    approve_i9.short_description = "Approve selected i9 form"

def reject_i9(modeladmin, request, queryset):
    queryset.update(status='REJECTED')
    reject_i9.short_description = "Reject selected i9 form"

class I9Admin(admin.ModelAdmin):
    
    actions = [approve_i9, reject_i9]
    
    exclude = ('employee_signature','date_translator_signature','translator_signature','document_a', 'document_b_c', 'document_b_c2')
    list_display = (
    'id', 'employee', 'status', 'created_at')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email','created_at')

    list_filter = ('status', 'employee',)
    list_per_page = 100

    readonly_fields = ['documentA','documentB','documentC']

    def documentA(self, obj):
        document_list = []
        document_set = EmployeeDocument.objects.filter(employee__id = obj.employee.id, document_type__document_a = True)

        for doc in document_set.iterator():
            document_list.append(doc.document)
            return mark_safe('<img src="%s" width="600" height="450" />' % (document_list[0]))

    def documentB(self, obj):
        document_list = []
        document_set = EmployeeDocument.objects.filter(employee__id = obj.employee.id, document_type__document_b = True)

        for doc in document_set.iterator():
            document_list.append(doc.document)
            return mark_safe('<img src="%s" width="600" height="450" />' % (document_list[0]))

    def documentC(self, obj):
        document_list = []
        document_set = EmployeeDocument.objects.filter(employee__id = obj.employee.id, document_type__document_c = True)

        for doc in document_set.iterator():
            document_list.append(doc.document)
            return mark_safe('<img src="%s" width="600" height="450" />' % (document_list[0]))

    documentA.allow_tags = True
    documentA.short_description = 'Documents A'
    documentB.allow_tags = True
    documentB.short_description = 'Documents B'
    documentC.allow_tags = True
    documentC.short_description = 'Documents C'

def approve_w4(modeladmin, request, queryset):
    queryset.update(status='APPROVED')
    approve_w4.short_description = "Approve selected i9 form"

def reject_w4(modeladmin, request, queryset):
    queryset.update(status='REJECTED')
    reject_w4.short_description = "Reject selected i9 form"

class W4Admin(admin.ModelAdmin):
    actions = [approve_w4, reject_w4]
    exclude = ('employee_signature',)
    list_display = (
    'id', 'employee', 'status', 'created_at')
    search_fields = (
        'employee__user__first_name', 'employee__user__last_name', 'employee__user__email','created_at')
    list_filter = ('status', 'employee',)
    list_per_page = 100


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
admin.site.register(AvailabilityBlock)
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
admin.site.register(UserProfile)
admin.site.register(Payment)

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
admin.site.register(I9Form, I9Admin)

admin.site.register(W4Form, W4Admin)
admin.site.register(EmployerSubscription, EmployerSubscriptionAdmin)
# admin.site.register(EmployerSubscription)
