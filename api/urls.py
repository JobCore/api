from django.urls import include, path
from django.contrib.auth.views import PasswordResetConfirmView
from rest_framework_jwt.views import ObtainJSONWebToken
from api.serializers import CustomJWTSerializer
from api import views

app_name = "api"

urlpatterns = [
    path('password_reset',
         views.UserEmailView.as_view(),
         name="password-reset-email"),
    #path('login/', views.UserLoginView.as_view(), name="login"),
    path('jobcore-invites', views.JobCoreInviteView.as_view(), name="get-jcinvites"),
    path('jobcore-invites/<int:id>', views.JobCoreInviteView.as_view(), name="id-jcinvites"),
    path('shiftinvites', views.ShiftInviteView.as_view(), name="get-jobinvites"),
    path('user', include('django.contrib.auth.urls'), name="user-auth"),
    path('user/<int:id>', views.UserView.as_view(), name="id-user"),
    path('tokenuser', views.TokenUserView.as_view(), name="token-user"),
    path('register', views.UserRegisterView.as_view(), name="register"),
    path('applicants', views.ApplicantsView.as_view(), name="get-applicants"),
    path('employers', views.EmployerView.as_view(), name="get-employers"),
    path('employers/<int:id>', views.EmployerView.as_view(), name="id-employers"),
    path('employees', views.EmployeeView.as_view(), name="get-employees"),
    path('employees/<int:id>', views.EmployeeView.as_view(), name="id-employees"),
    path('favlists', views.FavListView.as_view(), name="get-favlists"),
    path('favlists/<int:id>', views.FavListView.as_view(), name="id-favlists"),
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
    path('login', ObtainJSONWebToken.as_view(serializer_class=CustomJWTSerializer)),
    path('email/<str:slug>', views.EmailView.as_view()),
    # path('image/<str:image_name>', views.ImageView.as_view())
]
