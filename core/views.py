from django.shortcuts import render
from django.db.models import Prefetch
from django.utils.timezone import localdate

from bendahara.models import (
    JenisPembayaran,
    KasKeluar,
    Pembayaran,
    Semester,
    Siswa,
    Tagihan,
)

def home(request):
    semester_aktif = Semester.objects.filter(aktif=True).first()
    return render(request, 'core/home.html', {
        'semester_aktif': semester_aktif,
    })


def monitoring_bendahara(request):
    today = localdate()
    semester_aktif = Semester.objects.filter(aktif=True).first()

    if semester_aktif:
        tagihan_queryset = (
            Tagihan.objects.filter(semester=semester_aktif)
            .select_related('siswa', 'jenis', 'semester')
            .prefetch_related('pembayaran_set')
        )
        pembayaran_queryset = (
            Pembayaran.objects.select_related(
                'transaksi',
                'tagihan__siswa',
                'tagihan__jenis',
                'tagihan__semester',
            )
            .filter(tagihan__semester=semester_aktif)
            .order_by('-tanggal_bayar')
        )
        kas_keluar_queryset = KasKeluar.objects.filter(semester=semester_aktif).order_by('-tanggal_pengeluaran', '-id')
    else:
        tagihan_queryset = Tagihan.objects.none()
        pembayaran_queryset = Pembayaran.objects.none()
        kas_keluar_queryset = KasKeluar.objects.none()

    tagihan_items = list(tagihan_queryset)
    pembayaran_items = list(pembayaran_queryset[:8])
    kas_keluar_items = list(kas_keluar_queryset[:6])

    total_siswa_aktif = Siswa.objects.filter(aktif=True).count()
    total_jenis_pembayaran_aktif = JenisPembayaran.objects.filter(aktif=True).count()
    total_tagihan = len(tagihan_items)
    total_target_masuk = sum(tagihan.nominal for tagihan in tagihan_items)
    total_realisasi_masuk = sum(tagihan.total_terbayar for tagihan in tagihan_items)
    total_sisa = max(total_target_masuk - total_realisasi_masuk, 0)
    total_pengeluaran = sum(item.jumlah for item in kas_keluar_queryset)
    saldo_aktual = total_realisasi_masuk - total_pengeluaran

    siswa_objects = (
        Siswa.objects.filter(aktif=True)
        .prefetch_related(
            Prefetch(
                'tagihan_set',
                queryset=tagihan_queryset,
            )
        )
        .order_by('nama')
    )

    siswa_tunggakan = []
    pondok_summary_map = {}
    for siswa in siswa_objects:
        siswa_tagihan = list(siswa.tagihan_set.all())
        if not siswa_tagihan:
            continue

        siswa_total_sisa = sum(tagihan.sisa_tagihan for tagihan in siswa_tagihan)
        if siswa_total_sisa > 0:
            siswa_tunggakan.append({
                'siswa': siswa,
                'total_sisa': siswa_total_sisa,
                'jumlah_item': sum(1 for tagihan in siswa_tagihan if tagihan.sisa_tagihan > 0),
            })

            pondok_key = siswa.pondok or 'Belum Diisi'
            if pondok_key not in pondok_summary_map:
                pondok_summary_map[pondok_key] = {
                    'pondok': pondok_key,
                    'jumlah_siswa': 0,
                    'total_sisa': 0,
                }
            pondok_summary_map[pondok_key]['jumlah_siswa'] += 1
            pondok_summary_map[pondok_key]['total_sisa'] += siswa_total_sisa

    siswa_tunggakan.sort(key=lambda item: item['total_sisa'], reverse=True)
    pondok_summary_rows = sorted(
        pondok_summary_map.values(),
        key=lambda item: item['total_sisa'],
        reverse=True,
    )

    jenis_summary_map = {}
    for tagihan in tagihan_items:
        jenis_summary_map.setdefault(tagihan.jenis_id, {
            'jenis': tagihan.jenis,
            'target': 0,
            'masuk': 0,
            'sisa': 0,
        })
        jenis_summary_map[tagihan.jenis_id]['target'] += tagihan.nominal
        jenis_summary_map[tagihan.jenis_id]['masuk'] += tagihan.total_terbayar
        jenis_summary_map[tagihan.jenis_id]['sisa'] += tagihan.sisa_tagihan
    jenis_summary_rows = sorted(jenis_summary_map.values(), key=lambda item: item['target'], reverse=True)

    context = {
        'today': today,
        'semester_aktif': semester_aktif,
        'total_siswa_aktif': total_siswa_aktif,
        'total_jenis_pembayaran_aktif': total_jenis_pembayaran_aktif,
        'total_tagihan': total_tagihan,
        'total_target_masuk': total_target_masuk,
        'total_realisasi_masuk': total_realisasi_masuk,
        'total_sisa': total_sisa,
        'total_pengeluaran': total_pengeluaran,
        'saldo_aktual': saldo_aktual,
        'pembayaran_items': pembayaran_items,
        'kas_keluar_items': kas_keluar_items,
        'siswa_tunggakan': siswa_tunggakan[:8],
        'pondok_summary_rows': pondok_summary_rows[:8],
        'jenis_summary_rows': jenis_summary_rows[:8],
    }
    return render(request, 'core/monitoring_bendahara.html', context)
