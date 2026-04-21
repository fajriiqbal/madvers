from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bendahara', '0005_siswa_pondok'),
    ]

    operations = [
        migrations.AddField(
            model_name='kaskeluar',
            name='jenis_pembayaran',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='kas_keluar_set',
                to='bendahara.jenispembayaran',
            ),
        ),
    ]
