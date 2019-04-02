from api.utils.notifier import notify_invite_accepted
from api.models import JobCoreInvite
import pytest, datetime
from rest_framework.test import APITestCase, APIRequestFactory
from django.utils import timezone
from mixer.backend.django import mixer
from django.test import override_settings

@pytest.mark.django_db
@override_settings(STATICFILES_STORAGE=None)
@override_settings(EMAIL_NOTIFICATIONS_ENABLED=False)
class TestInvites(APITestCase):

    def test_JobCoreInvite_accepted(self):
        invite = mixer.blend('api.JobCoreInvite')
        self.assertEqual(True, notify_invite_accepted(invite))

   
if __name__ == '__main__':
    unittest.main()
    