import re

from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


class Semester(models.Model):
    nama = models.CharField(max_length=50)  # "Ganjil 2024/2025", "Genap 2024/2025"
    tahun_ajaran = models.CharField(max_length=20)  # "2024/2025"
    semester = models.CharField(max_length=20)  # "Ganjil" atau "Genap"
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    aktif = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.aktif:
            Semester.objects.exclude(pk=self.pk).update(aktif=False)

    def __str__(self):
        return self.nama

    class Meta:
        ordering = ['-tanggal_mulai']
        verbose_name = 'Semester'
        verbose_name_plural = 'Semester'


class Siswa(models.Model):
    nis = models.CharField(max_length=30, unique=True)
    nama = models.CharField(max_length=120)
    kelas = models.CharField(max_length=30)
    pondok = models.CharField(max_length=100, blank=True, default='')
    aktif = models.BooleanField(default=True)

    @property
    def tingkat_kelas(self):
        kelas_value = (self.kelas or '').strip().upper()
        if not kelas_value:
            return ''

        normalized = re.sub(r'\s+', '', kelas_value)
        roman_map = (
            ('VIII', '8'),
            ('VII', '7'),
            ('IX', '9'),
        )

        for prefix, grade in roman_map:
            if normalized.startswith(prefix):
                return grade

        match = re.match(r'(\d+)', normalized)
        if match:
            return match.group(1)

        return ''

    def __str__(self):
        return self.nama


class JenisPembayaran(models.Model):
    TARGET_KELAS_CHOICES = [
        ('', 'Semua Kelas'),
        ('7', 'Khusus Kelas 7'),
        ('8', 'Khusus Kelas 8'),
        ('9', 'Khusus Kelas 9'),
    ]

    nama = models.CharField(max_length=100)
    nominal_default = models.IntegerField()
    deskripsi = models.TextField(blank=True, null=True)
    aktif = models.BooleanField(default=True)
    wajib_per_semester = models.BooleanField(default=True)  # True jika harus dibayar tiap semester
    is_bulanan = models.BooleanField(default=False)
    jumlah_bulan_per_semester = models.PositiveSmallIntegerField(default=6)
    target_kelas = models.CharField(
        max_length=10,
        blank=True,
        default='',
        choices=TARGET_KELAS_CHOICES,
    )

    def applies_to_student(self, siswa):
        return not self.target_kelas or self.target_kelas == siswa.tingkat_kelas

    def __str__(self):
        return self.nama


class Tagihan(models.Model):
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='tagihan_set')
    jenis = models.ForeignKey(JenisPembayaran, on_delete=models.CASCADE, related_name='tagihan_set')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='tagihan_set')

    nominal = models.IntegerField()

    periode = models.CharField(max_length=20, blank=True, default='')
    urutan_periode = models.PositiveSmallIntegerField(default=0)
    jatuh_tempo = models.DateField(blank=True, null=True)
    catatan = models.TextField(blank=True, null=True)

    @property
    def total_terbayar(self):
        result = self.pembayaran_set.aggregate(
            total=Coalesce(Sum('jumlah_bayar'), 0)
        )['total']
        return result if result is not None else 0

    @property
    def sisa_tagihan(self):
        return max(self.nominal - self.total_terbayar, 0)

    @property
    def status_pembayaran(self):
        if self.total_terbayar <= 0:
            return 'Belum Bayar'
        if self.total_terbayar >= self.nominal:
            return 'Lunas'
        return 'Cicilan'

    def update_status(self):
        return self.status_pembayaran

    def __str__(self):
        if self.periode:
            return f"{self.siswa} - {self.jenis} - {self.semester} - {self.periode}"
        return f"{self.siswa} - {self.jenis} - {self.semester}"

    class Meta:
        ordering = ['-id']
        verbose_name = 'Tagihan'
        verbose_name_plural = 'Tagihan'
        constraints = [
            models.UniqueConstraint(
                fields=['siswa', 'jenis', 'semester', 'urutan_periode'],
                name='unique_tagihan_periode_siswa',
            ),
        ]


