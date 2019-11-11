from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.apps import apps

Badge = apps.get_model('api', 'Badge')


@override_settings(STATICFILES_STORAGE=None)
class AdminBadgesTestSuite(TestCase, WithMakeUser, WithMakeShift):
    def setUp(self):
        (
            self.test_user_employer,
            self.test_employer,
            self.test_profile_employer
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer1',
                email='employer1@testdoma.in',
                is_active=True,
            )
        )
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        self.badges = []
        for i in range(0, 10):
            badge = mixer.blend('api.Badge')
            self.badges.append(badge)

    def test_put_badge_no_payload_empty(self):
        url = reverse_lazy('api:admin-id-employees-badges', kwargs=dict(
            employee_id=self.test_employee.id,
            ))

        self.client.force_login(self.test_user_employee)

        response = self.client.put(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

    def test_put_badge_empty(self):
        url = reverse_lazy('api:admin-id-employees-badges', kwargs=dict(
            employee_id=self.test_employee.id,
            ))

        payload = {
            'badges': []
        }

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

        response_json = response.json()
        self.assertIn('badges', response_json)

    def test_put_bad_employee(self):
        url = reverse_lazy('api:admin-id-employees-badges', kwargs=dict(
            employee_id=99999,
            ))

        payload = {
        }

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

        response_json = response.json()
        self.assertIn('employee', response_json)

    def test_put_badges(self):

        url = reverse_lazy('api:admin-id-employees-badges', kwargs=dict(
            employee_id=self.test_employee.id,
            ))

        payload = {
            'badges': [i.pk for i in self.badges]
        }

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        employee = self.test_employee
        e_badges = employee.badges.all()
        badges = self.badges
        self.assertCountEqual(badges, e_badges)

    def test_put_badges_not_interfering(self):
        _, ee2, __ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            )
        )
        ee2.badges.add(*self.badges)

        url = reverse_lazy('api:admin-id-employees-badges', kwargs=dict(
            employee_id=self.test_employee.id,
            ))

        payload = {
            'badges': [self.badges[0].pk]
        }

        self.client.force_login(self.test_user_employee)

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        self.assertEquals(self.test_employee.badges.count(), 1)
        self.assertEquals(ee2.badges.all().count(), 10)
