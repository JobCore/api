from rest_framework.views import APIView
from api.models import Profile
from rest_framework.exceptions import PermissionDenied


class HaveProfileMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        try:
            request.user.profile
        except Profile.DoesNotExist:
            raise PermissionDenied("You don't have a profile")


class IsEmployeeMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if request.user.profile.employee_id is None:
            raise PermissionDenied("You don't seem to be a talent")

        self.employee = self.request.user.profile.employee
        self.user = self.request.user


class IsEmployerMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if request.user.profile.employer_id is None:
            raise PermissionDenied("You don't seem to be an employer")

        self.employer = self.request.user.profile.employer
        self.user = self.request.user


class WithProfileView(HaveProfileMixin, APIView):
    pass


class EmployeeView(IsEmployeeMixin, WithProfileView):
    pass


class EmployerView(IsEmployerMixin, WithProfileView):
    pass
