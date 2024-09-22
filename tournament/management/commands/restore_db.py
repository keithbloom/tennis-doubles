# yourapp/management/commands/restore_db.py

import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
import environ

class Command(BaseCommand):
    help = 'Restore SQLite database from the latest backup in AWS S3'

    def handle(self, *args, **options):
        environ.Env.read_env(settings.BASE_DIR / '.env')
        env = environ.Env()

        # Get the path to the SQLite database file
        db_path = settings.DATABASES['default']['NAME']

        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY')
        )

        bucket_name = env('AWS_BACKUP_BUCKET_NAME')

        try:
            # List objects in the bucket
            response = s3_client.list_objects_v2(Bucket=bucket_name)

            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING('No backups found in the S3 bucket.'))
                return

            # Sort the objects by last modified date
            backups = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)

            if not backups:
                self.stdout.write(self.style.WARNING('No backups found in the S3 bucket.'))
                return

            # Get the latest backup
            latest_backup = backups[0]['Key']

            # Download the latest backup
            download_path = os.path.join(settings.BASE_DIR, 'latest_backup.sqlite3')
            s3_client.download_file(bucket_name, latest_backup, download_path)

            # Backup the current database
            current_backup_path = f"{db_path}.bak"
            shutil.copy2(db_path, current_backup_path)

            # Replace the current database with the downloaded backup
            shutil.copy2(download_path, db_path)

            # Clean up the downloaded file
            os.remove(download_path)

            self.stdout.write(self.style.SUCCESS(f'Successfully restored database from {latest_backup}'))
            self.stdout.write(self.style.SUCCESS(f'Previous database backed up to {current_backup_path}'))

        except ClientError as e:
            self.stdout.write(self.style.ERROR(f'Error accessing S3: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during restore: {str(e)}'))