from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.utils import timezone
from datetime import timedelta


@override_settings(STATICFILES_STORAGE=None)
class EmployeeShiftInviteTestSuite(TestCase, WithMakeUser, WithMakeShift):
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

        url = reverse_lazy('api:me-employees-get-jobinvites')
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

    def test_invalid_filter_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites')
        self.client.force_login(self.test_user_employee)

        querystring = {
            'status': ':evil_type:'
        }

        response = self.client.get(
            url,
            data=querystring,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error')

    def test_invalid_id_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(id=999999))
        self.client.force_login(self.test_user_employee)

        response = self.client.get(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error')

    def test_invalid_put_id_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id)
        )
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error')

    def test_invalid_action_put_id_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action=":evil")
        )
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error')

    def test_invalid_id_put_id_shift_invites(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=999999,
            action="APPLY")
        )
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error')

    def test_put_shift_invite(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action="APPLY")
        )
        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_put_shift_invite_with_favorite(self):
        """
        """

        mixer.blend(
            'api.FavoriteList',
            employer=self.test_employer,
            auto_accept_employees_on_this_list=True,
            employees=[self.test_employee]
        )

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action="APPLY"
        )
        )

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_put_double_apply_favourite(self):
        """
        """
        mixer.blend(
            'api.FavoriteList',
            employer=self.test_employer,
            auto_accept_employees_on_this_list=True,
            employees=[self.test_employee]
        )
        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action="APPLY"
        )
        )

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_put_double_apply_regular(self):
        """
        """
        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action="APPLY"
        )
        )

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_put_shift_invite_as_employer(self):
        """
        """

        url = reverse_lazy('api:me-employees-get-jobinvites', kwargs=dict(
            id=self.test_invite.id,
            action="APPLY")
        )
        self.client.force_login(self.test_user_employer)

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            403,
            'It should return a success response')
