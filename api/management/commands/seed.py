import subprocess, os
from os import listdir
from os.path import isfile, join
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Deletes all the shifts form the database on cascade'

    def add_arguments(self, parser):
        parser.add_argument('environment', nargs='+', type=str)

    def handle(self, *args, **options):
        # loaddata api/fixtures/"+options['environment'][0]+"/*.yaml
        posible_environments = ['development', 'production']
        if options['environment'][0] not in posible_environments:
            self.stdout.write(self.style.ERROR("Please speficy a valid environment [development, production]"))
            return

        current_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../../"
        onlyfiles = [f for f in listdir(current_dir+"api/fixtures/"+options['environment'][0]) if isfile(join(current_dir+"api/fixtures/"+options['environment'][0], f))]
        buffer = ''
        self.stdout.write('Found the following fixtures to load: '+ ",".join(sorted(onlyfiles)))
        self.stdout.write('loading fixtures...')
        for file_name in sorted(onlyfiles):
            out = subprocess.Popen(['python3', current_dir+"manage.py", "loaddata", current_dir+"api/fixtures/"+options['environment'][0]+"/"+file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

            stdout = out.communicate()[0]
            buffer = buffer + stdout.decode('utf-8')

        self.stdout.write(buffer)

    # current_dir = os.path.dirname(os.path.realpath(__file__)) + "/../../../"
    # out = subprocess.Popen(['python3', current_dir+"manage.py", "loaddata", current_dir+"api/fixtures/"+options['environment'][0]+"/*.yaml"],
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.STDOUT)
    # print(current_dir+"api/fixtures/"+options['environment'][0]+"/*.yaml")
    # stdout = out.communicate()[0]
    # self.stdout.write(stdout.decode('utf-8'))