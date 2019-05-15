from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.apps import apps

FavoriteList = apps.get_model('api', 'FavoriteList')


@override_settings(STATICFILES_STORAGE=None)
class EmployerFavouriteTestSuite(TestCase, WithMakeUser, WithMakeShift):
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

        _, employer2, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employerx',
                email='employerx@testdoma.in',
                is_active=True,
            )
        )

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employeez',
                email='employeez@testdoma.in',
                is_active=True,
            )
        )

        self.test_favlist = mixer.blend(
            'api.FavoriteList',
            employer=self.test_employer,
            auto_accept_employees_on_this_list=False
            )

        for i in range(1, 10):
            _, employee, __ = self._make_user(
                'employee',
                userkwargs=dict(
                    username='employee{}'.format(i),
                    email='employee{}@testdoma.in'.format(i),
                    is_active=True,
                )
            )
            self.test_favlist.employees.add(employee)

        self.test_favlist2 = mixer.blend(
            'api.FavoriteList',
            employer=employer2,
            auto_accept_employees_on_this_list=False
            )
        self.employees = []
        for i in range(20, 25):
            _, employee, __ = self._make_user(
                'employee',
                userkwargs=dict(
                    username='employee{}'.format(i),
                    email='employee{}@testdoma.in'.format(i),
                    is_active=True,
                )
            )
            self.test_favlist.employees.add(employee)
            self.employees.append(employee)

    def test_list_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-favlists')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        favlist = FavoriteList.objects.filter(
            employer_id=self.test_employer.id)

        self.assertEquals(len(response_json), favlist.count())

        count = favlist.first().employees.all().count()

        self.assertEquals(
            len(response_json[0]['employees']),
            count)

    def test_get_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist.id
            ))
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        favlist = FavoriteList.objects.get(
            employer_id=self.test_employer.id,
            id=self.test_favlist.id
            )

        count = favlist.employees.all().count()

        self.assertEquals(len(response_json['employees']), count)
        self.assertEquals(response_json['title'], favlist.title)

    def test_get_not_mine_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist2.id
            ))
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_post_no_payload_favlist(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-favlists')
        self.client.force_login(self.test_user_employer)

        response = self.client.post(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_empty_favlist(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-favlists')
        self.client.force_login(self.test_user_employer)

        payload = {}
        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")
        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_favlist(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-favlists')
        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'ZLorem ipsum dolor',
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")
        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        count = FavoriteList.objects.filter(
            title=payload['title'],
            employer_id=self.test_employer.id).count()

        self.assertEquals(count, 1)

    def test_post_favlist_with_employee(self):
        """
        """
        url = reverse_lazy('api:me-employer-get-favlists')
        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'ZLorem ipsum dolor',
            'employees': [i.pk for i in self.employees],
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        count = FavoriteList.objects.filter(
            title=payload['title'],
            employer_id=self.test_employer.id).count()

        self.assertEquals(count, 1)

    def test_put_not_mine_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist2.id
            ))
        self.client.force_login(self.test_user_employer)

        response = self.client.put(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_delete_not_mine_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist2.id
            ))
        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

    def test_delete_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist.id
            ))
        self.client.force_login(self.test_user_employer)

        response = self.client.delete(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            204,
            'It should return an error response')

        self.assertEquals(
            FavoriteList.objects.filter(id=self.test_favlist.id).count(),
            0)

    def test_put_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist.id
            ))
        self.client.force_login(self.test_user_employer)

        payload = {
            'title': 'A NEW!'
        }

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

        favlist = FavoriteList.objects.get(id=self.test_favlist.id)
        self.assertEquals(
            favlist.title, payload['title'])

    def test_put_bad_favlists(self):
        """
        """
        url = reverse_lazy('api:me-employer-id-favlists', kwargs=dict(
            id=self.test_favlist.id
            ))
        self.client.force_login(self.test_user_employer)

        payload = {
            'title': ''
        }

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')
