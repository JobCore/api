from django.urls import include, path
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework_jwt.views import ObtainJSONWebToken
from api.serializers.auth_serializer import CustomJWTSerializer
from api import views
from api import hooks

app_name = "api"

urlpatterns = [
    
    #
    # AUTHENTICATION
    #
    
    path('login', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    path('user', include('django.contrib.auth.urls'), name="user-auth"),
    path('user/password/reset', views.PasswordView.as_view(), name="password-reset-email"),
    path('user/email/validate', views.ValidateEmailView.as_view(), name="validate-email"),
    path('user/<int:id>', views.UserView.as_view(), name="id-user"),
    path('user/register', views.UserRegisterView.as_view(), name="register"),
    path('user/<int:user_id>/employees', views.EmployeeView.as_view(), name="create-employees"),
    
    #
    # FOR THE EMPLOYER
    #
    
    path('jobcore-invites', views.JobCoreInviteView.as_view(), name="get-jcinvites"),
    path('jobcore-invites/<int:id>', views.JobCoreInviteView.as_view(), name="id-jcinvites"),
    path('applications', views.ApplicantsView.as_view(), name="get-applicants"),
    path('applications/<int:application_id>', views.ApplicantsView.as_view(), name="get-applicants"),
    path('catalog/<str:catalog_type>', views.CatalogView.as_view(), name="get-catalog"),
    path('employers/users', views.EmployerUsersView.as_view(), name="get-employers"),
    path('employers', views.EmployerView.as_view(), name="get-employers"),
    path('employers/<int:id>', views.EmployerView.as_view(), name="id-employers"),
    path('employees', views.EmployeeView.as_view(), name="get-employees"),
    path('employees/<int:id>', views.EmployeeView.as_view(), name="id-employees"),
    path('employees/<int:id>/applications', views.EmployeeApplicationsView.as_view(), name="employee-applications"),
    path('employees/<int:id>/payroll', views.PayrollView.as_view(), name="employee-payroll"),
    path('employees/<int:employee_id>/availability', views.AvailabilityBlockView.as_view(), name="employee-unavailability"),
    path('employees/availability/<int:availability_id>', views.AvailabilityBlockView.as_view(), name="id-availability"),
    path('employees/<int:id>/shifts', views.ShiftView.as_view(), name="employees-shifts"),
    path('favlists', views.FavListView.as_view(), name="get-favlists"),
    path('favlists/<int:id>', views.FavListView.as_view(), name="id-favlists"),
    path('favlists/employee/<int:employee_id>', views.FavListEmployeeView.as_view(), name="id-favlists"),
    
    path('shifts/invites', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    path('shifts/invites/<int:id>', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    path('shifts/<int:id>/candidates', views.ShiftCandidatesView.as_view(), name="update-shift-candidates"),
    path('shifts/<int:id>/employees', views.ShiftCandidatesView.as_view(), name="update-shift-employees"),
    path('shifts', views.ShiftView.as_view(), name="get-shifts"),
    path('shifts/<int:id>', views.ShiftView.as_view(), name="id-shifts"),
    
    path('badges', views.BadgeView.as_view(), name="get-badges"),
    path('badges/<int:id>', views.BadgeView.as_view(), name="id-badges"),
    path('profiles', views.ProfileView.as_view(), name="get-profiles"),
    path('profiles/<int:id>', views.ProfileView.as_view(), name="id-profiles"),
    path('venues', views.VenueView.as_view(), name="get-venues"),
    path('venues/<int:id>', views.VenueView.as_view(), name="id-venues"),
    path('positions', views.PositionView.as_view(), name="get-positions"),
    path('positions/<int:id>', views.PositionView.as_view(), name="id-positions"),
    
    path('ratings', views.RateView.as_view(), name="get-ratings"),
    path('ratings/<int:id>', views.RateView.as_view(), name="single-ratings"),
    
    path('clockins/', views.ClockinsView.as_view(), name="all-clockins"),
    path('clockins/<int:clockin_id>', views.ClockinsView.as_view(), name="me-employees"),
    path('payroll', views.PayrollView.as_view(), name="all-payroll"),
    # path('image/<str:image_name>', views.ImageView.as_view())
    
    #
    # FOR THE TALENT
    #
    
    path('profiles/me', views.ProfileMeView.as_view(), name="me-profiles"),
    path('employees/me', views.EmployeeMeView.as_view(), name="me-employees"),
    #path('clockins/me', views.PaymentMeView.as_view(), name="me-employees"),
    path('employees/me/shifts', views.EmployeeMeShiftView.as_view(), name="me-employees-shift"),
    path('employees/me/ratings', views.EmployeeMeRatingsView.as_view(), name="me-employees-ratings"),
    path('employees/me/devices', views.DeviceMeView.as_view(), name="me-all-device"),
    path('employees/me/devices/<str:device_id>', views.DeviceMeView.as_view(), name="me-device"),
    path('employees/me/shifts/invites', views.ShiftMeInviteView.as_view(), name="me-jobinvites"),
    path('employees/me/clockins', views.ClockinsMeView.as_view(), name="me-employees"),
    path('employees/me/clockins/<str:clockin_id>', views.ClockinsMeView.as_view(), name="me-employees"),
    path('employees/me/applications', views.EmployeeMeApplicationsView.as_view(), name="me-employee-applications"),
    path('employees/me/availability', views.AvailabilityBlockView.as_view(), name="employee-unavailability"),
    path('employees/me/availability/<int:block_id>', views.AvailabilityBlockView.as_view(), name="employee-unavailability"),
    path('shifts/invites/<int:id>/<str:action>', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    #path('employees/me/profiles', views.ProfileView.as_view(), name="get-profiles"),
    
    #
    # INTERNAL USE ONLY
    #
    
    path('email/<str:slug>', views.EmailView.as_view()),
    path('fmc', views.FMCView.as_view()),
    # hooks
    path('hook/delete_all_shifts', hooks.DeleteAllShifts.as_view()),
    path('hook/create_default_availablity_blocks', hooks.DefaultAvailabilityHook.as_view()),
]
