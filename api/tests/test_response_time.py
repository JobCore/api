from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta, datetime
from django.apps import apps
import pytz

Employer = apps.get_model('api', 'Employer')
Employee = apps.get_model('api', 'Employee')
Profile = apps.get_model('api', 'Profile')
ShiftInvite = apps.get_model('api', 'ShiftInvite')

@override_settings(STATICFILES_STORAGE=None)
class ResponseTime(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for clockinout
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



   
    
        self.client.force_login(self.test_user_employer)

    def test_response_time_formula(self):
        #Si a un employee lo aceptan en un trabajo deben eliminarse las otras aplicaciones con el mismo tiempo del trabajo aceptado. Deben recibir una notification de que han sido eliminada
        #enhancement has not been made
        position = mixer.blend('api.Position')
        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)
        (
            self.test_user_employee,
            self.test_employee,
            self.test_profile_employee
        ) = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                maximum_job_distance_miles= 25,
                response_time = 30,
                total_invites = 5,
                positions=[position.id]
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_invite = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
            status='PENDING',
        )
        
        self.client.force_login(self.test_user_employee)

        urlAPPLY = reverse_lazy('api:me-employees-get-jobinvites-apply', kwargs=dict(
            id=self.test_invite.id,
            # responded_at= responding_at,
            action="APPLY"
        )
        )
        responseAPPLY = self.client.put(
            urlAPPLY,
            content_type="application/json")

        self.assertEqual(ShiftInvite.objects.filter(employee=self.test_employee, status__in=['APPLIED', 'REJECTED','EXPIRED']).count(), 1)
        new_response_time = ((self.test_employee.response_time * self.test_employee.total_invites)+self.test_invite.responded_at)/(self.test_employee.total_invites + 1)

        self.assertEquals(
            responseAPPLY.status_code,
            200,
            'It should return a success response, because the employee is applying')
        #new response time calculator
        self.assertEquals(new_response_time, self.test_employee.response_time, "the new response time should be the same as the current resposne time because when a employee clicks apply or reject to a shift the response time must be updated")

    def test_update_responsetime(self):
            position = mixer.blend('api.Position')
            starting_at = timezone.now() + timedelta(days=1)
            ending_at = starting_at + timedelta(hours=8)
            (
                self.test_user_employee,
                self.test_employee,
                self.test_profile_employee
            ) = self._make_user(
                'employee',
                employexkwargs=dict(
                    minimum_hourly_rate = 9,
                    rating=5,
                    maximum_job_distance_miles= 25,
                    response_time = 30,
                    total_invites = 5,
                    positions=[position.id]
                ),
                userkwargs=dict(
                    username='employee1',
                    email='employee1@testdoma.in',
                    is_active=True,
                )
            )

            self.test_shift, _, __ = self._make_shift(
                shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
                employer=self.test_employer)

            self.test_invite = mixer.blend(
                'api.ShiftInvite',
                sender=self.test_profile_employer,
                shift=self.test_shift,
                employee=self.test_employee,
                status='PENDING',
            )
            
            self.client.force_login(self.test_user_employee)

            urlAPPLY = reverse_lazy('api:me-employees-get-jobinvites-apply', kwargs=dict(
                id=self.test_invite.id,
                # responded_at= responding_at,
                action="APPLY"
            )
            )
            responseAPPLY = self.client.put(
                urlAPPLY,
                content_type="application/json")

            self.assertEquals(self.test_invite.responded_at, timezone.now(), "The responded at of the shift that the athlete just apply or reject must be updated to the current time.")
           
            self.assertEquals(
            responseAPPLY.status_code,
            200,
            'It should return a success response, because the employee is applying')

    def test_expired_shift_update_response_time(self):
        position = mixer.blend('api.Position')
            starting_at = timezone.now() + timedelta(days=1)
            ending_at = starting_at + timedelta(hours=8)
            (
                self.test_user_employee,
                self.test_employee,
                self.test_profile_employee
            ) = self._make_user(
                'employee',
                employexkwargs=dict(
                    minimum_hourly_rate = 9,
                    rating=5,
                    maximum_job_distance_miles= 25,
                    response_time = 30,
                    total_invites = 5,
                    positions=[position.id]
                ),
                userkwargs=dict(
                    username='employee1',
                    email='employee1@testdoma.in',
                    is_active=True,
                )
            )

        self.test_invite, _, __ = self._make_shift(
            shiftkwargs=dict(status='EXPIRED', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=15, minimum_allowed_rating = 0, 
            ),
            employer=self.test_employer)

        test_invite = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_invite,
            employee=self.test_employee,
            status="PENDING"
        )

        url = reverse_lazy("api:hook-process-expired-shifts")
        response = self.client.get(
            url,
            content_type="application/json")

        response_json = response.json()
        
        new_response_time = ((self.test_employee.response_time * self.test_employee.total_invites)+self.test_invite.responded_at)/(self.test_employee.total_invites + 1)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.test_employee.total_invites, 6, "The new total must be 6 because one shiftinvite expired and it count as one")
        self.assertEquals(self.test_employee.response_time, new_response_time, "The total response time must be updated")