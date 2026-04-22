from django.contrib import admin
from .models import Semester, Siswa, JenisPembayaran, Tagihan, Pembayaran, TransaksiPembayaran, KasKeluar


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tahun_ajaran', 'semester', 'tanggal_mulai', 'tanggal_selesai', 'aktif')
    search_fields = ('nama', 'tahun_ajaran')
    list_filter = ('semester', 'aktif')
    list_editable = ('aktif',)


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ('nis', 'nama', 'kelas', 'pondok', 'aktif')
    search_fields = ('nis', 'nama')
    list_filter = ('kelas', 'pondok', 'aktif')


@admin.register(JenisPembayaran)
class JenisPembayaranAdmin(admin.ModelAdmin):
    list_display = ('nama', 'target_kelas_label', 'nominal_default', 'is_bulanan', 'jumlah_bulan_per_semester', 'wajib_per_semester', 'aktif')
    search_fields = ('nama',)
    list_filter = ('aktif', 'wajib_per_semester', 'is_bulanan', 'target_kelas')

    @admin.display(description='Target Kelas')
    def target_kelas_label(self, obj):
        return obj.get_target_kelas_display()


@admin.register(Tagihan)
class TagihanAdmin(admin.ModelAdmin):
    list_display = ['siswa', 'jenis', 'semester', 'nominal', 'periode', 'jatuh_tempo']
    list_filter = ['jenis', 'semester']
    search_fields = ('siswa__nama', 'semester__nama')


@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = ('transaksi', 'tagihan', 'jumlah_bayar', 'tanggal_bayar', 'metode')
    list_filter = ('tanggal_bayar', 'tagihan__semester')
    search_fields = ('tagihan__siswa__nama', 'tagihan__jenis__nama')
    date_hierarchy = 'tanggal_bayar'


@admin.register(TransaksiPembayaran)
class TransaksiPembayaranAdmin(admin.ModelAdmin):
    list_display = ('kode_transaksi', 'siswa', 'semester', 'tanggal_bayar', 'metode')
    list_filter = ('semester', 'tanggal_bayar')
    search_fields = ('kode_transaksi', 'siswa__nama', 'siswa__nis')
    date_hierarchy = 'tanggal_bayar'


@admin.register(KasKeluar)
class KasKeluarAdmin(admin.ModelAdmin):
    list_display = ('kode_pengeluaran', 'judul', 'kategori', 'jumlah', 'tanggal_pengeluaran', 'semester')
    list_filter = ('tanggal_pengeluaran', 'semester', 'kategori')
    search_fields = ('kode_pengeluaran', 'judul', 'kategori', 'keterangan')
    date_hierarchy = 'tanggal_pengeluaran'
