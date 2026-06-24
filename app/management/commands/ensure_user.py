from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create an application user from APP_USERNAME and APP_PASSWORD if one does not exist'

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        if not username or not password:
            self.stdout.write('APP_USERNAME and APP_PASSWORD not set, skipping user creation.')
            return

        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists.')
            return

        user_model.objects.create_user(username=username, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created user "{username}".'))

    def add_arguments(self, parser):
        import os

        parser.add_argument(
            '--username',
            default=os.environ.get('APP_USERNAME'),
        )
        parser.add_argument(
            '--password',
            default=os.environ.get('APP_PASSWORD'),
        )
