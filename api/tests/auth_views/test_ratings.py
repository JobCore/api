from django.test import TestCase, override_settings
from mixer.backend.django import mixer
import json
from django.urls import reverse_lazy
from api.tests.mixins import WithMakeUser, WithMakeShift

@override_settings(STATICFILES_STORAGE=None)
class EmployeeRatingTestSuite(TestCase, WithMakeUser, WithMakeShift):
    """
    Endpoint tests for Rating
    @revisionNeeded
    """

    def setUp(self):
        position = mixer.blend('api.Position')
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
                positions=[position.id]
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

        self.test_shift, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=self.test_shift,
            author=self.test_profile_employee,
            status='APPROVED'
        )

    def test_all_get_ratings(self):
        """
        Gets ratings
        """

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=self.test_shift,
            employer=self.test_employer,
        )

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
        )

        url = reverse_lazy('api:get-ratings')

        self.client.force_login(self.test_user_employer)

        response = self.client.get(url, content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 2)

    # @expectedFailure
    def test_post_rating_employee(self):
        """
        Gets ratings
        """
        
        position = mixer.blend('api.Position')
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('comments', response_json)
        self.assertIn('shift', response_json)
        self.assertIn('id', response_json)
        self.assertIn('rating', response_json)

        self.test_employer.refresh_from_db()

        self.assertEquals(float(self.test_employer.rating), 4)
        self.assertEquals(self.test_employer.total_ratings, 1)

        new_shift, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=new_shift,
            author=self.test_profile_employee,
            status='APPROVED'
        )

        payload = {
            'employer': self.test_employer.id,
            'rating': 2,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('comments', response_json)
        self.assertIn('shift', response_json)
        self.assertIn('id', response_json)
        self.assertIn('rating', response_json)

        self.test_employer.refresh_from_db()

        self.assertEquals(float(self.test_employer.rating), 3)
        self.assertEquals(self.test_employer.total_ratings, 2)

    def test_post_rating_employee_with_multipleshifts(self):
        """
        Gets ratings
        """
        
        position = mixer.blend('api.Position')
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        new_shift1, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)
        new_shift2, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)
        new_shift3, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=new_shift1,
            author=self.test_profile_employee,
            status='APPROVED'
        )
        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=new_shift2,
            author=self.test_profile_employee,
            status='APPROVED'
        )
        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=new_shift3,
            author=self.test_profile_employee,
            status='APPROVED'
        )

        payload = [{
                'employee': self.test_employee.id,
                'shifts': [new_shift1.id,new_shift2.id,new_shift3.id],
                'rating': 3.5,
                'comments': "ratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingratingrating"
        }]
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")
        print(
            response.json()
        )
        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('comments', response_json[0])
        self.assertIn('shift', response_json[0])
        self.assertIn('id', response_json[0])
        self.assertIn('rating', response_json[0])

        self.assertIn('comments', response_json[1])
        self.assertIn('shift', response_json[1])
        self.assertIn('id', response_json[1])
        self.assertIn('rating', response_json[1])

        self.assertIn('comments', response_json[2])
        self.assertIn('shift', response_json[2])
        self.assertIn('id', response_json[2])
        self.assertIn('rating', response_json[2])

       

    def test_post_rating_employer(self):
        """
        Gets ratings
        """

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet jlkasdlkas dalsdjikn asdljskb adlajksdasd ljkadsl;k asdiljkdsilsdkja '
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        #print(response.content)
        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response.')

        response_json = response.json()

        self.assertIn('comments', response_json)
        self.assertIn('shift', response_json)
        self.assertIn('id', response_json)
        self.assertIn('rating', response_json)

        self.test_employee.refresh_from_db()

        self.assertEquals(float(self.test_employee.rating), 4)
        self.assertEquals(self.test_employee.total_ratings, 1)

    def test_post_double_rating(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet lkjdfsdklfjn dfildjkfjsdlkfm skldfjsnmd flijksdfiokjlsdfn sidfoklsdnf sjdfks'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response: {str(response.content)}')

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return a success response: {str(response.content)}')

    def test_rate_without_clocking_in(self):
        """
        Gets ratings
        """
        position = mixer.blend('api.Position')
        new_shift, *_ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)
        new_shift.save()

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_integer(self, *a):
        """
        Gets ratings
        """
        position = mixer.blend('api.Position')
        new_shift, *_ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_num_out_of_range(self, *a):
        """
        Gets ratings
        """
        position = mixer.blend('api.Position')
        new_shift, *_ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 9,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_get_ratings_filter_employee(self):
        """
        Gets ratings
        """
        position = mixer.blend('api.Position')
        new_shift, *_ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=self.test_shift,
            employer=self.test_employer,
        )
        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employee,
            shift=new_shift,
            employer=self.test_employer,
        )

        mixer.blend(
            'api.Rate',
            sender=self.test_profile_employer,
            shift=self.test_shift,
            employee=self.test_employee,
        )

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        response = self.client.get(
            url,
            data=dict(employee=self.test_employee.id),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()
        print(response_json)
        self.assertEquals(len(response_json), 1)

        response = self.client.get(
            url,
            data=dict(employer=self.test_employer.id),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 2)

        response = self.client.get(
            url,
            data=dict(shift=new_shift.id),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            200,
            'It should return a success response')

        response_json = response.json()

        self.assertEquals(len(response_json), 1)

    def test_rate_talentxtalent(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employee': self.test_employee.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_employerxemployer(self):
        """
        Gets ratings
        """
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': self.test_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')

    def test_rate_another_shift(self):
        """
        Gets ratings
        """
        position = mixer.blend('api.Position')
        _, new_employer, __ = self._make_user(
            'employer',
            userkwargs=dict(
                username='employerx1',
                email='employerx@testdoma.in',
                is_active=True,
            ),
            employexkwargs=dict(
                rating=0,
                total_ratings=0,
            )
        )

        newshift, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employer)

        payload = {
            'employer': self.test_employer.id,
            'rating': 4,
            'shift': newshift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            400,
            'It should return an error response')




    def test_update_rating_totalrating_when_rate(self):
        position = mixer.blend('api.Position')
        url = reverse_lazy('api:get-ratings')
        self.client.force_login(self.test_user_employee)

        payload = {
            'employer': self.test_employer.id,
            'rating': 3,
            'shift': self.test_shift.id,
            'comments': 'good employer'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()
        
        self.assertIn('rating', response_json)

        self.test_employer.refresh_from_db()

        self.assertEquals(float(self.test_employer.rating), 3)
        self.assertEquals(self.test_employer.total_ratings, 1)

        new_shift, _, __ = self._make_shift(
            shiftkwargs=dict(position=position), employer=self.test_employer)

        mixer.blend(
            'api.Clockin',
            employee=self.test_employee,
            shift=new_shift,
            author=self.test_profile_employee,
            status='APPROVED'
        )

        payload = {
            'employer': self.test_employer.id,
            'rating': 2,
            'shift': new_shift.id,
            'comments': 'Lorem ipsum dolor sit amet'
        }
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json")

        self.assertEquals(
            response.status_code,
            201,
            'It should return a success response')

        response_json = response.json()

        self.assertIn('rating', response_json)

        self.test_employer.refresh_from_db()

        self.assertEquals(float(self.test_employer.rating), 2.5)
        self.assertEquals(self.test_employer.total_ratings, 2)