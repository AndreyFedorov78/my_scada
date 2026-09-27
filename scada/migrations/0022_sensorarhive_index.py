from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scada', '0021_sensorlist_archive'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='sensorarhive',
            index=models.Index(fields=['sensorId', 'type', 'date'], name='arhive_sensor_type_date'),
        ),
    ]
