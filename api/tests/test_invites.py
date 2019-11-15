from django.test import TestCase
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from api.utils import notifier


class InvitesTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for Invites
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

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

            
        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at),
            employer=self.test_employer)
            
        self.test_shift2, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate = 10),
            employer=self.test_employer)
        self.test_shift3, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_allowed_rating = 3),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                positions=[self.test_shift.position.id],
                minimum_hourly_rate = 8,
                rating=2,
                stop_receiving_invites=True,
                maximum_job_distance_miles= 30
            ),
            profilekwargs = dict(

            )
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )



    def test_employee_stop_receiving_invites_ON(self):
        # not reciving invites
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the talent is not accepting invites but there are'+str(talents))
       
    def test_shifts_minimum_hourly_rate_greater_employee(self):
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift2)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the shift offer higher hourly rate than the employee minimum hourly rate')


    def test_shift_minimum_allowed_rating(self):
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift3)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the shift have higher rating')
    
    def test_shift_further_employee_address(self):
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
            float(response_json['latitude']), float(venue.latitude))

        self.assertEquals(
            float(response_json['longitude']), float(venue.longitude))
