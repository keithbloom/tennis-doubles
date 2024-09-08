# In myapp/management/commands/create_seed_data.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os

class Command(BaseCommand):
    help = 'Creates seed data JSON file from the current database'

    def handle(self, *args, **options):
        output_file = 'tournament/fixtures/seed_data.json'
        
        # Ensure the fixtures directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Create the seed data
        call_command('dumpdata', 
                     exclude=['contenttypes', 'auth.permission'],
                     output=output_file,
                     indent=2)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created seed data at {output_file}'))