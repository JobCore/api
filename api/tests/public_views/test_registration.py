from django.test import TestCase, override_settings
from unittest import expectedFailure
from mixer.backend.django import mixer
from django.urls.base import reverse_lazy
from rest_framework_jwt.settings import api_settings
from mock import patch
from django.apps import apps

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


@override_settings(STATICFILES_STORAGE=None)
class RegistrationTestSuite(TestCase):
    """
    Endpoint tests for password reset
    """
    REGISTRATION_URL = reverse_lazy('api:register')

    def setUp(self):
        self.test_user = self._make_user_with_profile(
            username='test_user',
            email='test_user@testdoma.in',
            is_active=True,
        )

        self.employer = mixer.blend('api.Employer')
        self.employer.save()

        shift = mixer.blend('api.Shift')

        mixer.blend(
            'api.JobCoreInvite',
            sender=self.test_user.profile,
            email='delta@mail.tld',
            shift=shift,
            )

    def _make_user_with_profile(self, **kwargs):
        test_user = mixer.blend(
            'auth.User',
            **kwargs
            )

        test_user.set_password('pass1234')
        test_user.save()

        test_profile = mixer.blend('api.Profile', user=test_user)
        test_profile.save()
        return test_user

    def test_empty_form(self):
        payload = {
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

    @expectedFailure
    def test_long_email(self):
        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'alpha.beta.gamma.delta.alpha.beta.gamma.delta.go.go.power.rangers@gosh.u.better.store.my.mail.mail.mail.very.evil.mail.why.u.hate.this.linter.so.much.tld',  # NOQA: E261
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

    @expectedFailure
    def test_missing_names(self):
        payload = {
            'username': 'test',
            'first_name': '',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employee_all_good(self, mocked_requests):
        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 201)

        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')

        jsonresp = response.json()
        uid = jsonresp['id']
        Employee = apps.get_model('api.Employee')
        AvailabilityBlock = apps.get_model('api.AvailabilityBlock')
        Profile = apps.get_model('api.Profile')

        employee = Employee.objects.filter(user_id=uid).first()
        self.assertNotEquals(employee, None)

        self.assertEqual(
            AvailabilityBlock.objects.filter(employee=employee).count(),
            7)

        self.assertEqual(
            Profile.objects.filter(user_id=uid).count(),
            1)

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employee_passing_id(self, mocked_requests):
        """
        ID Should be ignored from payload
        """

        payload = {
            'id': 1,
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 201)

        jsonresp = response.json()

        self.assertNotEquals(jsonresp['id'], payload['id'])

        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    @expectedFailure
    def test_employer_all_good(self, mocked_requests):
        """
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employer',
            'employer': self.employer.id,
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 201)
        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')
        Profile = apps.get_model('api.Profile')

        jsonresp = response.json()
        self.assertEquals(
            Profile.objects.filter(user_id=jsonresp['id']).count(),
            1
            )

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_invalid(self, mocked_requests):
        """
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employer',
            'employer': -1,
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)
        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')

    @expectedFailure
    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_no_employer(self, mocked_requests):
        """
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employer',
            # 'employer': -1,
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)
        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_invalid_string(self, mocked_requests):
        """
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employer',
            'employer': '2 OR 1=1',
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)
        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')

    @expectedFailure
    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employee_repeat_email(self, mocked_requests):
        """
        Repeating email on registration

        @todo:
            NameError: name 'ValidationError' is not defined
            "api/serializers/auth_serializer.py", line 93, in validate
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': self.test_user.email,
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')

    @expectedFailure
    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_wrong_account_type(self, mocked_requests):
        """
        Wrong account type
        @todo:
            NameError: name 'ValidationError' is not defined
            "api/serializers/auth_serializer.py", line 102, in validate
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': ':evil type:'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')
