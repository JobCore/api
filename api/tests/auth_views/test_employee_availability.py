from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.apps import apps
from api.actions.employee_actions import create_default_availablity
from django.utils import timezone
from datetime import timedelta
from django.test.client import MULTIPART_CONTENT

AvailabilityBlock = apps.get_model('api', 'AvailabilityBlock')


@override_settings(STATICFILES_STORAGE=None)
class EEAvailabilityTestSuite(TestCase, WithMakeUser, WithMakeShift):
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

    def test_list_availability(self):
        """
        """
        create_default_availablity(self.test_employee)
        url = reverse_lazy('api:me-employees-availability')
        self.client.force_login(self.test_user_employee)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        count = AvailabilityBlock.objects.filter(
            employee_id=self.test_employee.id).count()

        self.assertEquals(len(response_json), count)

    def test_list_availability_no_talent(self):
        """
        """
        user, employer, _ = self._make_user(
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

        url = reverse_lazy('api:me-employees-availability')
        self.client.force_login(user)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            403,
            'It should return an error response')

    def test_list_availability_no_auth(self):
        """
        """
        url = reverse_lazy('api:me-employees-availability')

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            401,
            'It should return an error response')

    def test_post_new_availability_no_recurrency(self):
        """
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should fail because non-recurrent types are not allowed yet')

    def test_post_new_availability_bad_start_end(self):
        """
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)

        payload = {
            'starting_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_new_availability_too_wide(self):
        """
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=25)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_new_availability_too_many(self):
        """
        """
        create_default_availablity(self.test_employee)

        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_delete_availability(self):
        create_default_availablity(self.test_employee)
        self.client.force_login(self.test_user_employee)

        availability = AvailabilityBlock.objects.last()
        url = reverse_lazy('api:me-employees-availability', kwargs={
            'block_id': 1
            })

        response = self.client.delete(url)

        self.assertEquals(
            response.status_code,
            404,
            'It should return an error response')

        url = reverse_lazy('api:me-employees-availability', kwargs={
            'block_id': availability.id
            })

        response = self.client.delete(url)
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_post_new_availability_duplicate(self):
        """
        """
        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)
        availability = mixer.blend(AvailabilityBlock,
                employee=self.test_employee,
                starting_at=avail_start,
                ending_at=avail_end)

        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')



    def test_post_new_availability_bad_recurrent(self):
        """
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
            'recurrent': True,
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

        payload['recurrency_type'] = 'DAILY'

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_post_new_availability_full_payload(self):
        """
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability')

        avail_start = timezone.now() + timedelta(days=30)
        avail_end = avail_start + timedelta(hours=8)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
            'recurrent': True,
            'recurrency_type': 'WEEKLY'
        }

        response = self.client.post(url, data=payload)

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

    # def test_overlapping_availability_weekly(self):
    #     """
    #     """
    #     create_default_availablity(self.test_employee)
    #     self.client.force_login(self.test_user_employee)
    #     url = reverse_lazy('api:me-employees-availability')

    #     avail_start = timezone.now() + timedelta(days=30)
    #     avail_end = avail_start + timedelta(hours=8)

    #     payload = {
    #         'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
    #         'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
    #         'recurrent': True,
    #         'recurrency_type': 'WEEKLY'
    #     }

    #     response = self.client.post(url, data=payload)
    #     self.assertEquals(response.status_code,400,'It should return an error response')

    def test_update_block(self):
        """
        """
        create_default_availablity(self.test_employee)
        target = AvailabilityBlock.objects.first()

        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability', kwargs=dict(
            block_id=target.id))

        avail_start = target.starting_at.replace(hour=8, minute=30)
        avail_end = target.ending_at.replace(hour=12, minute=30)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
            'recurrent': True,
            'recurrency_type': 'WEEKLY'
        }

        payload = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(url, payload, content_type=MULTIPART_CONTENT)

        self.assertEquals(
            response.status_code,
            200,
            'It should return an error response')

    def test_update_block_overlaps(self):
        """
        """
        create_default_availablity(self.test_employee)
        target = AvailabilityBlock.objects.first()

        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-availability', kwargs=dict(
            block_id=target.id))

        avail_start = target.starting_at + timedelta(days=1)
        avail_end = target.ending_at + timedelta(days=1)

        payload = {
            'starting_at': avail_start.strftime('%Y-%m-%dT%H:%M:%S'),
            'ending_at': avail_end.strftime('%Y-%m-%dT%H:%M:%S'),
            'recurrent': True,
            'recurrency_type': 'WEEKLY'
        }

        payload = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(url, payload, content_type=MULTIPART_CONTENT)

        self.assertEquals(
            response.status_code,
            200,
            'It should allow and update the original block')
