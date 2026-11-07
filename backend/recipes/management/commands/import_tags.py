from django.core.management.base import BaseCommand

from recipes.models import Tag


DEFAULT_TAGS: tuple[tuple[str, str], ...] = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
)


class Command(BaseCommand):
    """Создать стандартные теги рецептов в базе данных."""

    help = 'Create default tags: breakfast, lunch, dinner.'

    def handle(self, *_args: object, **_options: object) -> None:
        """Создать недостающие теги и вывести статистику импорта."""
        created_count = 0
        existed_count = 0

        for name, slug in DEFAULT_TAGS:
            _, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )
            if created:
                created_count += 1
            else:
                existed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Import completed. created={created_count}; '
                f'existed={existed_count}.',
            ),
        )
