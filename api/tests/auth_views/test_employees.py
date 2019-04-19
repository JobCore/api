from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser


class EmployeesTestSuite(TestCase, WithMakeUser):
    """
    Endpoint tests for login
    """
    def setUp(self):
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile
        ) = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        self.employee_stack = []
        for _ in range(1, 10):
            emp = self._make_user('employee', userkwargs=dict(is_active=True))
            self.employee_stack.append(emp)

        self.client.force_login(self.test_user_employee)

    def test_get_employees(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:get-employees')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        response_json = response.json()

        self.assertEquals(len(response_json), 10)

    def test_get_employee_id(self):
        """
        Try to reach without credentials
        """
        _, emp, __ = self.employee_stack[0]
        url = reverse_lazy('api:id-employees', kwargs=dict(id=emp.id))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        response_json = response.json()

        self.assertEquals(response_json['id'], emp.id)

    def test_get_employee_id_evil(self):
        """
        Try to reach without credentials
        """
        url = reverse_lazy('api:id-employees', kwargs=dict(id=9999))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_delete_employee(self):
        """
        """
        _, emp, __ = self.employee_stack[0]
        url = reverse_lazy('api:id-employees', kwargs=dict(id=emp.id))
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 403)

    def test_delete_myself(self):
        """
        """
        url = reverse_lazy(
            'api:id-employees', kwargs=dict(id=self.test_employee.id))
        response = self.client.delete(url)
        self.assertEquals(response.status_code, 403)
