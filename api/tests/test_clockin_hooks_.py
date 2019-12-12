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
ShiftInvite = apps.get_model('api', 'ShiftInvite')
ShiftApplication = apps.get_model('api', 'ShiftApplication')


@override_settings(STATICFILES_STORAGE=None)
class HookTestClockinHooks(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for Invites
    """
    def setUp(self):
        position = mixer.blend('api.Position')

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

        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                stop_receiving_invites=True,
                positions=[position.id],
                maximum_job_distance_miles= 20
            ),
            profilekwargs = dict(
                latitude = 40,
                longitude = -73
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        (
            self.test_user_employee2,
            self.test_employee2,
            self.test_profile_employee2
        ) = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                stop_receiving_invites=True,
                positions=[position.id],
                maximum_job_distance_miles= 20
            ),
            profilekwargs = dict(
                latitude = 40,
                longitude = -73
            ),
            userkwargs=dict(
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            )
        )


        self.test_shift_with_no_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(days=3), ending_at=timezone.now() + timedelta(hours=8) - timedelta(days=3), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes=None, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        # mixer.blend(
        #         'api.Clockin',
        #         employee=self.test_employee,
        #         shift=self.test_shift_with_delay,
        #         author=self.test_profile_employee,
        #         ended_at=None,
        #         starting_at= timezone.now()- timedelta(days=3)
        #     )

        # mixer.blend(
        #         'api.Clockin',
        #         employee=self.test_employee,
        #         shift=self.test_shift_with_no_delay,
        #         author=self.test_profile_employee,
        #         ended_at=None,
        #         starting_at= timezone.now()- timedelta(days=3)
        #     )
        # mixer.blend(
        #     'api.ShiftInvite',
        #     sender=self.test_profile_employer,
        #     shift=self.test_shift_with_delay,
        #     employee=self.test_employee2
        # )
        self.client.force_login(self.test_user_employee)

    def test_expired_all_shifts_that_delay_hast_passed(self):
        position = mixer.blend('api.Position')
        self.test_shift_with_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=16), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        print(response.content)
        self.assertEquals(response.status_code, 200)
   
        _shift = Shift.objects.get(id=self.test_shift_with_delay.id)
        self.assertEquals(_shift.status == "EXPIRED", True, "The shift must have been set as EXPIRED because it ended 16 minutes ago")

    def test_expired_shifts_with_delay_none_and_no_pending_clockouts(self):
        position = mixer.blend('api.Position')
        self.test_shift_with_no_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=16), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= None, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        print(response.content)
        self.assertEquals(response.status_code, 200)
   
        _shift = Shift.objects.get(id=self.test_shift_with_no_delay.id)
        self.assertEquals(_shift.status == "EXPIRED", True, "The shift must have been set as EXPIRED because it ended, delay is None and no one is missing clockout")

    def test_expired_shifts_with_delay_none_but_with_pending_clockouts(self):
        position = mixer.blend('api.Position')
        self.test_shift_with_no_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=16), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= None, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        mixer.blend(
                'api.Clockin',
                employee=self.test_employee,
                shift=self.test_shift_with_no_delay,
                author=self.test_profile_employee,
                ended_at=None,
                starting_at= timezone.now()- timedelta(hours=1)
            )

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        print(response.content)
        self.assertEquals(response.status_code, 200)
   
        _shift = Shift.objects.get(id=self.test_shift_with_no_delay.id)
        self.assertEquals(_shift.status == "OPEN", True, "The shift must have been set as OPEN because it ended, delay is None BUT someone is missing clockout")
        
    def test_expired_shifts_with_delay_diff_None_clockin_close(self):
        position = mixer.blend('api.Position')
        self.test_shift_with_no_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=15), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        clockin= mixer.blend(
                'api.Clockin',
                employee=self.test_employee,
                shift=self.test_shift_with_no_delay,
                author=self.test_profile_employee,
                ended_at=None,
                starting_at= timezone.now()- timedelta(hours=2)
            )

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
       
        self.assertEquals(response.status_code, 200)
      
        _clockout = Clockin.objects.get(employee_id=self.test_employee.id)
      
        self.assertEquals(_clockout.ended_at != None, True, "Se deberia cerrar los clockin que exceed el ending mas delta")
            
    def test_shiftsinvites_with_expired_time_to(self):
        position = mixer.blend('api.Position')
        self.test_shift_with_delay, _, __ = self._make_shift(
            shiftkwargs=dict(status='EXPIRED', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=16), position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            maximum_clockin_delta_minutes=15, maximum_clockout_delay_minutes= 15, maximum_allowed_employees = 5, employees=self.test_employee),
            employer=self.test_employer)

        _inv = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift_with_delay,
            employee=self.test_employee,
            status="PENDING"
        )

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        shift_invite = ShiftInvite.objects.get( id=_inv.id)
        print(shift_invite)
        self.assertEquals(response.status_code, 200)
   
        # _shiftinvite = ShiftInvite.objects.get(id=self.test_shift_with_delay.id)
        self.assertEquals(shift_invite.status == "EXPIRED", True, "The shift invitte must have been set as EXPIRED because it has a expired shift")

    def test_delete_shift_application_with_expired_shift(self):
        self.test_shift_expired, _, __ = self._make_shift(
            shiftkwargs=dict(status='EXPIRED', starting_at=timezone.now() - timedelta(hours=2), ending_at=timezone.now() - timedelta(minutes=15)),
            employer=self.test_employer)
        self.test_shift_completed, _, __ = self._make_shift(
            shiftkwargs=dict(status='COMPLETED', starting_at=timezone.now() - timedelta(hours=3), ending_at=timezone.now() - timedelta(minutes=15)),
            employer=self.test_employer)
        self.test_shift_cancelled, _, __ = self._make_shift(
            shiftkwargs=dict(status='CANCELLED', starting_at=timezone.now() - timedelta(hours=4), ending_at=timezone.now() - timedelta(minutes=15)),
            employer=self.test_employer)

        self.test_application_expired = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_expired,
            employee=self.test_employee
        )
        self.test_application_completed = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_completed,
            employee=self.test_employee
        )
        self.test_shift_cancelled = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_cancelled,
            employee=self.test_employee
        )
        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        self.assertEquals(response.status_code, 200)
        #self.assertEquals(response_json, [], "All shift application must be deleted if they are completed, cancelled or expired")