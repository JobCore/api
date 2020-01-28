from django.core.management.base import BaseCommand, CommandError
from api.models import (Employee, Shift, ShiftInvite, ShiftApplication, Clockin, Employer, AvailabilityBlock, FavoriteList, Venue, JobCoreInvite,
                        Rate, FCMDevice, Notification, PayrollPeriod, PayrollPeriodPayment, Profile, Position, User, Document)

class Command(BaseCommand):
    help = 'Resets the database and adds the default fixtures'

    def handle(self, *args, **options):

        log = []

        log.insert(0, "Deleting ShiftInvites...")
        ShiftInvite.objects.all().delete()

        log.insert(0, "Deleting ShiftApplication...")
        ShiftApplication.objects.all().delete()

        log.insert(0, "Deleting Shifts...")
        Shift.objects.all().delete()

        log.insert(0, "Deleting Employees...")
        Employee.objects.all().delete()

        log.insert(0, "Deleting Employers...")
        Employer.objects.all().delete()
        log.insert(0, "Deleting Profiles and Users...")
        Profile.objects.all().delete()
        User.objects.all().delete()

        log.insert(0, "Deleting Clockins...")
        Clockin.objects.all().delete()

        log.insert(0, "Deleting AvailabilityBlocks...")
        AvailabilityBlock.objects.all().delete()

        log.insert(0, "Deleting FavoriteLists...")
        FavoriteList.objects.all().delete()

        log.insert(0, "Deleting Venues...")
        Venue.objects.all().delete()

        log.insert(0, "Deleting JobCoreInvites...")
        JobCoreInvite.objects.all().delete()

        log.insert(0, "Deleting Ratings...")
        Rate.objects.all().delete()

        log.insert(0, "Deleting FCM Devices...")
        FCMDevice.objects.all().delete()

        log.insert(0, "Deleting Notification...")
        Notification.objects.all().delete()

        log.insert(0, "Deleting PayrollPeriods...")
        PayrollPeriod.objects.all().delete()

        log.insert(0, "Deleting PayrollPeriodPayments...")
        PayrollPeriodPayment.objects.all().delete()

        log.insert(0, "Deleting Documents...")
        Document.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Successfully deleted all models"))