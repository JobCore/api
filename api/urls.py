from django.urls import include, path
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework_jwt.views import ObtainJSONWebToken
from api.serializers import CustomJWTSerializer
from api import views

app_name = "api"

urlpatterns = [
    path('jobcore-invites', views.JobCoreInviteView.as_view(), name="get-jcinvites"),
    path('jobcore-invites/<int:id>', views.JobCoreInviteView.as_view(), name="id-jcinvites"),
    path('user', include('django.contrib.auth.urls'), name="user-auth"),
    path('user/password/reset', views.PasswordView.as_view(), name="change-password"),
    path('user/email/validate', views.ValidateEmailView.as_view(), name="validate-email"),
    path('user/<int:id>', views.UserView.as_view(), name="id-user"),
    path('user/register', views.UserRegisterView.as_view(), name="register"),
    path('user/<int:user_id>/employees', views.EmployeeView.as_view(), name="create-employees"),
    path('tokenuser', views.TokenUserView.as_view(), name="token-user"),
    path('applicants', views.ApplicantsView.as_view(), name="get-applicants"),
    path('catalog/<str:catalog_type>', views.CatalogView.as_view(), name="get-catalog"),
    path('employers/users', views.EmployerUsersView.as_view(), name="get-employers"),
    path('employers', views.EmployerView.as_view(), name="get-employers"),
    path('employers/<int:id>', views.EmployerView.as_view(), name="id-employers"),
    path('employees', views.EmployeeView.as_view(), name="get-employees"),
    path('employees/<int:id>', views.EmployeeView.as_view(), name="id-employees"),
    path('employees/<int:id>/applications', views.EmployeeApplicationsView.as_view(), name="employee-applications"),
    path('employees/unavailability', views.EmployeeWeekUnavailabilityView.as_view(), name="employee-unavailability"),
    #path('employees/<int:employee_id>/unavailability', views.EmployeeWeekUnavailabilityView.as_view(), name="employee-unavailability"),
    path('employees/unavailability/<int:unavailability_id>', views.EmployeeWeekUnavailabilityView.as_view(), name="employee-unavailability"),
    path('employees/<int:id>/shifts', views.ShiftView.as_view(), name="employees-shifts"),
    path('favlists', views.FavListView.as_view(), name="get-favlists"),
    path('favlists/<int:id>', views.FavListView.as_view(), name="id-favlists"),
    path('shifts/invites', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    path('shifts/invites/<int:id>', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    path('shifts/invites/<int:id>/<str:action>', views.ShiftInviteView.as_view(), name="get-jobinvites"),
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
    path('ratings/<int:user_id>', views.RateView.as_view(), name="get-single-ratings"),
    path('login', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    # path('image/<str:image_name>', views.ImageView.as_view())
    
    # Inernal use only
    path('email/<str:slug>', views.EmailView.as_view()),
]
