import pytest
from api.models import *
from api.views import *
from mixer.backend.django import mixer
from rest_framework.test import APITestCase, APIRequestFactory
from unittest import skip


@skip
@pytest.mark.django_db
class TestModels(APITestCase):
    @classmethod
    def setUpClass(cls):
        super(TestModels, cls).setUpClass()
        cls.factory = APIRequestFactory()
        # Create Users
        cls.user = mixer.blend(User)
        # Basic models
        cls.badge = mixer.blend('api.Badge')
        cls.position = mixer.blend('api.Position')
        cls.venue = mixer.blend('api.Venue')
        cls.shift = mixer.blend('api.Shift')
        cls.profile = mixer.blend(
            'api.Profile', user=cls.user)
        cls.employer = mixer.blend(
            'api.Employer', user=cls.profile.user)
        cls.employee = mixer.blend(
            'api.Employee', user=cls.profile.user)
        cls.favlist = mixer.blend('api.FavoriteList', owner=cls.employer)

    def test_position_str(self):
        assert self.position.__str__() == self.position.title

    def test_badge_str(self):
        assert self.badge.__str__() == self.badge.title

    def test_profile_str(self):
        assert self.profile.__str__() == self.profile.user.username

    # def test_employer_str(self):
    #     assert self.employer.__str__() == self.profile.employer.title

    def test_employee_str(self):
        assert self.employee.__str__() == self.profile.user.email

    def test_favorite_list_str(self):
        assert self.favlist.__str__() == self.favlist.title

    def test_venue_str(self):
        assert self.venue.__str__() == self.venue.title

    def test_shift_str(self):
        name = "{} at {} on {}".format(
            self.shift.position.title, self.shift.venue.title, self.shift.starting_at)
        assert self.shift.__str__() == name
