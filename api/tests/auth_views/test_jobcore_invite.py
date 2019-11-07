from django.test import TestCase, override_settings
from mixer.backend.django import mixer
import json
from mock import patch
from django.urls import reverse_lazy
from django.apps import apps
from api.tests.mixins import WithMakeUser, WithMakeShift


@override_settings(STATICFILES_STORAGE=None)
class JobcoreInviteTestSuite(TestCase, WithMakeUser, WithMakeShift):
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

        self.test_shift, _, __ = self._make_shift(
            employer=self.test_employer)

        self.test_invite = mixer.blend(
            'api.JobCoreInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift)

    def test_list_jobcore_invites(self):
        """
        Send an invite
        """

        url = reverse_lazy('api:get-jcinvites')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 1)

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_send_jobcore_invite(self, mocked_requests):
        """
        Send an invite
        """

        url = reverse_lazy('api:get-jcinvites')
        self.client.force_login(self.test_user_employer)

        payload = {
            'email': 'invite@testdoma.in'
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')

    # @expectedFailure
    def test_send_jobcore_invite_empty_payload(self):
        """
        Send an invite
        """

        url = reverse_lazy('api:get-jcinvites')
        self.client.force_login(self.test_user_employer)

        payload = {
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_send_jobcore_invite_already_in_jobcore(self, mocked_requests):
        """
        Send an invite
        """

        url = reverse_lazy('api:get-jcinvites')
        self.client.force_login(self.test_user_employer)

        payload = {
            'email': self.test_user_employer.email,
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should NOT have called requests.post to send mail')

    def test_delete_jobcore_invite(self):
        """
        Delete an invitation
        """

        url = reverse_lazy(
            'api:id-jcinvites',
            kwargs=dict(id=self.test_invite.id)
        )

        self.client.force_login(self.test_user_employer)

        response = self.client.delete(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            204,
            'It should return a success response')

        JobCoreInvite = apps.get_model('api.JobCoreInvite')

        with self.assertRaises(JobCoreInvite.DoesNotExist):
            JobCoreInvite.objects.get(id=self.test_invite.id)

    def test_delete_jobcore_invite_evil_id(self):
        """
        Delete an evil id
        """

        url = reverse_lazy(
            'api:id-jcinvites',
            kwargs=dict(id=9999)
        )

        self.client.force_login(self.test_user_employer)

        response = self.client.delete(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')
