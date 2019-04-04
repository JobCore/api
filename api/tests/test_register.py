from api.models import JobCoreInvite, ShiftInvite
from api.serializers.auth_serializer import create_shift_invites_from_jobcore_invites
import pytest, datetime
from rest_framework.test import APITestCase, APIRequestFactory
from django.utils import timezone
from mixer.backend.django import mixer
from django.contrib.auth.models import User
from api.models import Employee, Shift, JobCoreInvite, Profile

@pytest.mark.django_db
class TestRegister(APITestCase):
    
    @classmethod
    def setUpClass(self):
        super(TestRegister, self).setUpClass()
        
        self.user = mixer.blend(User)
        self.profile = mixer.blend(Profile, user=self.user)
        self.employee = mixer.blend(Employee,user=self.user)

        five_minutes = datetime.timedelta(minutes=5)
        self.shifts_expired = [ 
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() - five_minutes)
        ];
        self.shifts_not_expired = [ 
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes),
            mixer.blend(Shift, starting_at = timezone.now() + five_minutes)
        ];
        
    def test_Sync_invites_with_exired_shfit(self):
        
        mixer.blend(JobCoreInvite,shift=self.shifts_expired[0],email=self.user.email)
        mixer.blend(JobCoreInvite,shift=self.shifts_expired[1],email=self.user.email)
        
        shift_invites = create_shift_invites_from_jobcore_invites(JobCoreInvite.objects.filter(email=self.user.email).all(), self.employee);
        self.assertEqual(0, len(shift_invites))
        self.assertEqual(True, len(JobCoreInvite.objects.filter(email=self.user.email).all()) == 0)
        
    def test_Sync_invites_with_not_exired_shfit(self):
        
        mixer.blend(JobCoreInvite,shift=self.shifts_not_expired[0],email=self.user.email)
        mixer.blend(JobCoreInvite,shift=self.shifts_not_expired[1],email=self.user.email)
        
        shift_invites = create_shift_invites_from_jobcore_invites(JobCoreInvite.objects.filter(email=self.user.email).all(), self.employee);
        self.assertEqual(2, len(shift_invites))
        self.assertEqual(True, len(JobCoreInvite.objects.filter(email=self.user.email).all()) == 0)
        
if __name__ == '__main__':
    unittest.main()
    