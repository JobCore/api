from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from django.apps import apps
from django.test.client import MULTIPART_CONTENT

FCMDevice = apps.get_model('api', 'FCMDevice')


class EmployeeDevicesTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for devices
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

        self.employee_device = mixer.blend(
            'api.FCMDevice',
            user=self.test_user_employee,
            registration_id='device-employee'
            )

        self.employer_device = mixer.blend(
            'api.FCMDevice',
            user=self.test_user_employer,
            registration_id='device-employer'
            )

    def test_get_devices(self):
        """
        Try to reach without credentials
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-all-device')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        count = FCMDevice.objects.filter(user=self.test_user_employee).count()

        self.assertEquals(len(response_json), count)

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        count = FCMDevice.objects.filter(user=self.test_user_employer).count()

        self.assertEquals(len(response_json), count)

    def test_get_device(self):
        """
        Try to reach without credentials
        """

        suite = [
            [self.test_user_employee, self.employee_device],
            [self.test_user_employer, self.employer_device],
        ]

        for user, device in suite:
            self.client.force_login(user)

            url = reverse_lazy('api:me-employees-device', kwargs={
                'device_id': device.registration_id
            })

            response = self.client.get(url)
            self.assertEquals(response.status_code, 200)
            response_json = response.json()

            self.assertEquals(response_json['id'], device.id)

            self.assertEquals(
                response_json['registration_id'],
                device.registration_id)

    def test_get_device_regid_not_belongs(self):
        """
        Try to reach without credentials
        """
        self.client.force_login(self.test_user_employee)

        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employer_device.registration_id
        })

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_get_device_wrong(self):
        """
        Try to reach without credentials
        """
        self.client.force_login(self.test_user_employee)

        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': 9999999
        })

        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_unauth(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': 1
        })

        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

        url = reverse_lazy('api:me-employees-all-device')

        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_delete_device(self):
        """
        Try to reach without credentials
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employee_device.registration_id
        })

        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)

        exists = FCMDevice.objects.filter(
            id=self.employee_device.id).exists()

        self.assertEquals(exists, False)

        self.client.force_login(self.test_user_employer)
        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employer_device.registration_id
        })

        response = self.client.delete(url)
        self.assertEquals(response.status_code, 204)

        exists = FCMDevice.objects.filter(
            id=self.employer_device.id).exists()

        self.assertEquals(exists, False)

    def test_delete_device_not_mine(self):
        """
        Try to reach without credentials
        """
        self.client.force_login(self.test_user_employee)
        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employer_device.registration_id
        })

        response = self.client.delete(url)
        self.assertEquals(response.status_code, 404)

        count = FCMDevice.objects.all().count()

        self.assertEquals(count, 2)

    def test_update_device(self):
        self.client.force_login(self.test_user_employee)

        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employee_device.registration_id
        })

        payload = {
            'registration_id': 'new-regid'
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)
        self.assertEquals(response.status_code, 200)

        response_json = response.json()

        self.assertNotEquals(
            self.employer_device.registration_id,
            response_json['registration_id']
            )

    def test_update_device_not_mine(self):
        self.client.force_login(self.test_user_employee)

        url = reverse_lazy('api:me-employees-device', kwargs={
            'device_id': self.employer_device.registration_id
        })

        payload = {
            'registration_id': 'new-regid'
        }

        payload_enc = self.client._encode_data(payload, MULTIPART_CONTENT)
        response = self.client.put(
            url, data=payload_enc, content_type=MULTIPART_CONTENT)

        self.assertEquals(response.status_code, 404)
