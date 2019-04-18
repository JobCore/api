from django.test import TestCase
from mixer.backend.django import mixer
import json
from mock import patch
from django.urls import reverse_lazy
# from unittest import expectedFailure
# from django.apps import apps


class RatingTestSuite(TestCase):
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

        # self.test_employee_rating = mixer.blend(
        #     'api.Rate',
        #     sender=self.test_profile_employee,
        #     shift=self.test_shift,
        #     employee=self.test_employee,
        #     )

        # self.test_employer_rating = mixer.blend(
        #     'api.Rate',
        #     sender=self.test_profile_employee,
        #     shift=self.test_shift,
        #     employer=self.test_employer,
        #     )

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            status='APPROVED'
            )

    def _make_shift(self, employer):
        venue = mixer.blend('api.Venue', employer=employer)
        position = mixer.blend('api.Position')

        shift = mixer.blend(
            'api.Shift',
            venue=venue,
            position=position,
            employer=employer)

        return shift, venue, position

    def _make_user(self, 
        kind, userkwargs={}, employexkwargs={}, profilekwargs={}):

        if kind not in ['employee', 'employer']:
            raise RuntimeError('Do you know what are you doing?')

        user = mixer.blend('auth.User', **userkwargs)
        user.set_password('pass1234')
        user.save()

        emptype = 'api.Employee' if kind == 'employee' else 'api.Employer'

        if kind == 'employee':
            employexkwargs.update({
                'user': user
            })

        emp = mixer.blend(emptype, **employexkwargs)
        emp.save()

        profilekwargs = profilekwargs.copy()
        profilekwargs.update({
            'user': user,
            kind: emp,
        })

        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

        return user, emp, profile

    def test_get_ratings(self):
        """
        Gets ratings
        """

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

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 2)

    # @expectedFailure
    def test_post_rating_employee(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('comments', response_json)
        self.assertIn('shift', response_json)
        self.assertIn('id', response_json)
        self.assertIn('rating', response_json)

        self.test_employer.refresh_from_db()

        self.assertEquals(float(self.test_employer.rating), 4)
        self.assertEquals(self.test_employer.total_ratings, 1)

    def test_post_rating_employer(self):
        """
        Gets ratings
        """

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response.')

        response_json = response.json()

        self.assertIn('comments', response_json)
        self.assertIn('shift', response_json)
        self.assertIn('id', response_json)
        self.assertIn('rating', response_json)

        self.test_employee.refresh_from_db()

        self.assertEquals(float(self.test_employee.rating), 4)
        self.assertEquals(self.test_employee.total_ratings, 1)

    def test_post_double_rating(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

    def test_rate_without_clocking_in(self):
        """
        Gets ratings
        """
        new_shift, *_ = self._make_shift(
            employer=self.test_employer)
        new_shift.save()

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_integer(self, *a):
        """
        Gets ratings
        """
        new_shift, *_ = self._make_shift(
            employer=self.test_employer)

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_num_out_of_range(self, *a):
        """
        Gets ratings
        """
        new_shift, *_ = self._make_shift(
            employer=self.test_employer)

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 9,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_get_ratings_filter_employee(self):
        """
        Gets ratings
        """

        new_shift, *_ = self._make_shift(
            employer=self.test_employer)

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=self.test_shift,
            employer=self.test_employer,
            )
        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=new_shift,
            employer=self.test_employer,
            )

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
            )

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(
            url,
            data=dict(employee=self.test_employee.id),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 1)

        response = self.client.get(
            url,
            data=dict(employer=self.test_employer.id),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 2)

    def test_rate_talentxtalent(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_employerxemployer(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')
