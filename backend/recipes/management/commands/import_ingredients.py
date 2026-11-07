import argparse
import json
from pathlib import Path
from typing import cast

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


DEFAULT_PATH = Path(settings.BASE_DIR).parent / 'data' / 'ingredients.json'


class Command(BaseCommand):
    """Импортировать ингредиенты из JSON-файла в базу данных."""

    help = 'Import ingredients from a JSON file.'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Добавить аргумент командной строки для пути к файлу."""
        parser.add_argument(
            '--path',
            default=None,
            help='Custom path to ingredients.json.',
        )

    def handle(self, *_args: object, **options: object) -> None:
        """Прочитать файл и создать недостающие ингредиенты."""
        raw_path = cast('str | None', options['path'])
        path = Path(raw_path) if raw_path else DEFAULT_PATH
        if not path.is_file():
            raise CommandError(f'File does not exist: {path}')

        with path.open(encoding='utf-8') as file_obj:
            rows = json.load(file_obj)

        ingredients = [
            Ingredient(
                name=row['name'],
                measurement_unit=row['measurement_unit'],
            )
            for row in rows
        ]
        created = Ingredient.objects.bulk_create(
            ingredients,
            ignore_conflicts=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed. file={path}; '
                f'parsed={len(ingredients)}; created={len(created)}.',
            ),
        )
