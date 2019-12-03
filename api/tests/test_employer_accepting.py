from django.test import TestCase, override_settings
from mixer.backend.django import mixer
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift
from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from api.actions.employee_actions import create_default_availablity

ShiftApplication = apps.get_model('api', 'ShiftApplication')

@override_settings(STATICFILES_STORAGE=None)
class EmployerAcceptingEmployee(TestCase, WithMakeUser, WithMakeShift):
 
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
        ending_at = starting_at + timedelta(hours=8)

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=11.50 ),
            employer=self.test_employer)

        self.test_shift_2, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at),
            employer=self.test_employer)

        self.test_shift_3, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at),
            employer=self.test_employer)

        self.test_user_employee, self.test_employee, _ = self._make_user(
            'employee',
            employexkwargs=dict(positions=[self.test_shift.position.id]),
            userkwargs=dict(
                username='employee1',
                email='employee1@testdoma.in',
                is_active=True,
            )
        )


        self.test_application = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_2,
            employee=self.test_employee
        )

        self.test_application2 = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_3,
            employee=self.test_employee
        )

   
    def test_employee_list_of_all_application(self):
        self.client.force_login(self.test_user_employee)

        url = reverse_lazy('api:me-employee-applications')
   

        response = self.client.get(url, content_type="application/json")
        response_json = response.json()

        print(len(response_json))

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        self.assertEquals(len(response_json), 2) #deberia ser dos porque en el set up el employee tiene dos aplicaciones

    def test_employee_application_when_accept(self):
        #Si una persona, la aceptan en un trabajo deben eliminarse toda las aplicaciones que esa persona ha hecho en otro trabajo a la misma hora
        self.client.force_login(self.test_user_employee)
        test_invite = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
            status='PENDING'
        )
        url = reverse_lazy('api:me-employees-get-jobinvites-apply', kwargs=dict(
            id=test_invite.id,
            action="APPLY")
        )

        response = self.client.put(
            url,
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')


        url = reverse_lazy('api:me-employee-applications')
   

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()
        print(len(response_json))
        self.assertEquals(len(response_json), 3, 'It should be 3 application because the employee just apply to one') 

    def test_employer_list_applications(self):
        url = reverse_lazy('api:me-employer-get-applicants')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        response_json = response.json()
        print(response_json)

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')
        
        count = ShiftApplication.objects.filter(
            shift__employer=self.test_employer).count()

        self.assertEquals(len(response_json), count, 'It should be 2 because the employer have to assigned employees') 

    def test_employer_accept_employee_delete_all_same_time(self):
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
            )
        )
        self.client.force_login(self.test_user_employer2)

        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)

        self.test_shift_accept, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=10.5,maximum_allowed_employees=4),
            employer=self.test_employer2)

        self.test_application = mixer.blend(
            'api.ShiftApplication',
            shift=self.test_shift_accept,
            employee=self.test_employee
        )


        url_candidates = reverse_lazy('api:me-employer-update-shift-employees', kwargs=dict(
            id=self.test_shift_accept.id
            )
        )

        payload = {
            'candidates': [],
            'employees': [self.test_employee.id],
        }

        response_shift = self.client.put(url_candidates, data=payload, content_type="application/json")
        
        self.assertEquals(
            response_shift.status_code,
            200,
            'It should return a success response')

        url = reverse_lazy('api:me-employer-get-applicants')

        response = self.client.get(url,content_type="application/json")

        response_json = response.json() # Se borraron todos los shift a ese mismo tiempo
        print(response_json)
        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

    def test_shift_manual_invite_no_autorization(self):
        position = mixer.blend('api.Position')

        self.test_user_employee2, self.test_employee2, _ = self._make_user(
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
                username='employee2',
                email='employee2@testdoma.in',
                is_active=True,
            )
        )
        starting_at = timezone.now() + timedelta(days=1)
        ending_at = starting_at + timedelta(hours=8)

        self.test_shiftt, _, __ = self._make_shift(
            shiftkwargs=dict(status='OPEN', starting_at=starting_at, ending_at=ending_at, minimum_hourly_rate=15,maximum_allowed_employees=4, position=position),
            employer=self.test_employer)
        test_shift_invite = mixer.blend(
            'api.ShiftInvite',
            sender=self.test_profile_employer,
            shift=self.test_shiftt,
            employee=self.test_employee2,
            manually_created = True,
            status='PENDING'
        )

        self.client.force_login(self.test_user_employee2)

        url_apply_shift = reverse_lazy("api:me-employees-get-jobinvites-apply", kwargs=dict(
            id=test_shift_invite.id, action="APPLY"))
        payload = {
            'shifts': test_shift_invite.id,
            'employee': self.test_employee2.id,
        }
        response = self.client.put(
            url_apply_shift,
            data=payload,
            content_type="application/json")

        response_json = response.json()

        self.assertEquals(
            response.status_code,
            200,
            'It should return an 200 because is approved')
        self.assertEquals(
            response_json,
            {'details': 'Your application was automatically approved because you were hand-picked for this shift.'})       