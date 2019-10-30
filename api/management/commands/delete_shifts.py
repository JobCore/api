from django.core.management.base import BaseCommand, CommandError
from api.models import (Shift, ShiftInvite, ShiftApplication)

class Command(BaseCommand):
    help = 'Deletes all the shifts form the database on cascade'

    def handle(self, *args, **options):

        ShiftInvite.objects.all().delete()
        ShiftApplication.objects.all().delete()
        Shift.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Successfully deleted all shifts"))