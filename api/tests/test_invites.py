from django.test import TestCase, override_settings
from django.urls.base import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from mixer.backend.django import mixer
from api.models import SHIFT_STATUS_CHOICES
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from api.utils import notifier
from api.actions.employee_actions import create_default_availablity

AvailabilityBlock = apps.get_model('api', 'AvailabilityBlock')
@override_settings(STATICFILES_STORAGE=None)
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
 
        # starting_at = timezone.now() + timedelta(days=1)
        # ending_at = starting_at + timedelta(minutes=90)
        
        
        # self.test_shift, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at),
        #     employer=self.test_employer)

        # self.test_shift_with_rating_rate, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
        #     employer=self.test_employer)            
        # self.test_shift_min_rate_10, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate = 10),
        #     employer=self.test_employer)

        # self.test_shift4, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at),
        #     venuekwargs=dict(latitude=25, longitude=-80),
        #     employer=self.test_employer)

        # self.test_shift3, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_allowed_rating  = 3),
        #     employer=self.test_employer)

        # self.test_shift5, _, __ = self._make_shift(
        #     shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_allowed_rating  = 3),
        #     employer=self.test_employer)


    def test_employee_stop_receiving_invites_ON(self):
        # not reciving invites
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_stop_receiving_invites_ON, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                stop_receiving_invites=True,
                positions=[position.id],
                maximum_job_distance_miles= 15
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

        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_stop_receiving_invites_ON)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the talent is not accepting invites but there are')

    def test_employee_stop_receiving_invites_OFF(self):
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_stop_receiving_invites_OFF, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                positions=[position.id],
                stop_receiving_invites=False,
                maximum_job_distance_miles= 15
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
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_stop_receiving_invites_OFF)
        self.assertEquals(len(talents) > 0, True, 'There should be more than 0 invites because the talent is accepting invites')


    def test_shifts_minimum_hourly_rate_lesser_employee(self):
        # An employee cannot receive invites from shifts.minimum_hourly_rate that pay less than its employee. minimum_hourly_rate
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_minimum_hourly_rate_lesser_employee, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=9, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 10,
                positions=[position.id],
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        talents = []

        talents = notifier.get_talents_to_notify(self.test_shift_minimum_hourly_rate_lesser_employee)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the minimum shifts minimum hourly rate is lesser than employee')

    def test_shifts_minimum_hourly_rate_greater_employee(self):
        # An employee can  receive invites from shifts.minimum_hourly_rate that pay greater than its employee. minimum_hourly_rate
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_minimum_hourly_rate_greater_employee, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                positions=[position.id],
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        talents = []

        talents = notifier.get_talents_to_notify(self.test_shift_minimum_hourly_rate_greater_employee)
        self.assertEquals(len(talents) > 0, True, 'There should be 1 invites because the minimum shifts minimum hourly rate is greater than employee')


    def test_shift_minimum_allowed_rating_greater_employee(self):
        # An employee cannot receive invites from shifts were shift.minimum_allowed_rating is bigger than employee.rating
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_minimum_hourly_rate_greater_employee, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 3  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                rating= 1,
                total_ratings=1,
                positions=[position.id],
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_minimum_hourly_rate_greater_employee)
        self.assertEquals(len(talents) == 0, True, 'There should be 0 invites because the shift have higher rating')

    def test_shift_minimum_allowed_rating_lesser_employee(self):
        # An employee can receive invites from shifts were shift.minimum_allowed_rating is smaller than employee.rating
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_minimum_hourly_rate_lesser_employee, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 3  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                rating= 5,
                total_ratings=5,
                positions=[position.id],
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_minimum_hourly_rate_lesser_employee)
        self.assertEquals(len(talents) > 0, True, 'There should be 1 invites because the shift have smaller rating')
    





    # def test_shift_further_employee_address(self):
    #     #An employee cannot receive invites from shifts located (venue.latitude, venue.longitude) further than employee.maximum_job_distance_miles from the employee address (profile.latitude, profile.longitud).
    #     position = mixer.blend('api.Position')

    #     starting_at = timezone.now() + timedelta(days=1)
    #     ending_at = starting_at + timedelta(minutes=90)

    #     self.test_shift_further_employee_address, _, __ = self._make_shift(
    #         shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 3  ),
    #         venuekwargs=dict(latitude=40, longitude=-73), #Brooklyn New York Lat/Long
    #         employer=self.test_employer)        
        
    #     self.test_user_employee, self.test_employee, _ = self._make_user(
    #         'employee',
    #         employexkwargs=dict(
    #             maximum_job_distance_miles= 30,
    #             positions=[position.id],         
    #         ),
    #         profilekwargs = dict( #Coral Gable Lat/Long
    #             latitude = 25, 
    #             longitude = -80
    #         ),
    #         userkwargs=dict(
    #             username='employee1',
    #             email='employee1@testdoma.in',
    #             is_active=True,
    #         )
    #     )
    #     talents = []
    #     talents = notifier.get_talents_to_notify(self.test_shift_further_employee_address)
    #     self.assertEquals(len(talents) == 0, True, 'Venue location is farther than the employee address so the shift invite cannot be delivered')


    # def test_shift_near_employee_address(self):
    #     #An employee cannot receive invites from shifts located (venue.latitude, venue.longitude) further than employee.maximum_job_distance_miles from the employee address (profile.latitude, profile.longitud).
    #     position = mixer.blend('api.Position')

    #     starting_at = timezone.now() + timedelta(days=1)
    #     ending_at = starting_at + timedelta(minutes=90)

    #     self.test_shift_further_employee_address, _, __ = self._make_shift(
    #         shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 3  ),
    #         venuekwargs=dict(latitude=40, longitude=-73),
    #         employer=self.test_employer)        
        
    #     self.test_user_employee, self.test_employee, _ = self._make_user(
    #         'employee',
    #         employexkwargs=dict(
    #             maximum_job_distance_miles= 30,
    #             positions=[position.id],         
    #         ),
    #         profilekwargs = dict(
    #             latitude = 40,
    #             longitude = -73
    #         ),
    #         userkwargs=dict(
    #             username='employee1',
    #             email='employee1@testdoma.in',
    #             is_active=True,
    #         )
    #     )
    #     talents = []
    #     talents = notifier.get_talents_to_notify(self.test_shift_further_employee_address)
    #     self.assertEquals(len(talents) > 0, True, 'Venue location is nearer than the employee address so the shift invite can be delivered')

    def test_shifts_position_not_included_employee_position(self):
        # An employee cannot receive invites from shifts were shift.position is not included in employee.positions.

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                # stop_receiving_invites=True,
                maximum_job_distance_miles= 15
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

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_position, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)
             
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_position)
        self.assertEquals(len(talents) == 0, True, 'Employee cannot recieve invites from shifts were shift.position is not included in the employee positions')

    def test_shifts_position_included_employee_position(self):
        # An employee cannot receive invites from shifts were shift.position is not included in employee.positions.
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_position, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                positions=[position.id],
                stop_receiving_invites=False,
                maximum_job_distance_miles= 15
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
            
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_position)
        self.assertEquals(len(talents) > 0, True, 'Employee should receive invite from shift because shift.position is included in the employee positions')


    def test_shift_not_in_availability_block_allday(self):
        # An employee cannot receive invites from shifts that occur (shift.starting_at, shift.ending_at) outside of its availability blocks (employee.availabilit_block_set).
        position = mixer.blend('api.Position')
        shift_starting_at = timezone.now() + timedelta(days=1)
        shift_ending_at = shift_starting_at + timedelta(minutes=90)
        # employee_available_starting_at = shift_starting_at
        # employee_available_ending_at = shift_ending_at

        self.test_shift_availability_block, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=shift_starting_at, ending_at=shift_ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)
            
        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
                positions=[position.id],                
            )
        )
        mixer.blend('api.AvailabilityBlock', employee=self.test_employee, starting_at=shift_starting_at, ending_at = shift_ending_at, allday=True)

        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_availability_block)
        self.assertEquals(len(talents) == 0, True, 'Employee can get invite if the employee starting at is lesser than shift starting at or the employee ending at is greater than the shift endingt at ') 
    
    def test_shift_not_in_availability_block_allday(self):
        # An employee cannot receive invites from shifts that occur (shift.starting_at, shift.ending_at) outside of its availability blocks (employee.availabilit_block_set).
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_availability, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=11.50, minimum_allowed_rating = 0  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                positions=[position.id],
                stop_receiving_invites=False,
                maximum_job_distance_miles= 15
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
        mixer.blend('api.AvailabilityBlock', employee=self.test_employee, starting_at=starting_at - timedelta(minutes=180), ending_at = ending_at - timedelta(minutes=90), allday=True)

        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_availability)
        self.assertEquals(len(talents) > 0, True, 'There should be more than 0 invites because the talent is accepting invites')
    def test_shift_same_time_applied_other_shift(self):
       # An employee cannot receive invites from shifts that occur (shift.starting_at, shift.ending_at) at within the time that other shifts were the employee is already an employee of.
        position = mixer.blend('api.Position')

        starting_at = timezone.now()
        ending_at = starting_at + timedelta(minutes=120)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                positions=[position.id],
                stop_receiving_invites=False,
                maximum_job_distance_miles= 15
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
        #this in range of the shift  
        self.test_shift_pending_inrange, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at - timedelta(minutes=15),  ending_at=ending_at, position=position, minimum_hourly_rate=10, minimum_allowed_rating = 1  ),
            employer=self.test_employer)

        self.test_shift_accepted_employees, _, __ = self._make_shift(
            shiftkwargs=dict(
                employees=self.test_employee,
                status='OPEN', 
                starting_at=starting_at, 
                ending_at=ending_at, 
                position=position, 
                minimum_hourly_rate=11.50, 
                minimum_allowed_rating = 0  ),
                employer=self.test_employer,
            )
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_pending_inrange)
        self.assertEquals(len(talents) == 0, True, 'There should be more than 0 invites because the talent is accepting invites within the same timeframe') 

    def test_shift_same_time_applied_other_shift(self):
       # An employee cannot receive invites from shifts that occur (shift.starting_at, shift.ending_at) at within the time that other shifts were the employee is already an employee of.
        position = mixer.blend('api.Position')

        starting_at = timezone.now()
        ending_at = starting_at + timedelta(minutes=120)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 9,
                rating=5,
                positions=[position.id],
                stop_receiving_invites=False,
                maximum_job_distance_miles= 15
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
        #this one available to be sent because is outside the range of the applied shift
        self.test_shift_pending_outrange, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at - timedelta(minutes=125),  ending_at=starting_at - timedelta(minutes=5), position=position, minimum_hourly_rate=10, minimum_allowed_rating = 1  ),
            employer=self.test_employer)

        self.test_shift_accepted_employees, _, __ = self._make_shift(
            shiftkwargs=dict(
                employees=self.test_employee,
                status='OPEN', 
                starting_at=starting_at, 
                ending_at=ending_at, 
                position=position, 
                minimum_hourly_rate=11.50, 
                minimum_allowed_rating = 0  ),
                employer=self.test_employer,
            )
        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_pending_outrange)
        self.assertEquals(len(talents) > 0, True, 'There should be more than 0 invites because the talent is accepting invites outside the same timeframe') 

    def test_limitation_for_employees_in_favoritelist(self):
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift_favlist, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=9, minimum_allowed_rating = 3  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 10,
                rating=1,
                positions=[position.id],
                stop_receiving_invites=False,
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
    
        mixer.blend(
            'api.FavoriteList',
            employer=self.test_employer,
            auto_accept_employees_on_this_list=True,
            employees=[self.test_employee]
        )

        talents = []
        talents = notifier.get_talents_to_notify(self.test_shift_favlist)
        self.assertEquals(len(talents) == 0, True, 'There should be more than 0 invites because the only favorite employe dont pass any of the requierement') 

    def test_shift_manual_invite_no_limitation(self):
        #MANUAL INVITE    
        position = mixer.blend('api.Position')

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(minutes=90)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, position=position, minimum_hourly_rate=9, minimum_allowed_rating = 3  ),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(
                minimum_hourly_rate = 10,
                rating=1,
                positions=[position.id],
                stop_receiving_invites=False,
            ),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )
        url = reverse_lazy('api:me-employer-get-jobinvites')
        self.client.force_login(self.test_user_employer)
        create_default_availablity(self.test_employee)
        payload = {
            'shifts': self.test_shift.id,
            'employee': self.test_employee.id,
        }

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return an 201 because manual invite will be sent with or without requirements')