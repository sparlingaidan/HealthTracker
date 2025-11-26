import time
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from django.db import connections

class Command(BaseCommand):
    """Django command to wait for database connection."""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        while not db_conn:
            try:
                # Try to get a connection to the default database
                connections['default'].ensure_connection()
                db_conn = True
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))