from django.core.management.base import BaseCommand, CommandError
from api.views import hooks

class Command(BaseCommand):
    help = 'Process the expired shifts, invites and clockins'

    def handle(self, *args, **options):

        #log = []

        hooks.process_expired_shifts()
        self.stdout.write(self.style.SUCCESS("Successfully expired shifts and clockins"))

        hooks.process_expired_documents()
        self.stdout.write(self.style.SUCCESS("Successfully expired documents"))