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

    def test_JobCoreInvite_with_exired_shfit(self):
        
        five_minutes = datetime.timedelta(minutes=5)
        
        user = mixer.blend(User)
        profile = mixer.blend(Profile, user=user)
        employee = mixer.blend(Employee,user=user)
        shift = mixer.blend(Shift)
        for i in range(10):
            jc_invite = mixer.blend(JobCoreInvite, shift=shift)
            jc_invite.shift.starting_at = timezone.now() - five_minutes #expired
            jc_invite.save()
        
        shift_invites = create_shift_invites_from_jobcore_invites(JobCoreInvite.objects.all(), employee);
        self.assertEqual(True, len(shift_invites) == 0)

   
if __name__ == '__main__':
    unittest.main()
    