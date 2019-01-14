from api.serializers import clockin_serializer
import unittest, datetime
from django.utils import timezone

class TestCI(unittest.TestCase):

    def test_clockin(self):
        five_minutes = datetime.timedelta(minutes=5)
        sixty_minutes = datetime.timedelta(minutes=60)
        ended_at = timezone.now() + sixty_minutes
        
        five_minutes_late = timezone.now() + five_minutes
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, five_minutes_late, ended_at, None) # no delay allowed
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, five_minutes_late, ended_at, 4) # only allow 4 minutes delay
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, 6)) # allow max 6 min of delay
        
        # 
        five_minute_early = timezone.now() - five_minutes
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, None)) # no delay allowed
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, 1) # 1 early allowed
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, 10)) # 10 min earaly allowed
        
        # 
        started_at = timezone.now()
        ended_at = timezone.now() - sixty_minutes
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, None)
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, 70)
        
        

   
if __name__ == '__main__':
    unittest.main()
    