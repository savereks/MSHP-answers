from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Saves info from json file to database'

    def add_arguments(self, parser):
        # Здесь вы назвали аргумент 'filename'
        parser.add_argument('filename', type=str, help='Json file name')

    def handle(self, *args, **options):
        # И здесь нужно обращаться к 'filename'
        filename = options['filename']
        self.stdout.write(self.style.SUCCESS(f'Команда запущена с файлом: {filename}'))