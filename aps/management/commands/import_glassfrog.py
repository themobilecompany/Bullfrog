__author__ = 'Erie'

from django.core.management.base import BaseCommand, CommandError
from aps.utils.GlassfrogImporter import GlassfrogImporter
from aps.models import Person
from aps.models import Circle
from aps.models import RoleFiller
from aps.models import Role

# script meant to do automated imports via cron
# > python manage.py import_glassfrog

class Command(BaseCommand):
    help = 'Imports all entities from Glassfrog and updates the Bullfrog database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Import started, be patient...'))
        imp = GlassfrogImporter()
        imp.doImport()
        self.stdout.write(self.style.SUCCESS('Done.'))