from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.apps import apps

Venue = apps.get_model('api', 'Venue')


@override_settings(STATICFILES_STORAGE=None)
class EmployerVenueTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for login
    """

    def setUp(self):
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

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

    def test_list_venues(self):
        """
        """
        _, emp2, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            )
        )

        for i in range(1, 10):
            mixer.blend('api.Venue', employer=self.test_employer)

        for i in range(1, 2):
            mixer.blend('api.Venue', employer=emp2)

        url = reverse_lazy('api:me-employer-get-venues')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()
        count = Venue.objects.filter(employer_id=self.test_employer.id).count()
        self.assertEquals(len(response_json), count)

    def test_get_venue(self):
        """
        """
        venue = mixer.blend('api.Venue', employer=self.test_employer)

        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()
        self.assertEquals(
            response_json['id'], venue.id)

        self.assertEquals(
            response_json['title'], venue.title)

        self.assertEquals(
            response_json['employer'], venue.employer.id)

        self.assertEquals(
            response_json['street_address'], venue.street_address)

        self.assertEquals(
            response_json['country'], venue.country)

        self.assertEquals(
            float(response_json['latitude']), float(venue.latitude))

        self.assertEquals(
            float(response_json['longitude']), float(venue.longitude))

        self.assertEquals(
            response_json['state'], venue.state)

        self.assertEquals(
            response_json['zip_code'], venue.zip_code)

    def test_get_404_venue(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=999
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_get_not_your_venue(self):
        """
        """
        _, emp2, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            )
        )

        venue = mixer.blend('api.Venue', employer=emp2)

        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_delete_404_venue(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=999
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_delete_not_your_venue(self):
        """
        """
        _, emp2, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            )
        )

        venue = mixer.blend('api.Venue', employer=emp2)

        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_delete_venue(self):
        """
        """
        venue = mixer.blend('api.Venue', employer=self.test_employer)

        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            204,
            'It should return a success response')

        self.assertEquals(
            Venue.objects.filter(id=venue.id).count(), 0)

    def test_create_venue_nodata(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-venues')

        self.client.force_login(self.test_user_employer)

        payload = {}
        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

    def test_create_venue_empty(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-venues')

        self.client.force_login(self.test_user_employer)

        payload = {
            'title': '',
            'street_address': '',
            'country': '',
            'latitude': '',
            'longitude': '',
            'state': '',
            'zip_code': '',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')

        self.assertEquals(Venue.objects.all().count(), 0)

    def test_create_venue(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-venues')

        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'a new venue',
            'street_address': 'My great address',
            'country': 'A country',
            'latitude': '64',
            'longitude': '10',
            'state': 'State?',
            'zip_code': '3123',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        self.assertEquals(Venue.objects.all().count(), 1)

    def test_put_404_venue(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=999
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.put(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_put_not_your_venue(self):
        """
        """
        _, emp2, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            )
        )

        venue = mixer.blend('api.Venue', employer=emp2)

        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id
            ))

        self.client.force_login(self.test_user_employer)

        response = self.client.put(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return a success response')

    def test_put_venue(self):
        """
        """
        venue = mixer.blend('api.Venue', employer=self.test_employer)
        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id))

        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'a new venue',
            'street_address': 'My great address',
            'country': 'A country',
            'state': 'State?',
            'zip_code': 3123,
        }

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        for key in payload.keys():
            self.assertEquals(response_json[key], payload[key])
            self.assertNotEquals(response_json[key], getattr(venue, key))

    def test_put_venue_bad(self):
        """
        """
        venue = mixer.blend('api.Venue', employer=self.test_employer)
        url = reverse_lazy('api:me-employer-id-venues', kwargs=dict(
            id=venue.id))

        self.client.force_login(self.test_user_employer)

        payload = {
            'zip_code': 'ZZZ',
        }

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response')
