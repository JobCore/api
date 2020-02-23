from django.test import TestCase
from django.urls import reverse_lazy

from api.tests.mixins import WithMakeShift, WithMakeUser


class PayrollPeriodTestSuite(TestCase, WithMakeUser, WithMakeShift):

    def setUp(self):
        self.test_user_employer, self.test_employer, self.test_profile_employer = self._make_user(
            'employer',
            userkwargs={"username": 'employer', "email": 'employer@testdoma.in', "is_active": True},
            employexkwargs={"maximum_clockin_delta_minutes": 15, "maximum_clockout_delay_minutes": 15,
                            "rating": 0, "total_ratings": 0}
        )
        self.test_user_employer2, self.test_employer2, self.test_profile_employer2 = self._make_user(
            'employer',
            userkwargs={"username": 'employer2', "email": 'employer2@testdoma.in', "is_active": True},
            employexkwargs={"maximum_clockin_delta_minutes": 15, "maximum_clockout_delay_minutes": 15,
                            "rating": 0, "total_ratings": 0}
        )
        self.test_user_employee, self.test_employee, self.test_profile_employee = self._make_user(
            'employee',
            userkwargs={"username": 'employee', "email": 'employee@testdoma.in', "is_active": True},
        )
        self.test_user_employee2, self.test_employee2, self.test_profile_employee2 = self._make_user(
            'employee',
            userkwargs={"username": 'employee2', "email": 'employee2@testdoma.in', "is_active": True},
        )

        self.shift, _, _ = self._make_shift(self.test_employer,
                                            shiftkwargs={'status': 'OPEN', 'maximum_allowed_employees': 2})
        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'OPEN', 'maximum_allowed_employees': 2})
        self.shift_open_ids = [self.shift.id, shift.id]
        self.all_shift_ids = [self.shift.id, shift.id]
        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'FILLED', 'maximum_allowed_employees': 2})
        self.shift_filled_ids = [shift.id]
        self.all_shift_ids.append(shift.id)
        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'COMPLETED', 'maximum_allowed_employees': 2})
        shift2, _, _ = self._make_shift(self.test_employer,
                                        shiftkwargs={'status': 'COMPLETED', 'maximum_allowed_employees': 2})
        self.shift_completed_ids = [shift.id, shift2.id]
        self.all_shift_ids.append(shift.id)
        self.all_shift_ids.append(shift2.id)
        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'DRAFT', 'maximum_allowed_employees': 2})
        self.shift_draft_ids = [shift.id]
        self.all_shift_ids.append(shift.id)
        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'CANCELLED', 'maximum_allowed_employees': 2})
        shift2, _, _ = self._make_shift(self.test_employer,
                                        shiftkwargs={'status': 'CANCELLED', 'maximum_allowed_employees': 2})
        self.shift_cancelled_ids = [shift.id, shift2.id]
        self.all_shift_ids.append(shift.id)
        self.all_shift_ids.append(shift2.id)

        shift, _, _ = self._make_shift(self.test_employer,
                                       shiftkwargs={'status': 'OPEN', 'maximum_allowed_employees': 2})
        self.shift_open_ids.append(shift.id)
        self.all_shift_ids.append(shift.id)
        shift.employees.add(self.test_employee)
        shift.employees.add(self.test_employee2)
        self.shift_fill_ids = [shift.id]

    def test_get_my_shifts(self):
        url = reverse_lazy('api:me-employer-get-new-shifts')
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, list, response_json)
        self.assertEqual(len(response_json), 7, response_json)
        for shift in response_json:
            self.assertIn(shift.get('id'), self.all_shift_ids, shift)
            self.assertEqual(shift.get('employer'), self.test_employer.id, shift)
            self.assertIsInstance(shift.get('venue'), dict, shift)
            self.assertIsInstance(shift.get('position'), dict, shift)
            self.assertIsInstance(shift.get('maximum_allowed_employees'), int, shift)
            self.assertIsNotNone(shift.get('minimum_hourly_rate'), shift)
            self.assertIn(shift.get('status'), ['OPEN', 'FILLED', 'COMPLETED', 'DRAFT'], shift)
            self.assertIsInstance(shift.get('employees'), list, shift)
            self.assertIsInstance(shift.get('candidates'), list, shift)

    def test_get_my_shifts2(self):
        """Test getting an empty list"""
        url = reverse_lazy('api:me-employer-get-new-shifts')
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, list, response_json)
        self.assertEqual(len(response_json), 0, response_json)

    def test_get_my_cancelled_shifts(self):
        url = reverse_lazy('api:me-employer-get-new-shifts') + '?status=CANCELLED'
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, list, response_json)
        self.assertEqual(len(response_json), 2, response_json)
        for shift in response_json:
            self.assertIn(shift.get('id'), self.shift_cancelled_ids, shift)
            self.assertEqual(shift.get('employer'), self.test_employer.id, shift)
            self.assertIn(shift.get('status'), ['CANCELLED'], shift)
            self.assertIsInstance(shift.get('employees'), list, shift)
            self.assertIsInstance(shift.get('candidates'), list, shift)

    def test_get_my_shifts_except_open(self):
        url = reverse_lazy('api:me-employer-get-new-shifts') + '?not_status=OPEN'
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, list, response_json)
        self.assertEqual(len(response_json), 4, response_json)
        all_ids = self.shift_filled_ids + self.shift_completed_ids + self.shift_draft_ids
        for shift in response_json:
            self.assertIn(shift.get('id'), all_ids, shift)
            self.assertEqual(shift.get('employer'), self.test_employer.id, shift)
            self.assertIn(shift.get('status'), ['FILLED', 'COMPLETED', 'DRAFT'], shift)
            self.assertIsInstance(shift.get('employees'), list, shift)
            self.assertIsInstance(shift.get('candidates'), list, shift)

    def test_get_my_shift_fill_condition(self):
        url = reverse_lazy('api:me-employer-get-new-shifts') + '?filled=true'
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, list, response_json)
        self.assertEqual(len(response_json), 1, response_json)
        for shift in response_json:
            self.assertIn(shift.get('id'), self.shift_fill_ids, shift)
            self.assertEqual(shift.get('employer'), self.test_employer.id, shift)
            self.assertIn(shift.get('status'), ['OPEN'], shift)
            self.assertIsInstance(shift.get('employees'), list, shift)
            self.assertEqual(len(shift.get('employees')), 2, shift)
            self.assertIsInstance(shift.get('candidates'), list, shift)

    def test_get_my_shifts_wrong_status(self):
        url = reverse_lazy('api:me-employer-get-new-shifts') + '?status=OTHER'
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertContains(response, 'Invalid Status', status_code=400)

    def test_get_one_shift(self):
        url = reverse_lazy('api:me-employer-id-new-shifts', kwargs={'id': self.shift_draft_ids[0]})
        self.client.force_login(self.test_user_employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertIsInstance(response_json, dict, response_json)
        self.assertEqual(response_json.get('id'), self.shift_draft_ids[0], response_json)
        self.assertIsInstance(response_json.get('employer'), dict, response_json)
        self.assertEqual(response_json.get('employer').get('id'), self.test_employer.id, response_json)
        self.assertEqual(response_json.get('employer').get('title'), self.test_employer.title, response_json)
        self.assertEqual(response_json.get('status'), 'DRAFT', response_json)
        self.assertIsInstance(response_json.get('employees'), list, response_json)
        self.assertIsInstance(response_json.get('candidates'), list, response_json)

    def test_get_one_shift_no_linked(self):
        url = reverse_lazy('api:me-employer-id-new-shifts', kwargs={'id': self.shift_draft_ids[0]})
        self.client.force_login(self.test_user_employer2)
        response = self.client.get(url)
        self.assertContains(response, 'Not found', status_code=404)
