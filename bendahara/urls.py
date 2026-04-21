from django.urls import path

from .views import (
    dashboard,
    download_template_siswa,
    jenis_pembayaran_create,
    jenis_pembayaran_delete,
    jenis_pembayaran_list,
    jenis_pembayaran_toggle,
    jenis_pembayaran_update,
    kas_sekolah,
    login_bendahara,
    logout_bendahara,
    pembayaran_create,
    pembayaran_detail_siswa,
    pembayaran_download,
    pembayaran_list,
    transaksi_pembayaran_download,
    siswa_create,
    siswa_delete,
    siswa_list,
    siswa_update,
    tagihan_create,
    tagihan_download,
    tagihan_list,
    tagihan_update,
    upload_siswa,
    # Semester views
    semester_list,
    semester_create,
    semester_update,
    semester_delete,
    semester_toggle,
    # Bulk tagihan
    buat_tagihan_semester,
    # Laporan
    laporan_bulanan,
    laporan_pondok,
    laporan_jenis_pembayaran,
    laporan_semester,
    laporan_siswa,
    laporan_tunggakan,
)

app_name = 'bendahara'

urlpatterns = [
    path('login/', login_bendahara, name='login'),
    path('logout/', logout_bendahara, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('kas-sekolah/', kas_sekolah, name='kas_sekolah'),
    
    # Semester
    path('semester/', semester_list, name='semester_list'),
    path('semester/tambah/', semester_create, name='semester_create'),
    path('semester/<int:pk>/edit/', semester_update, name='semester_update'),
    path('semester/<int:pk>/delete/', semester_delete, name='semester_delete'),
    path('semester/<int:pk>/toggle/', semester_toggle, name='semester_toggle'),
    
    # Siswa
    path('siswa/', siswa_list, name='siswa_list'),
    path('siswa/tambah/', siswa_create, name='siswa_create'),
    path('siswa/upload/', upload_siswa, name='upload_siswa'),
    path('siswa/<int:pk>/edit/', siswa_update, name='siswa_update'),
    path('siswa/<int:pk>/delete/', siswa_delete, name='siswa_delete'),
    
    # Jenis Pembayaran
    path('jenis-pembayaran/', jenis_pembayaran_list, name='jenis_pembayaran_list'),
    path('jenis-pembayaran/tambah/', jenis_pembayaran_create, name='jenis_pembayaran_create'),
    path('jenis-pembayaran/<int:pk>/edit/', jenis_pembayaran_update, name='jenis_pembayaran_update'),
    path('jenis-pembayaran/<int:pk>/delete/', jenis_pembayaran_delete, name='jenis_pembayaran_delete'),
    path('jenis-pembayaran/<int:pk>/toggle/', jenis_pembayaran_toggle, name='jenis_pembayaran_toggle'),
    
    # Tagihan
    path('tagihan/', tagihan_list, name='tagihan_list'),
    path('tagihan/tambah/', tagihan_create, name='tagihan_create'),
    path('tagihan/<int:pk>/edit/', tagihan_update, name='tagihan_update'),
    path('tagihan/<int:pk>/download/', tagihan_download, name='tagihan_download'),
    path('tagihan/buat-semester/', buat_tagihan_semester, name='buat_tagihan_semester'),
    
    # Pembayaran
    path('pembayaran/', pembayaran_list, name='pembayaran_list'),
    path('pembayaran/tambah/', pembayaran_create, name='pembayaran_create'),
    path('pembayaran/<int:pk>/download/', pembayaran_download, name='pembayaran_download'),
    path('pembayaran/transaksi/<int:pk>/download/', transaksi_pembayaran_download, name='transaksi_pembayaran_download'),
    path('pembayaran/siswa/<int:pk>/', pembayaran_detail_siswa, name='pembayaran_detail_siswa'),
    
    # Laporan
    path('laporan/bulanan/', laporan_bulanan, name='laporan_bulanan'),
    path('laporan/pondok/', laporan_pondok, name='laporan_pondok'),
    path('laporan/jenis-pembayaran/', laporan_jenis_pembayaran, name='laporan_jenis_pembayaran'),
    path('laporan/semester/', laporan_semester, name='laporan_semester'),
    path('laporan/siswa/', laporan_siswa, name='laporan_siswa'),
    path('laporan/tunggakan/', laporan_tunggakan, name='laporan_tunggakan'),
    
    # Template
    path('download-template-siswa/', download_template_siswa, name='download_template_siswa'),
]