class TransaksiPembayaran(models.Model):
    kode_transaksi = models.CharField(max_length=32, unique=True, blank=True)
    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='transaksi_pembayaran_set')
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        related_name='transaksi_pembayaran_set',
        blank=True,
        null=True,
    )
    tanggal_bayar = models.DateTimeField(auto_now_add=True)
    metode = models.CharField(max_length=50, blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.kode_transaksi:
            local_time = timezone.localtime(self.tanggal_bayar)
            self.kode_transaksi = f"TRX-{local_time.strftime('%Y%m%d')}-{self.pk:04d}"
            super().save(update_fields=['kode_transaksi'])

    @property
    def total_bayar(self):
        result = self.pembayaran_set.aggregate(
            total=Coalesce(Sum('jumlah_bayar'), 0)
        )['total']
        return result if result is not None else 0

    @property
    def jumlah_tagihan(self):
        return self.pembayaran_set.count()

    def __str__(self):
        return self.kode_transaksi or f"Transaksi #{self.pk}"

    class Meta:
        ordering = ['-tanggal_bayar', '-id']
        verbose_name = 'Transaksi Pembayaran'
        verbose_name_plural = 'Transaksi Pembayaran'


class Pembayaran(models.Model):
    transaksi = models.ForeignKey(
        TransaksiPembayaran,
        on_delete=models.CASCADE,
        related_name='pembayaran_set',
        blank=True,
        null=True,
    )
    tagihan = models.ForeignKey(Tagihan, on_delete=models.CASCADE, related_name='pembayaran_set')
    jumlah_bayar = models.IntegerField()
    tanggal_bayar = models.DateTimeField(auto_now_add=True)

    metode = models.CharField(max_length=50, blank=True, null=True)
    keterangan = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        if self.transaksi_id and self.transaksi and self.transaksi.kode_transaksi:
            return f"{self.transaksi.kode_transaksi} - {self.tagihan} - {self.jumlah_bayar}"
        return f"{self.tagihan} - {self.jumlah_bayar}"


class KasKeluar(models.Model):
    kode_pengeluaran = models.CharField(max_length=32, unique=True, blank=True)
    judul = models.CharField(max_length=150)
    kategori = models.CharField(max_length=100)
    jenis_pembayaran = models.ForeignKey(
        JenisPembayaran,
        on_delete=models.SET_NULL,
        related_name='kas_keluar_set',
        blank=True,
        null=True,
    )
    jumlah = models.IntegerField()
    tanggal_pengeluaran = models.DateField(default=timezone.localdate)
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        related_name='kas_keluar_set',
        blank=True,
        null=True,
    )
    keterangan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.kode_pengeluaran:
            self.kode_pengeluaran = f"KK-{self.tanggal_pengeluaran.strftime('%Y%m%d')}-{self.pk:04d}"
            super().save(update_fields=['kode_pengeluaran'])

    def __str__(self):
        return self.kode_pengeluaran or f"Kas Keluar #{self.pk}"

    @property
    def total_alokasi(self):
        allocations = getattr(self, '_prefetched_objects_cache', {}).get('alokasi_set')
        if allocations is None:
            allocations = self.alokasi_set.all()
        return sum(item.nominal for item in allocations)

    @property
    def sisa_belum_dialokasikan(self):
        return max(self.jumlah - self.total_alokasi, 0)

    class Meta:
        ordering = ['-tanggal_pengeluaran', '-id']
        verbose_name = 'Kas Keluar'
        verbose_name_plural = 'Kas Keluar'


class KasKeluarAlokasi(models.Model):
    kas_keluar = models.ForeignKey(
        KasKeluar,
        on_delete=models.CASCADE,
        related_name='alokasi_set',
    )
    jenis_pembayaran = models.ForeignKey(
        JenisPembayaran,
        on_delete=models.CASCADE,
        related_name='kas_keluar_alokasi_set',
    )
    nominal = models.IntegerField()

    def __str__(self):
        return f"{self.kas_keluar} -> {self.jenis_pembayaran} ({self.nominal})"

    class Meta:
        ordering = ['id']
        verbose_name = 'Kas Keluar Alokasi'
        verbose_name_plural = 'Kas Keluar Alokasi'
        constraints = [
            models.UniqueConstraint(
                fields=['kas_keluar', 'jenis_pembayaran'],
                name='unique_alokasi_per_jenis_pengeluaran',
            ),
        ]
