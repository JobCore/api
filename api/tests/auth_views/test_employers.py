import json
from django.test import TestCase
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser
from django.apps import apps

Employer = apps.get_model('api', 'Employer')
Profile = apps.get_model('api', 'Profile')
User = apps.get_model('auth', 'User')


class EmployersTestSuite(TestCase, WithMakeUser):
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

        self.test_user_employer, self.test_employer, _ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer@testdoma.in',
                is_active=True,
            )
        )

    def test_get_all_employers(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:get-employers')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, list)

        self.assertEquals(len(response_json), 1)

    def test_get_one_employer(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=self.test_employer.id))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertIsInstance(response_json, dict)
        self.assertEquals(response_json['id'], self.test_employer.id)
        self.assertEquals(response_json['bio'], self.test_employer.bio)
        self.assertEquals(response_json['website'], self.test_employer.website)
        self.assertEquals(response_json['title'], self.test_employer.title)

    def test_get_one_employer_non_existing(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:id-employers',
                           kwargs=dict(id=99999))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_get_one_employer_bad_id(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:get-employers') + '/ZZZZZZz'

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_no_auth(self):
        """
        Unauthorized list
        """

        url = reverse_lazy('api:get-employers')

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_get_me_noauth(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer')

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_get_me(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_update_me(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer')
        self.client.force_login(self.test_user_employer)

        payload = {
            'rating': 9.9,
            'total_ratings': 999,

            'title': 'Our sample title',
            'website': 'https://ademosite.com/',
            'bio': 'a sample bio',
            'response_time': 30,
            'automatically_accept_from_favlists': False,
            'payroll_period_starting_time': '2019-05-10T10:30',
            'payroll_period_length': 15,
            'payroll_period_type': 'MONTHS',
            'maximum_clockin_delta_minutes': 15,
            'maximum_clockout_delay_minutes': 15,
        }

        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        # self.test_employer.refresh_from_db()

        new_employer = Profile.objects.get(
            user=self.test_user_employer).employer

        self.assertEquals(
            new_employer.rating, self.test_employer.rating)

        self.assertEquals(
            new_employer.total_ratings, self.test_employer.total_ratings)

        self.assertNotEquals(
            new_employer.title,
            self.test_employer.title)
        self.assertNotEquals(
            new_employer.website,
            self.test_employer.website)
        self.assertNotEquals(
            new_employer.bio,
            self.test_employer.bio)
        self.assertNotEquals(
            new_employer.response_time,
            self.test_employer.response_time)
        self.assertNotEquals(
            new_employer.automatically_accept_from_favlists,
            self.test_employer.automatically_accept_from_favlists)
        self.assertNotEquals(
            new_employer.payroll_period_starting_time,
            self.test_employer.payroll_period_starting_time)
        self.assertNotEquals(
            new_employer.payroll_period_length,
            self.test_employer.payroll_period_length)
        self.assertNotEquals(
            new_employer.payroll_period_type,
            self.test_employer.payroll_period_type)
        self.assertNotEquals(
            new_employer.maximum_clockin_delta_minutes,
            self.test_employer.maximum_clockin_delta_minutes)
        self.assertNotEquals(
            new_employer.maximum_clockout_delay_minutes,
            self.test_employer.maximum_clockout_delay_minutes)

    def test_update_me_empty(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer')
        self.client.force_login(self.test_user_employer)

        payload = {
        }

        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,  # todos los campos son opcionales
            'It should return a success response')

    def test_update_change_payroll_bad_type(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer')
        self.client.force_login(self.test_user_employer)

        payload = {
            'payroll_period_type': 'ZZZZ',
        }

        response = self.client.put(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,  # todos los campos son opcionales
            'It should return an error response')

    def test_list_my_users(self):
        """
        Get employers logged in
        """

        url = reverse_lazy('api:me-employer-users')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        user_count = User.objects.filter(
            profile__employer_id=self.test_employer.id
            ).count()

        self.assertEquals(
            user_count,
            len(response_json)
            )
