from api.serializers import clockin_serializer
import unittest, datetime
from django.utils import timezone

class TestCI(unittest.TestCase):

    def test_clockin(self):
        five_minutes = datetime.timedelta(minutes=5)
        sixty_minutes = datetime.timedelta(minutes=60)
        ended_at = timezone.now() + sixty_minutes #the shift ends in one hour
        
        starts_in_five_min = timezone.now() + five_minutes #the shift starts in five min
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, starts_in_five_min, ended_at, None) # no delay allowed
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, starts_in_five_min, ended_at, 4) # only allow 4 minutes delay
        self.assertIsNone(clockin_serializer.validate_clock_in(starts_in_five_min, ended_at, 6)) # allow max 6 min of delay
        
        # 
        started_five_min_ago = timezone.now() - five_minutes #the shift starts in 5 minutes from NOW
        self.assertIsNone(clockin_serializer.validate_clock_in(started_five_min_ago, ended_at, None)) # no delay allowed
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_five_min_ago, ended_at, 1) # 1 early allowed
        self.assertIsNone(clockin_serializer.validate_clock_in(started_five_min_ago, ended_at, 10)) # 10 min early allowed
        
        # 
        started_at = timezone.now() - sixty_minutes #the shift started 60min ago
        ends_in_five_minutes = timezone.now() + five_minutes #the ends in 5 min
        ended_at_ended_five_min_ago = timezone.now() - five_minutes #the ended five minutes ago
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ends_in_five_minutes, None)) # without delay
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ends_in_five_minutes, 70)) # with 70 min delay
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at_ended_five_min_ago, None) # no delay allowed
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at_ended_five_min_ago, 4) # 4 min delay allowed

   
if __name__ == '__main__':
    unittest.main()
    