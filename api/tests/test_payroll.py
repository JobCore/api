from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta, datetime
from django.apps import apps
from decimal import Decimal
import pytz
import math


Employer = apps.get_model('api', 'Employer')
Profile = apps.get_model('api', 'Profile')
PayrollPeriodPayment = apps.get_model('api', 'PayrollPeriodPayment')
PayrollPeriod = apps.get_model('api', 'PayrollPeriod')

@override_settings(STATICFILES_STORAGE=None)
class Payroll(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for clockinout
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
                created_at=timezone.now()
            )
        )

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=14),
            employer=self.test_employer)

        self.test_payrollperiod = mixer.blend(
            'api.PayrollPeriod',
            shift=self.test_shift,
            employer=self.test_employer
        )

        self.client.force_login(self.test_user_employer)

    def test_payroll_setting_update(self):
        
        url = reverse_lazy('api:me-employer')
        url_process_payroll = reverse_lazy('api:hook-generate_periods')
        response_process_payroll = self.client.get(
            url_process_payroll + "?employer="+str(self.test_employer.id),
            content_type="application/json")

        self.assertEquals(
            response_process_payroll.status_code,
            400,
            'You have to setup your payroll configuration')

        self.assertEquals(
            self.test_employer.payroll_period_starting_time, None)
        payload = {
            'payroll_period_starting_time': timezone.now(),
            'payroll_period_length': 15,
            'payroll_period_type': 'DAYS'
        }   

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")
 
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        updated_employer = Profile.objects.get(
            user=self.test_user_employer).employer
  
        self.assertNotEqual(
            updated_employer.payroll_period_starting_time, None)

    def test_first_payrollperiod(self):
        #Si la emrpesa no ha procesado ninguna nomina, la primera nomina debe buscar el dia de inicio una la semana hacia atras y no hacia adelante (solo la primera vez
        utc=pytz.UTC

        (
            self.test_user_employer2,
            self.test_employer2,
            self.test_profile_employer2
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                rating=0,
                created_at=timezone.now(),
                payroll_period_starting_time= timezone.now(),
                payroll_period_length= 7,
                payroll_period_type= 'DAYS'
            )
        )
        url_process_payroll = reverse_lazy('api:hook-generate_periods')
        response_process_payroll = self.client.get(
            url_process_payroll + "?employer="+str(self.test_employer2.id),content_type="application/json")

        res = response_process_payroll.json()
        print(response_process_payroll.json()[0]['starting_at'])
        payrollstart = datetime.strptime(response_process_payroll.json()[0]['starting_at'][:-1], "%Y-%m-%dT%H:%M:%S.%f")
        self.assertEquals(
           utc.localize(payrollstart) < timezone.now() - timedelta (days = 6), True, "The first payroll period will be one week behind the day you start using jobcore")
    
    def test_create_payment_without_shift_associated(self):

        self.test_shift2, _, __ = self._make_shift(
                    shiftkwargs=dict(status='OPEN', starting_at=timezone.now(), ending_at=timezone.now() + timedelta(hours=8), minimum_hourly_rate=15, minimum_allowed_rating = 0, 
                    maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
                    employer=self.test_employer)

        test_payroll_period = mixer.blend(
                'api.PayrollPeriod',
                employer=self.test_employer
            )


        payload = {
            'payroll_period': test_payroll_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id, 
            'shift': '', # shift not associated 
            # 'clockin': ,
            'splited_payment': True,
            'status':'PENDING',
            'breaktime_minutes':5,
            'regular_hours':8,
            'over_time':5,
            'hourly_rate':10,
            'total_amount':80,
            
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        response_json = response.json()
        print(response_json)
        self.assertEquals(response.status_code, 400, "No se debe hacer payment sin shift asociado")

    def test_create_payment_without_regularhours(self):

        self.test_shift2, _, __ = self._make_shift(
                    shiftkwargs=dict(status='OPEN', starting_at=timezone.now(), ending_at=timezone.now() + timedelta(hours=8), minimum_hourly_rate=15, minimum_allowed_rating = 0, 
                    maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
                    employer=self.test_employer)

        test_payroll_period = mixer.blend(
                'api.PayrollPeriod',
                employer=self.test_employer
            )

        payload = {
            'payroll_period': test_payroll_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id, 
            'shift': self.test_shift2.id, # shift not associated 
            # 'clockin': ,
            'splited_payment': True,
            'status':'PENDING',
            'breaktime_minutes':5,
            # 'regular_hours':, # no regular hours
            'over_time':5,
            'hourly_rate':10,
            'total_amount':80,
            
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        response_json = response.json()
        print(response_json)
        self.assertEquals(response.status_code, 400, "No se debe hacer payment sin regular hours")

    def test_create_payment_without_over_time(self):

        self.test_shift2, _, __ = self._make_shift(
                    shiftkwargs=dict(status='OPEN', starting_at=timezone.now(), ending_at=timezone.now() + timedelta(hours=8), minimum_hourly_rate=15, minimum_allowed_rating = 0, 
                    maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
                    employer=self.test_employer)

        test_payroll_period = mixer.blend(
                'api.PayrollPeriod',
                employer=self.test_employer
            )

        payload = {
            'payroll_period': test_payroll_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id, 
            'shift': self.test_shift2.id, # shift not associated 
            # 'clockin': ,
            'splited_payment': True,
            'status':'PENDING',
            'breaktime_minutes':5,
            'regular_hours': 6, 
            # 'over_time':5,
            'hourly_rate':10,
            'total_amount':80,
            
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        response_json = response.json()
        print(response_json)
        self.assertEquals(response.status_code, 400, "No se debe hacer payment sin overtime")

    def test_create_payment_without_breaktime_minutes(self):

        self.test_shift2, _, __ = self._make_shift(
                    shiftkwargs=dict(status='OPEN', starting_at=timezone.now(), ending_at=timezone.now() + timedelta(hours=8), minimum_hourly_rate=15, minimum_allowed_rating = 0, 
                    maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
                    employer=self.test_employer)

        test_payroll_period = mixer.blend(
                'api.PayrollPeriod',
                employer=self.test_employer
            )

        payload = {
            'payroll_period': test_payroll_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id, 
            'shift': self.test_shift2.id, # shift not associated 
            # 'clockin': ,
            'splited_payment': True,
            'status':'PENDING',
            # 'breaktime_minutes':5,
            'regular_hours': 6,
            'over_time':5,
            'hourly_rate':10,
            'total_amount':80,
            
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        response_json = response.json()
        print(response_json)
        self.assertEquals(response.status_code, 400, "No se debe hacer payment sin breaktime minutes")

    def test_two_day_shift_payment(self):

        starting_at = timezone.now()
        ending_at = timezone.now() + timedelta(hours=24)

        self.test_shift2, _, __ = self._make_shift(
                    shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=8, minimum_allowed_rating = 0, 
                    maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
                    employer=self.test_employer)

        test_payroll_period = mixer.blend(
                'api.PayrollPeriod',
                employer=self.test_employer
            )


        payload = {
            'payroll_period': test_payroll_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id, 
            'shift': self.test_shift2.id,
            # 'clockin': ,
            'splited_payment': True,
            'status':'PENDING',
            'breaktime_minutes':5,
            'regular_hours':6.25,
            'over_time':10,
            'hourly_rate':8,
            'total_amount':55,
            
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        response_json = response.json()

        _payment = PayrollPeriodPayment.objects.get(id=response_json['id'])
        
        self.assertEquals(response.status_code, 200, "No se debe hacer payment sin shift asociado")
        self.assertEquals(_payment.splited_payment, True, "Splitted payment must be equal to true")

    def test_payroll_starting_at_update(self):
        (
            self.test_user_employer2,
            self.test_employer2,
            self.test_profile_employer2
        ) = self._make_user(
            'employer',
            userkwargs=dict(
                username='employer2',
                email='employer2@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                rating=0,
                created_at=timezone.now() - timedelta(days=2),
                payroll_period_starting_time= timezone.now() - timedelta(days=2),
                payroll_period_length= 7,
                payroll_period_type= 'DAYS'
            )
        )

        self.client.force_login(self.test_user_employer2)
        url = reverse_lazy('api:me-employer')

        payload = {
            'payroll_period_starting_time': timezone.now() - timedelta(days=4),
            'payroll_period_length': 7,
            'payroll_period_type': 'DAYS'
        }   

        response = self.client.put(
            url,
            data=payload,
            content_type="application/json")
        
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        updated_employer = Employer.objects.get(
            id=self.test_employer2.id).payroll_period_starting_time
        today = timezone.now()
        # print(updated_employer)
        # self.assertEquals(
        #     updated_employer.payroll_period_starting_time > today, True, "Next starting period time must be next week")

    def test_create_payment_verify_amounts(self):
        """Create a PayrollPaymentEmployer with wrong total_amount value, then verify returned total_amount"""
        test_shift, _, __ = self._make_shift(
            shiftkwargs={'status': 'OPEN', 'starting_at': timezone.now(),
                         'ending_at': timezone.now() + timedelta(hours=8), 'minimum_hourly_rate': 15,
                         'minimum_allowed_rating': 0, 'maximum_clockin_delta_minutes': 15,
                         'maximum_clockout_delay_minutes': 15, 'maximum_allowed_employees': 5,
                         'employees': self.test_employee},
            employer=self.test_employer)
        test_period = mixer.blend('api.PayrollPeriod', employer=self.test_employer)

        payload = {
            'payroll_period': test_period.id,
            'employee': self.test_employee.id,
            'employer': self.test_employer.id,
            'shift': test_shift.id,
            'splited_payment': True,
            'status': 'PENDING',
            'breaktime_minutes': 5,
            'regular_hours': 6,
            'over_time': 2.42,
            'hourly_rate': 8.4,
            'total_amount': 13,
        }
        url = reverse_lazy('api:me-get-payroll-payments-employer')
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200, response.content.decode())
        response_json = response.json()
        self.assertEqual(response_json.get('breaktime_minutes'), 5, response_json)
        self.assertEqual(Decimal(response_json.get('regular_hours')), Decimal(payload.get('regular_hours')), response_json)
        self.assertEqual(Decimal(response_json.get('over_time')), Decimal(str(payload.get('over_time'))), response_json)
        self.assertIsNotNone(response_json.get('hourly_rate'), response_json)
        self.assertIsNotNone(response_json.get('total_amount'), response_json)
        total_amount = Decimal(str(
            math.trunc((Decimal(response_json.get('regular_hours')) + Decimal(response_json.get('over_time')))
                       * Decimal(response_json.get('hourly_rate')) * 100) / 100
        ))
        self.assertEqual(Decimal(response_json.get('total_amount')), total_amount, response_json)
