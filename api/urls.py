from django.urls import include, path
# from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework_jwt.views import ObtainJSONWebToken
from api.serializers.auth_serializer import CustomJWTSerializer
from api.views import (
    admin_views, general_views, employer_views,
    employee_views, hooks)

app_name = "api"

urlpatterns = [

    #
    # AUTHENTICATION
    #

    path('login', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    path('user', include('django.contrib.auth.urls'), name="user-auth"),
    path('user/password/reset',general_views.PasswordView.as_view(), name="password-reset-email"),
    path('user/email/validate',general_views.ValidateEmailView.as_view(), name="validate-email"),
    path('user/<int:id>',general_views.UserView.as_view(), name="id-user"),
    path('user/register',general_views.UserRegisterView.as_view(), name="register"),
    #path('user/<int:user_id>/employees',general_views.EmployeeView.as_view(), name="create-employees"),

    #
    # FOR EVERYONE LOGGED IN (execution permissions may vary depending on your privileges)
    #

    path('employers',general_views.EmployerView.as_view(), name="get-employers"),
    path('employers/<int:id>',general_views.EmployerView.as_view(), name="id-employers"),

    path('profiles/me',general_views.ProfileMeView.as_view(), name="me-profiles"),
    path('profiles/me/image',general_views.ProfileMeImageView.as_view(), name="me-profiles-image"),

    path('jobcore-invites',general_views.JobCoreInviteView.as_view(), name="get-jcinvites"),
    path('jobcore-invites/<int:id>',general_views.JobCoreInviteView.as_view(), name="id-jcinvites"),

    path('catalog/<str:catalog_type>',general_views.CatalogView.as_view(), name="get-catalog"),

    path('ratings',general_views.RateView.as_view(), name="get-ratings"),
    path('ratings/<int:id>',general_views.RateView.as_view(), name="single-ratings"),

    path('badges',general_views.BadgeView.as_view(), name="get-badges"),
    path('badges/<int:id>',general_views.BadgeView.as_view(), name="id-badges"), #manage the badges

    #
    # UNCLASIFIED ENDPOINTS
    # @TODO: Classify endpoint permissions to employer, empoyee, admin, logged_in or public
    #

    path('employees',general_views.EmployeeView.as_view(), name="get-employees"),
    path('employees/<int:id>',general_views.EmployeeView.as_view(), name="id-employees"),


    # path('profiles',general_views.ProfileView.as_view(), name="get-profiles"),
    # path('profiles/<int:id>',general_views.ProfileView.as_view(), name="id-profiles"),
    path('payroll',general_views.PayrollShiftsView.as_view(), name="all-payroll"),
    path('employer/<int:employer_id>/payroll_projection',general_views.ProjectedPaymentsView.as_view(), name="employer-payroll-projection"),

    # path('image/<str:image_name>',general_views.ImageView.as_view())


    #
    # FOR THE EMPLOYER
    #

    path('employers/me/periods', employer_views.EmployerPayrollPeriodView.as_view(), name="employer-periods"),
    path('employers/me', employer_views.EmployerMeView.as_view(), name="employer-me"),
    path('employers/me/users',employer_views.EmployerMeUsersView.as_view(), name="get-employer-users"),
    path('employers/me/periods/<int:period_id>',employer_views.EmployerPayrollPeriodView.as_view(), name="employer-single-periods"),
    path('employers/me/jobcore-invites',general_views.JobCoreInviteView.as_view(), name="get-jcinvites"),
    path('employers/me/jobcore-invites/<int:id>',general_views.JobCoreInviteView.as_view(), name="id-jcinvites"),
    path('employers/me/applications',employer_views.ApplicantsView.as_view(), name="get-applicants"),
    path('employers/me/applications/<int:application_id>',employer_views.ApplicantsView.as_view(), name="get-applicants"),
    # path('employees/<int:id>/applications',general_views.EmployeeApplicationsView.as_view(), name="employee-applications"),
    # path('employees/<int:id>/payroll',general_views.PayrollShiftsView.as_view(), name="employee-payroll"),
    # path('clockins/',general_views.ClockinsView.as_view(), name="all-clockins"),
    # path('clockins/<int:clockin_id>',general_views.ClockinsView.as_view(), name="me-employees"),

    path('employers/me/shifts/invites',employer_views.EmployerShiftInviteView.as_view(), name="get-jobinvites"),
    path('employers/me/invites',employer_views.EmployerShiftInviteView.as_view(), name="get-jobinvites"),
    path('employers/me/shifts/invites/<int:id>',employer_views.EmployerShiftInviteView.as_view(), name="get-jobinvites"),
    path('employers/me/venues',employer_views.EmployerVenueView.as_view(), name="get-venues"),
    path('employers/me/venues/<int:id>',employer_views.EmployerVenueView.as_view(), name="id-venues"),
    path('employers/me/favlists',employer_views.FavListView.as_view(), name="get-favlists"),
    path('employers/me/favlists/<int:id>',employer_views.FavListView.as_view(), name="id-favlists"),
    path('employers/me/favlists/employee/<int:employee_id>',employer_views.FavListEmployeeView.as_view(), name="id-favlists"),
    path('employers/me/shifts/<int:id>/candidates',employer_views.EmployerShiftCandidatesView.as_view(), name="update-shift-candidates"),
    path('employers/me/shifts/<int:id>/employees',employer_views.EmployerShiftEmployeesView.as_view(), name="update-shift-employees"),
    path('employers/me/shifts',employer_views.EmployerShiftView.as_view(), name="get-shifts"),
    path('employers/me/shifts/<int:id>',employer_views.EmployerShiftView.as_view(), name="id-shifts"),

    #
    # FOR THE TALENT
    #

    path('employees/me',employee_views.EmployeeMeView.as_view(), name="me-employees"),
    #path('clockins/me',general_views.PaymentMeView.as_view(), name="me-employees"),
    path('employees/me/shifts/invites',employee_views.EmployeeShiftInviteView.as_view(), name="get-jobinvites"),
    path('employees/me/shifts/invites/<int:id>',employee_views.EmployeeShiftInviteView.as_view(), name="get-jobinvites"),
    path('employees/me/shifts',employee_views.EmployeeMeShiftView.as_view(), name="me-employees-shift"),
    #path('shifts/<int:id>',general_views.ShiftView.as_view(), name="id-shifts"),
    # path('employees/<int:id>/shifts',general_views.ShiftView.as_view(), name="employees-shifts"),
    path('employees/me/ratings/sent',employee_views.EmployeeMeSentRatingsView.as_view(), name="me-employees-ratings"),
    path('employees/me/ratings/received',employee_views.EmployeeMeReceivedRatingsView.as_view(), name="me-employees-ratings"),
    path('employees/me/devices',employee_views.EmployeeDeviceMeView.as_view(), name="me-all-device"),
    path('employees/me/devices/<str:device_id>',employee_views.EmployeeDeviceMeView.as_view(), name="me-device"),
    path('employees/me/clockins',employee_views.ClockinsMeView.as_view(), name="me-employees"),
    path('employees/me/clockins/<str:clockin_id>',employee_views.ClockinsMeView.as_view(), name="me-employees"),
    path('employees/me/applications',employee_views.EmployeeMeApplicationsView.as_view(), name="me-employee-applications"),
    path('employees/me/applications/<int:application_id>',employee_views.EmployeeMeApplicationsView.as_view(), name="me-single-application"),
    path('employees/me/availability',employee_views.EmployeeAvailabilityBlockView.as_view(), name="employee-unavailability"),
    path('employees/me/availability/<int:block_id>',employee_views.EmployeeAvailabilityBlockView.as_view(), name="employee-unavailability"),
    path('shifts/invites/<int:id>/<str:action>',employee_views.EmployeeShiftInviteView.as_view(), name="get-jobinvites"),

    # This endpoints have to be changed on the all
    path('applications/<int:application_id>',general_views.SingleApplicantView.as_view(), name="get-single-applicantion"),#this one will be replaced with employees/me/applications/id
    path('shifts/invites',employee_views.EmployeeShiftInviteView.as_view(), name="old-get-jobinvites"), #this one will be replaced with employees/me/shifts/invites
    path('shifts/invites/<int:id>',employee_views.EmployeeShiftInviteView.as_view(), name="get-emploje-jobinvites"),

    #
    # ADMIN USE ONLY
    #

    path('employees/<int:employee_id>/badges', admin_views.EmployeeBadgesView.as_view(), name="id-employees"), #update the talent badges
    path('positions',general_views.PositionView.as_view(), name="get-positions"),
    path('positions/<int:id>',general_views.PositionView.as_view(), name="id-positions"),
    path('periods', admin_views.PayrollPeriodView.as_view(), name="get-periods"),
    path('periods/<int:period_id>', admin_views.PayrollPeriodView.as_view(), name="get-periods"),
    path('email/<str:slug>', admin_views.EmailView.as_view()), # test email
    path('fmc', admin_views.FMCView.as_view()), # test mobile notification


    #
    # HOOKS
    #
    path('hook/delete_all_shifts', hooks.DeleteAllShifts.as_view()),
    path('hook/create_default_availablity_blocks', hooks.DefaultAvailabilityHook.as_view()),

    #
    # CRONJOBS
    #

    path('employer/<int:employer_id>/generate_periods', admin_views.GeneratePeriodsView.as_view(), name="employer-payment"), # every hour, will generate payment periods
]
