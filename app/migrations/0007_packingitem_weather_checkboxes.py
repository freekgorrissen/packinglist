from django.db import migrations, models


def migrate_weather_to_checkboxes(apps, schema_editor):
    PackingItem = apps.get_model('app', 'PackingItem')
    for item in PackingItem.objects.exclude(weather='').iterator():
        if item.weather == 'hot':
            item.weather_hot = True
        elif item.weather == 'cold':
            item.weather_cold = True
        item.save(update_fields=['weather_hot', 'weather_cold'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_packingitem_weather_trip_weather_cold_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='packingitem',
            name='weather_hot',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='packingitem',
            name='weather_cold',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_weather_to_checkboxes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='packingitem',
            name='weather',
        ),
    ]
