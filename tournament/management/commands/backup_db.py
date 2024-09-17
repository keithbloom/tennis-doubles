# yourapp/management/commands/backup_db.py

import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from pathlib import Path
import environ


class Command(BaseCommand):
    help = 'Backup SQLite database and upload to AWS S3'

    def handle(self, *args, **options):
        environ.Env.read_env(settings.BASE_DIR / '.env')

        env = environ.Env()
   
        # Get the path to the SQLite database file
        db_path = settings.DATABASES['default']['NAME']
        
        # Create a timestamp for the backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sqlite3'
        
        # Create a copy of the database file
        backup_path = os.path.join(settings.BASE_DIR, backup_filename)
        shutil.copy2(db_path, backup_path)

        # Upload to AWS S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY')
        )

        bucket_name = env('AWS_BACKUP_BUCKET_NAME')
        s3_client.upload_file(backup_path, bucket_name, backup_filename)

        # Clean up local backup file
        os.remove(backup_path)

        self.stdout.write(self.style.SUCCESS(f'Successfully backed up database to {backup_filename} in S3 bucket {bucket_name}'))