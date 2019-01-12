from api.serializers import clockin_serializer
import unittest, datetime
from django.utils import timezone

class TestCI(unittest.TestCase):

    def test_clockin(self):
        five_minutes = datetime.timedelta(minutes=5)
        sixty_minutes = datetime.timedelta(minutes=60)
        
        started_at = timezone.now() + five_minutes
        ended_at = timezone.now() + sixty_minutes
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, None)
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, 4)
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, 6))
        
        started_at = timezone.now() - five_minutes
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, None))
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, 1)
        self.assertIsNone(clockin_serializer.validate_clock_in(started_at, ended_at, 10))
        
        started_at = timezone.now() - five_minutes
        ended_at = timezone.now() - sixty_minutes
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, None)
        self.assertRaises(ValueError, clockin_serializer.validate_clock_in, started_at, ended_at, 70)
        
        

   
if __name__ == '__main__':
    unittest.main()
    