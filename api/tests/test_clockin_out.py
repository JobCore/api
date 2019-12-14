from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps

Clockin = apps.get_model('api', 'Clockin')
Shift = apps.get_model('api', 'Shift')
@override_settings(STATICFILES_STORAGE=None)
class ClockinOut(TestCase, WithMakeUser, WithMakeShift):
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
                maximum_clockin_delta_minutes=15,
                maximum_clockout_delay_minutes=15,
                rating=0,
                total_ratings=0,
            )
        )

        self.test_shift, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0], #Open
                'maximum_clockin_delta_minutes': 15,
                'maximum_clockout_delay_minutes': 15,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)

        self.test_shift_clockoutdelay_zero, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0], #Open
                'maximum_clockin_delta_minutes': 0,
                'maximum_clockout_delay_minutes': 0,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)

        self.test_shift_null, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift,
        )

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift_null,
        )

        self.client.force_login(self.test_user_employee)

    def test_new_shift_max_clock_min_clock(self):
        # When a new shift is created, the maximum clockin and clockout has to be inherted from its employer.
        position = mixer.blend('api.Position')
        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)
        self.test_newshift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=10),
            employer=self.test_employer)
        
   
        self.assertEquals(self.test_employer.maximum_clockin_delta_minutes == self.test_newshift.maximum_clockin_delta_minutes, True, 'maximum_clockin_delta_minutes must be equal if the shift clockin is not specified')
        self.assertEquals(self.test_employer.maximum_clockout_delay_minutes == self.test_newshift.maximum_clockout_delay_minutes, True, 'maximum_clockout_delay_minutes must be equal if the shift clockin is not specified')

    def test_clockin_rule_greater_delta(self):
        # Solo puedes hacer clockin despues de (shift.starting_at - shift.clockin_delta)
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at - timedelta(minutes=self.test_shift.maximum_clockin_delta_minutes+1)

        payload = {
            'shift': self.test_shift.id, #shift start right now 
            'author': self.test_profile_employee.id,
            'started_at': started_at, #starting time - 15minutes of delta + 1 minuto (16 minutos clockin) : 
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400, "No puedes hacer clockin un menuto despues del delta")
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()

        self.assertEquals(count, 0)
    def test_clockin_rule_lesser_delta(self):
        # Solo puedes hacer clockin despues de (shift.starting_at - shift.clockin_delta)
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift.starting_at - timedelta(minutes=self.test_shift.maximum_clockin_delta_minutes)

        payload = {
            'shift': self.test_shift.id, #shift start right now 
            'author': self.test_profile_employee.id,
            'started_at': started_at, #starting time - 15minutes of delta : 
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201, "Puedes hacer clockin antes del tiempo dentro." )
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
   
        self.assertEquals(count, 1)

    def test_clockin_delta_is_null(self):
        url = reverse_lazy('api:me-employees-clockins')

        started_at = self.test_shift_null.starting_at - timedelta(minutes=90) #1hr30min

        payload = {
            'shift': self.test_shift_null.id, #shift start right now and the shift delta is null
            'author': self.test_profile_employee.id,
            'started_at': started_at, #anytime in this case is 1hr30 less than the started time of the shift
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()
        print(response_json)
        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift_null.id,
        ).count()

        print(count)
        self.assertEquals(count, 1) #you will be able to clockin since there is no limitation with the clockins


    def test_clockin_before_shift_ending(self):
        # Si ya el shift empezo, puedo siempre hacer just antes (shift.ending_at) de que termine si pertenezo a los employees de ese shift.

        url = reverse_lazy('api:me-employees-clockins')

        payload = {
            'shift': self.test_shift.id, 
            'author': self.test_profile_employee.id,
            'started_at': self.test_shift.ending_at - timedelta (minutes=5), #outside the timedelta of clockout delay minutes: Ejemplo el shift es de 9am a 5pm y el employee hizo clockin ala 5:01pm
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()
        
        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)


    def test_clockin_after_shift_ending(self):
        # Si ya el shift empezo, puedo siempre hacer just antes (shift.ending_at) de que termine si pertenezo a los employees de ese shift. En el otro caso no podras hacer clockout

        url = reverse_lazy('api:me-employees-clockins')

        payload = {
            'shift': self.test_shift.id, 
            'author': self.test_profile_employee.id,
            'started_at': self.test_shift.ending_at + timedelta (minutes=5), #outside the timedelta of clockout delay minutes: Ejemplo el shift es de 9am a 5pm y el employee hizo clockin ala 5:01pm
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)
        response_json = response.json()
        
        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clockout_no_clockin_past_shift(self):
        # Si ya hice clockin en otro shift y no he hecho clockout, no puedo hacer clockin in este shift.
        url = reverse_lazy('api:me-employees-clockins')

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': timezone.now(),
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()
        print(response.content)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()

        self.assertEquals(count, 1)

        second_shift_starting_at = timezone.now() + timedelta(hours=12)
        second_shift_ending_at = timezone.now() + timedelta(hours=20) 
 
        self.test_second_shift, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': 'OPEN',
                'maximum_clockin_delta_minutes': 5,
                'maximum_clockout_delay_minutes': 5,
                'starting_at': second_shift_starting_at,
                'ending_at': second_shift_ending_at
            },
            employer=self.test_employer)
        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_second_shift,
        )
        payload2 = {
            'shift': self.test_second_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': second_shift_starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload2)
        print(response.content)
        self.assertEquals(response.status_code, 400, 'You are not able to clockin if you didnt clock out the previous shift')
        response_json = response.json()

    def test_clockout_having_clockin_past_shift(self):
        # Si ya hice clockin en otro shift y hice clockout, puedo hacer clockin in este shift.
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': self.test_shift.ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

        
        # second shift clock in 
        second_shift_starting_at = timezone.now() + timedelta(hours=12)
        second_shift_ending_at = timezone.now() + timedelta(hours=20) 
 
        self.test_second_shift, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': second_shift_starting_at,
                'ending_at': second_shift_ending_at
            },
            employer=self.test_employer)
        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_second_shift,
        )
        payload2 = {
            'shift': self.test_second_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': second_shift_starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload2)
        print(response.content)
        self.assertEquals(response.status_code, 201, 'You are able to clockin if you clock out the previous shift')
        response_json = response.json()

    def test_clockout_having_clockin_past_shift(self):
        # Si ya hice clockin en otro shift y hice clockout, puedo hacer clockin in este shift.
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': self.test_shift.ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

        
        # second shift clock in 
        second_shift_starting_at = timezone.now() + timedelta(hours=12)
        second_shift_ending_at = timezone.now() + timedelta(hours=20) 
 
        self.test_second_shift, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': second_shift_starting_at,
                'ending_at': second_shift_ending_at
            },
            employer=self.test_employer)
        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_second_shift,
        )
        payload2 = {
            'shift': self.test_second_shift.id,
            'author': self.test_profile_employee.id,
            'started_at': second_shift_starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload2)
        print(response.content)
        self.assertEquals(response.status_code, 201, 'You are able to clockin if you clock out the previous shift')
        response_json = response.json()
        
    def test_clocking_out_before_delta(self):
        #If there is a clockout_delta (not Null), you can only clock out before the shift.endint_at + clockout_delta.
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        clockout_delta = self.test_shift.maximum_clockout_delay_minutes
        ending_at = self.test_shift.ending_at + timedelta(minutes=clockout_delta)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    def test_clocking_out_after_delta(self):
        #If there is a clockout_delta (not Null), you can only clock out before the shift.endint_at + clockout_delta.
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ClockIn',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            started_at=self.test_shift.starting_at,
            latitude_in=-64,
            longitude_in=10,
            ended_at=None,
        )

        clockout_delta = self.test_shift.maximum_clockout_delay_minutes
        ending_at = self.test_shift.ending_at + timedelta(minutes=clockout_delta)

        payload = {
            'shift': self.test_shift.id,
            'author': self.test_profile_employee.id,
            'ended_at': ending_at,
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 1)

    def test_clocking_out_delta_zero_before(self):
        # If there clockout_delta is 0, i cannot clockout after the shift.ending_at
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift_clockoutdelay_zero,
        )
        payload = {
            'shift': self.test_shift_clockoutdelay_zero.id,
            'author': self.test_profile_employee.id,
            'started_at': self.test_shift_clockoutdelay_zero.starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift_clockoutdelay_zero.id,
        ).count()

        self.assertEquals(count, 1)

        payload = {
            'shift': self.test_shift_clockoutdelay_zero.id,
            'author': self.test_profile_employee.id,
            'ended_at': self.test_shift_clockoutdelay_zero.ending_at - timedelta(minutes=1),
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift_clockoutdelay_zero.id,
        )

        self.assertEquals(clockin.count(), 1)
  
    def test_clocking_out_delta_zero_after(self):
        # If there clockout_delta is 0, i cannot clockout after the shift.ending_at
        url = reverse_lazy('api:me-employees-clockins')

        mixer.blend(
            'api.ShiftEmployee',
            employee=self.test_employee,
            shift=self.test_shift_clockoutdelay_zero,
        )
        payload = {
            'shift': self.test_shift_clockoutdelay_zero.id,
            'author': self.test_profile_employee.id,
            'started_at': self.test_shift_clockoutdelay_zero.starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 201)
        response_json = response.json()

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift_clockoutdelay_zero.id,
        ).count()

        self.assertEquals(count, 1)

        payload = {
            'shift': self.test_shift_clockoutdelay_zero.id,
            'author': self.test_profile_employee.id,
            'ended_at': self.test_shift_clockoutdelay_zero.ending_at + timedelta(minutes=1),
            'latitude_out': -64,
            'longitude_out': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)
        response_json = response.json()
        print(response.content)
        clockin = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift_clockoutdelay_zero.id,
        )


    def test_clocking_only_your_shift(self):
        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_in_shift, _, __ = self._make_shift(
            shiftkwargs={
                'status': SHIFT_STATUS_CHOICES[0][0],
                'maximum_clockin_delta_minutes': 0,
                'maximum_clockout_delay_minutes': 0,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=3)
            },employer=self.test_employer)

        self.test_user_employee2, self.test_employee2,self.test_profile_employee2= self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                stop_receiving_invites=False
            ),
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            )
        )
    
        url = reverse_lazy('api:me-employees-clockins')

        payload = {
            'shift': self.test_in_shift.id, #shift start right now 
            'author': self.test_profile_employee2.id,
            'started_at': starting_at, #starting time - 15minutes of delta : 
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400) #no puedes tomar este shift que no perteneces
        response_json = response.json()
    
    def test_delta_delay_retroactively(self):
        # If those two fields are updated for the company and retroactive == True then we need to update all the upcoming shifts as well, the same properties but in the shifts.
        #open and filled.

        #SHIFTS
        self.test_shift_filled, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': "FILLED",
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': timezone.now(),
                'ending_at': timezone.now() + timedelta(hours=8)
            },
            employer=self.test_employer)    

        self.test_shift_open, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': "OPEN",
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': timezone.now() + timedelta(days=1),
                'ending_at': timezone.now() + timedelta(days=1)
            },
            employer=self.test_employer)       

        self.test_shift_open2, _, __ = self._make_shift(
            venuekwargs={
                'latitude': -64,
                'longitude': 10
            },
            shiftkwargs={
                'status': "OPEN",
                'maximum_clockin_delta_minutes': None,
                'maximum_clockout_delay_minutes': None,
                'starting_at': timezone.now() + timedelta(days=2),
                'ending_at': timezone.now() + + timedelta(days=2)
            },
            employer=self.test_employer)       

        #updating delta and delay
        url_update_delta_delay = reverse_lazy('api:me-employer')
        self.client.force_login(self.test_user_employer)

        payload = {
            'maximum_clockin_delta_minutes': 30,
            'maximum_clockout_delay_minutes': 30,
            'retroactive': True
        }

        response = self.client.put(
            url_update_delta_delay,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')


        url = reverse_lazy('api:me-employer-get-shifts')


        response2 = self.client.get(url, content_type="application/json")
        response_json2 = response.json()
        print(self.test_shift_filled)
        count = Shift.objects.filter(
            maximum_clockin_delta_minutes=30,
            maximum_clockout_delay_minutes=30
        ).count()

        self.assertEquals(
            count,
            6,
            'It must be six shift with 30 delay and delta minutes (3 shifts in the start and 3 inside the function)')

    def test_clockin_not_part_of_the_shift(self):
        url = reverse_lazy('api:me-employees-clockins')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)
        self.test_no_apply, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)


        payload = {
            'shift': self.test_no_apply.id,
            'author': self.test_profile_employee.id,
            'started_at': starting_at,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400)

        count = Clockin.objects.filter(
            employee_id=self.test_employee.id,
            shift_id=self.test_shift.id,
        ).count()
        self.assertEquals(count, 0)

    def test_clockout_not_part_of_the_shift(self):
        #you need to be part of the shift to be able to clockin or clockout
        url = reverse_lazy('api:me-employees-clockins')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)
        self.test_no_apply, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)


        payload = {
            'shift': self.test_no_apply.id,
            'author': self.test_profile_employee.id,
            'started_at': starting_at,
            'latitude_in': -64,
            'longitude_in': 10,
        }

        response = self.client.post(url, data=payload)
        self.assertEquals(response.status_code, 400, "You need to be part of the shift to be able to clockin or clockout")

    
