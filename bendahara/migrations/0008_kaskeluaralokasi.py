from django.db import migrations, models


def forward_copy_single_allocation(apps, schema_editor):
    KasKeluar = apps.get_model('bendahara', 'KasKeluar')
    KasKeluarAlokasi = apps.get_model('bendahara', 'KasKeluarAlokasi')

    for kas_keluar in KasKeluar.objects.exclude(jenis_pembayaran_id__isnull=True):
        exists = KasKeluarAlokasi.objects.filter(
            kas_keluar_id=kas_keluar.id,
            jenis_pembayaran_id=kas_keluar.jenis_pembayaran_id,
        ).exists()
        if exists:
            continue

        KasKeluarAlokasi.objects.create(
            kas_keluar_id=kas_keluar.id,
            jenis_pembayaran_id=kas_keluar.jenis_pembayaran_id,
            nominal=kas_keluar.jumlah,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('bendahara', '0007_jenispembayaran_target_kelas'),
    ]

    operations = [
        migrations.CreateModel(
            name='KasKeluarAlokasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nominal', models.IntegerField()),
                ('jenis_pembayaran', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='kas_keluar_alokasi_set', to='bendahara.jenispembayaran')),
                ('kas_keluar', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='alokasi_set', to='bendahara.kaskeluar')),
            ],
            options={
                'verbose_name': 'Kas Keluar Alokasi',
                'verbose_name_plural': 'Kas Keluar Alokasi',
                'ordering': ['id'],
            },
        ),
        migrations.AddConstraint(
            model_name='kaskeluaralokasi',
            constraint=models.UniqueConstraint(fields=('kas_keluar', 'jenis_pembayaran'), name='unique_alokasi_per_jenis_pengeluaran'),
        ),
        migrations.RunPython(forward_copy_single_allocation, migrations.RunPython.noop),
    ]
