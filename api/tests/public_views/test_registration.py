from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls.base import reverse_lazy
from rest_framework_jwt.settings import api_settings
from mock import patch
from django.apps import apps
from datetime import timedelta
from django.utils import timezone
from api.tests.mixins import WithMakeUser

from api.models import City

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


@override_settings(STATICFILES_STORAGE=None)
class RegistrationTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for password reset
    """
    REGISTRATION_URL = reverse_lazy('api:register')

    def setUp(self):
        self.test_user, self.employer, _ = self._make_user(
            'employer',
            userkwargs=dict(
                username='test_user',
                email='test_user@testdoma.in',
                is_active=True,
            )
        )

        dt_2h_future = timezone.now() + timedelta(hours=2)
        shift = mixer.blend('api.Shift', starting_at=dt_2h_future)

        self.jc_invite = mixer.blend(
            'api.JobCoreInvite',
            sender=self.test_user.profile,
            email='delta@mail.tld',
            shift=shift,
        )

    def test_empty_form(self):
        payload = {
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

    def test_long_email(self):
        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'alpha.beta.gamma.delta.alpha.beta.gamma.delta.go.go.power.rangers@gosh.u.better.store.my.mail.mail.mail.very.evil.mail.why.u.hate.this.linter.so.much.tld',
            # NOQA: E261
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

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
        city = City.objects.create(name="Miami")
        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employee',
            "profile_city": city.id
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
        ShiftInvite = apps.get_model('api.ShiftInvite')

        employee = Employee.objects.filter(user_id=uid).first()
        self.assertNotEquals(employee, None)

        self.assertEqual(
            AvailabilityBlock.objects.filter(employee=employee).count(),
            7)

        self.assertEqual(
            Profile.objects.filter(user_id=uid).count(),
            1)

        self.assertEqual(
            ShiftInvite.objects.filter(
                shift=self.jc_invite.shift,
                employee=employee,
                sender=self.jc_invite.sender
            ).count(),
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

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employee_repeat_email(self, mocked_requests):
        """
        Repeating email on registration
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

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_wrong_account_type(self, mocked_requests):
        """
        Wrong account type
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
