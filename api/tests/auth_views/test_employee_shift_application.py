from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.utils import timezone
from datetime import timedelta


@override_settings(STATICFILES_STORAGE=None)
class ShiftApplicationsTestSuite(TestCase, WithMakeUser, WithMakeShift):
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

        self.test_invite = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
            status='PENDING'
        )

        mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
            status='APPLIED'
        )

    def test_list_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employee-applications')
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 2)

    def test_filter_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites')
        self.client.force_login(self.test_user_employee)

        querystring = {
            'status': 'PENDING'
        }

        response = self.client.get(
            url,
            data=querystring,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 1)
