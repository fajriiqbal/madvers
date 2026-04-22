from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bendahara', '0006_kaskeluar_jenis_pembayaran'),
    ]

    operations = [
        migrations.AddField(
            model_name='jenispembayaran',
            name='target_kelas',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Semua Kelas'),
                    ('7', 'Khusus Kelas 7'),
                    ('8', 'Khusus Kelas 8'),
                    ('9', 'Khusus Kelas 9'),
                ],
                default='',
                max_length=10,
            ),
        ),
    ]
