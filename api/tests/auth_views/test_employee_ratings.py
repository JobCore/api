from django.test import TestCase
from mixer.backend.django import mixer
import json
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.apps import apps

Rate = apps.get_model('api', 'Rate')


class EmployeeRatingTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for Rating
    @revisionNeeded
    """

    def setUp(self):
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
            ),
            employexkwargs=dict(
                ratings=0,
                total_ratings=0,
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
            ),
            employexkwargs=dict(
                rating=0,
                total_ratings=0,
            )
        )

        self.test_shift, _, __ = self._make_shift(
            employer=self.test_employer)

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            status='APPROVED'
        )

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=self.test_shift,
            employer=self.test_employer,
        )

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
        )

    def test_get_ratings(self):
        """
        Gets ratings
        """

        url = reverse_lazy('api:me-employees-ratings-sent')

        self.client.force_login(self.test_user_employee)
        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        count = Rate.objects.filter(
            sender__user=self.test_user_employee).count()

        self.assertEquals(len(response_json), count)

    def test_get_rating_tryforce_different_employer(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:me-employees-ratings-sent')

        self.client.force_login(self.test_user_employee)

        payload = {
            'employee': 99
        }

        response = self.client.get(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        count = Rate.objects.filter(
            sender__user=self.test_user_employee).count()

        self.assertEquals(len(response_json), count)

    def test_post_rating_employee(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:me-employees-ratings-sent')
        self.client.force_login(self.test_user_employee)

        payload = {

        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            405,
            'It should return a success response')
