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

    def test_pass_8_char(self):
        payload = {
            'username': 'test',
            'first_name': 'Beta',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABD',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400, "password must be 8 characters long")

    def test_pass_one_cap(self):
        payload = {
            'username': 'test',
            'first_name': 'Beta',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'abcdefghi',
            'account_type': 'employee'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400, "password must have one capital letter")

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employee_all_good(self, mocked_requests):
        city = City.objects.create(name="Miami")
        Employee = apps.get_model('api.Employee')
        AvailabilityBlock = apps.get_model('api.AvailabilityBlock')
        Profile = apps.get_model('api.Profile')
        ShiftInvite = apps.get_model('api.ShiftInvite')

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABhgvbhjbhjD',
            'account_type': 'employee',
            "profile_city": city.id
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        self.assertEquals(response.status_code, 201)
        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')
        json_resp = response.json()
        uid = json_resp['id']

        employee = Employee.objects.filter(user_id=uid).first()
        self.assertNotEquals(employee, None)
        self.assertEqual(AvailabilityBlock.objects.filter(employee=employee).count(), 7)
        self.assertEqual(Profile.objects.filter(user_id=uid).count(), 1)
        self.assertEqual(ShiftInvite.objects.filter(
            shift=self.jc_invite.shift,
            employee=employee,
            sender=self.jc_invite.sender
        ).count(), 1)

        # Testing city text
        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail3.tld',
            'password': 'AnbvcbchvBD',
            'account_type': 'employee',
            "city": "Chicago"
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        self.assertEquals(response.status_code, 201, response.content)
        self.assertEquals(
            mocked_requests.post.called,
            True,
            'It should have called requests.post to send mail')
        json_resp = response.json()
        uid = json_resp['id']

        employee = Employee.objects.filter(user_id=uid).first()
        self.assertNotEquals(employee, None)
        self.assertEqual(AvailabilityBlock.objects.filter(employee=employee).count(), 7)
        self.assertEqual(Profile.objects.filter(user_id=uid).count(), 1)

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
            'password': 'jhvjhghjbABD',
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
            'password': 'AadadsdasBD',
            'account_type': 'employer',
            'employer': self.employer.id,
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        print(response.content)
        self.assertEquals(response.status_code, 201)

        # Once the registration is activated again we have re-enable this commented code

        # self.assertEquals(response.status_code, 201)
        # self.assertEquals(
        #     mocked_requests.post.called,
        #     True,
        #     'It should have called requests.post to send mail')
        # Profile = apps.get_model('api.Profile')

        # jsonresp = response.json()
        # self.assertEquals(
        #     Profile.objects.filter(user_id=jsonresp['id']).count(),
        #     1
        # )

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
            'password': 'ABuhbkhjbkjhbD',
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
    def test_employer_invalid_string(self, mocked_requests):
        """
        """

        payload = {
            'username': 'test',
            'first_name': 'Alpha',
            'last_name': 'Bravo',
            'email': 'delta@mail.tld',
            'password': 'ABfdsvsdfvsdfvD',
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
            'password': 'ABdvsdfvsdfvsdfvD',
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
            'password': 'ABvdfvdfvdfvfvD',
            'account_type': ':evil type:'
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)

        self.assertEquals(response.status_code, 400)

        self.assertEquals(
            mocked_requests.post.called,
            False,
            'It should have called requests.post to send mail')

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_register_with_id(self, mocked_requests):
        """
        Wrong account type
        """

        payload = {
            'employer': self.employer.id,
            'email': "ixaxtav+prueba1@gmail.com",
            'account_type': "employer",
            'username': "ixaxtav+prueba1@gmail.com",
            'first_name': "Prueba",
            'last_name': "Pruebon",
            'password': "L12121212",
            'phone': "(233) 231 - 23121"
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        print(response.content)
        self.assertEquals(response.status_code, 200)

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_register_business_name(self): 
        payload = {
            'business_name': "ixax bus"
            'business_website': "website"
            'about_business': "googeldokfaoskdso" 
            'employer': None,
            'email': "ixaxtav+prueba1@gmail.com",
            'account_type': "employer",
            'username': "ixaxtav+prueba1@gmail.com",
            'first_name': "Prueba",
            'last_name': "Pruebon",
            'password': "L12121212",
            'phone': "(233) 231 - 23121"
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        print(response.content)
        self.assertEquals(response.status_code, 200)

    @patch('api.utils.email.requests')
    @override_settings(EMAIL_NOTIFICATIONS_ENABLED=True)
    def test_employer_register_random_ID(self): 
        payload = {
            'business_name': "ixax bus"
            'business_website': "website"
            'about_business': "googeldokfaoskdso" 
            'employer': 3124214,
            'email': "ixaxtav+prueba1@gmail.com",
            'account_type': "employer",
            'username': "ixaxtav+prueba1@gmail.com",
            'first_name': "Prueba",
            'last_name': "Pruebon",
            'password': "L12121212",
            'phone': "(233) 231 - 23121"
        }

        response = self.client.post(self.REGISTRATION_URL, data=payload)
        print(response.content)
        self.assertEquals(response.status_code, 200)
