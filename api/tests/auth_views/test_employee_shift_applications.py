from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

ShiftApplication = apps.get_model('api', 'ShiftApplication')


@override_settings(STATICFILES_STORAGE=None)
class EEShiftApplicationTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for login
    """

    def setUp(self):
        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        (
            self.test_user_employer,
            self.test_employer,
            self.test_profile_employer
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer@testdoma.in',
                is_active=True,
            )
        )

        starting_at = timezone.now() + timedelta(days=1)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at),
            employer=self.test_employer)

        self.test_application = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift,
            employee=self.test_employee
        )

    def test_list_applications(self):
        """
        """

        url = reverse_lazy('api:me-employee-applications')
        self.client.force_login(self.test_user_employee)

        all_shifts = []
        starting_at = self.test_shift.starting_at
        for i in range(0, 5):
            starting_at = starting_at + timedelta(days=1)
            shift, _, __ = self._make_shift(
                shiftkwargs=dict(status='OPEN', starting_at=starting_at),
                employer=self.test_employer)
            all_shifts.append(shift)

        for shift in all_shifts:
            self.test_application = mixer.blend(
                'api.ShiftApplication',
                shift=shift,
                employee=self.test_employee
            )

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')
        response_json = response.json()

        print([str(appli['shift']['starting_at']) for appli in response_json])

        count = ShiftApplication.objects.filter(
            employee_id=self.test_employee.id).count()

        self.assertEquals(len(response_json), count)

        first = response_json[0]
        last = response_json[-1]

        # applications should be sorted by date decreasing
        self.assertLessEqual(last['shift']['starting_at'], first['shift']['starting_at'])

    def test_detail_application(self):
        """
        """

        url = reverse_lazy('api:me-employees-single-application', kwargs=dict(
            application_id=self.test_application.id,
            ))
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        test_app = ShiftApplication.objects.get(id=self.test_application.id)

        self.assertEquals(response_json['id'], test_app.id)
        self.assertEquals(response_json['shift']['id'], test_app.shift_id)

    def test_list_applications_unauth(self):
        """
        """

        url = reverse_lazy('api:me-employee-applications')

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_list_applications_as_employer(self):
        """
        """

        url = reverse_lazy('api:me-employee-applications')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            403,
            'It should return an error response')

    def test_detail_app_not_mine(self):
        """
        """

        __, other_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            )
        )

        other_shift, _, __ = self._make_shift(
            shiftkwargs=dict(
                status='OPEN',
                starting_at=self.test_shift.starting_at),
            employer=self.test_employer)

        other_app = mixer.blend(
            'api.ShiftApplication',
            shift=other_shift,
            employee=other_employee,
        )

        url = reverse_lazy('api:me-employees-single-application', kwargs=dict(
            application_id=other_app.id,
            ))
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')
