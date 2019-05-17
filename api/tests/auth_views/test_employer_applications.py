from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

ShiftApplication = apps.get_model('api', 'ShiftApplication')


@override_settings(STATICFILES_STORAGE=None)
class ERApplicationTestCase(TestCase, WithMakeUser, WithMakeShift):
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

    def test_get_application(self):
        """
        """

        url = reverse_lazy('api:me-employer-get-applicants')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        count = ShiftApplication.objects.filter(
            shift__employer=self.test_employer).count()

        self.assertEquals(len(response_json), count)

    def test_get_application_detail(self):
        """
        """

        url = reverse_lazy('api:me-employer-get-applicants', kwargs=dict(
            application_id=self.test_application.id
        ))
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        app = ShiftApplication.objects.get(id=self.test_application.id)

        self.assertEquals(app.employee.id, response_json['employee']['id'])
        self.assertEquals(app.shift.id, response_json['shift']['id'])

    def test_get_application_detail_non_existing(self):
        """
        """

        url = reverse_lazy('api:me-employer-get-applicants', kwargs=dict(
            application_id=99999
        ))
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_delete_app_non_existing(self):
        """
        """

        url = reverse_lazy('api:me-employer-get-applicants', kwargs=dict(
            application_id=99999
        ))
        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_delete_app(self):
        """
        """

        url = reverse_lazy('api:me-employer-get-applicants', kwargs=dict(
            application_id=self.test_application.id
        ))
        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            204,
            'It should return a success response')
