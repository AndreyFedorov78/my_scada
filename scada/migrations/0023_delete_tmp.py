from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scada', '0022_sensorarhive_index'),
    ]

    operations = [
        migrations.DeleteModel(
            name='tmp',
        ),
    ]
