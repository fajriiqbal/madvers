from django import forms
from itertools import zip_longest

from .models import (
    JenisPembayaran,
    KasKeluar,
    Pembayaran,
    Semester,
    Siswa,
    Tagihan,
)


def positive_integer_attrs(*, placeholder):
    return {
        'min': '1',
        'step': '1',
        'inputmode': 'numeric',
        'placeholder': placeholder,
        'autocomplete': 'off',
    }


class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class SiswaForm(forms.ModelForm):
    class Meta:
        model = Siswa
        fields = ['nis', 'nama', 'kelas', 'pondok', 'aktif']


class JenisPembayaranForm(forms.ModelForm):
    class Meta:
        model = JenisPembayaran
        fields = [
            'nama',
            'nominal_default',
            'target_kelas',
            'deskripsi',
            'aktif',
            'wajib_per_semester',
            'is_bulanan',
            'jumlah_bulan_per_semester',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nama'].widget.attrs.update({
            'placeholder': 'Contoh: SPP, Jemputan, Wisuda',
        })
        self.fields['nominal_default'].widget.attrs.update(
            positive_integer_attrs(placeholder='Masukkan nominal default')
        )
        self.fields['jumlah_bulan_per_semester'].widget.attrs.update({
            'min': '1',
            'step': '1',
            'inputmode': 'numeric',
            'placeholder': 'Contoh: 6',
            'autocomplete': 'off',
        })
        self.fields['target_kelas'].label = 'Berlaku untuk kelas'
        self.fields['target_kelas'].help_text = (
            'Pilih "Semua Kelas" jika tagihan ini berlaku umum, atau batasi untuk kelas tertentu seperti kelas 9.'
        )
        self.fields['wajib_per_semester'].label = 'Muncul setiap semester'
        self.fields['wajib_per_semester'].help_text = (
            'Aktifkan jika tagihan ini perlu otomatis dibuat saat siswa baru ditambahkan pada semester aktif.'
        )
        self.fields['is_bulanan'].label = 'Gunakan tagihan per bulan'
        self.fields['jumlah_bulan_per_semester'].label = 'Jumlah bulan per semester'
        self.fields['jumlah_bulan_per_semester'].help_text = (
            'Dipakai saat jenis pembayaran dibuat bulanan, misalnya SPP 6 bulan.'
        )

    def clean_nominal_default(self):
        nominal = self.cleaned_data.get('nominal_default')
        if nominal is None or nominal <= 0:
            raise forms.ValidationError('Nominal default harus lebih dari 0.')
        return nominal

    def clean_jumlah_bulan_per_semester(self):
        jumlah = self.cleaned_data.get('jumlah_bulan_per_semester') or 0
        if jumlah <= 0:
            raise forms.ValidationError('Jumlah bulan per semester harus lebih dari 0.')
        return jumlah


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['nama', 'tahun_ajaran', 'semester', 'tanggal_mulai', 'tanggal_selesai', 'aktif']
        widgets = {
            'tanggal_mulai': forms.DateInput(attrs={'type': 'date'}),
            'tanggal_selesai': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tanggal_mulai = cleaned_data.get('tanggal_mulai')
        tanggal_selesai = cleaned_data.get('tanggal_selesai')

        if tanggal_mulai and tanggal_selesai and tanggal_mulai > tanggal_selesai:
            raise forms.ValidationError("Tanggal mulai harus lebih kecil dari tanggal selesai.")

        return cleaned_data


class TagihanForm(forms.ModelForm):
    class Meta:
        model = Tagihan
        fields = ['siswa', 'jenis', 'semester', 'nominal', 'periode', 'jatuh_tempo', 'catatan']
        widgets = {
            'jatuh_tempo': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nominal'].widget.attrs.update(
            positive_integer_attrs(placeholder='Masukkan nominal tagihan')
        )
        self.fields['periode'].widget.attrs.update({
            'placeholder': 'Contoh: Juli 2026',
        })

    def clean_nominal(self):
        nominal = self.cleaned_data.get('nominal')
        if nominal is None or nominal <= 0:
            raise forms.ValidationError('Nominal tagihan harus lebih dari 0.')
        return nominal


class PembayaranForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = ['tagihan', 'jumlah_bayar', 'metode', 'keterangan']

    def __init__(self, *args, **kwargs):
        siswa_id = kwargs.pop('siswa_id', None)
        tagihan_id = kwargs.pop('tagihan_id', None)
        semester_id = kwargs.pop('semester_id', None)
        super().__init__(*args, **kwargs)
        self.fields['jumlah_bayar'].widget.attrs.update(
            positive_integer_attrs(placeholder='Masukkan jumlah bayar')
        )
        if not semester_id:
            active_semester = Semester.objects.filter(aktif=True).first()
            semester_id = active_semester.pk if active_semester else None

        base_queryset = Tagihan.objects.select_related('siswa', 'jenis', 'semester').order_by(
            'siswa__nama', 'jenis__nama', 'semester__nama'
        )
        if siswa_id:
            base_queryset = base_queryset.filter(siswa_id=siswa_id)
        if semester_id:
            base_queryset = base_queryset.filter(semester_id=semester_id)

        available_tagihan = [
            tagihan.pk
            for tagihan in base_queryset
            if tagihan.sisa_tagihan > 0
        ]
        self.fields['tagihan'].queryset = Tagihan.objects.select_related(
            'siswa', 'jenis', 'semester'
        ).filter(pk__in=available_tagihan).order_by('siswa__nama', 'jenis__nama', 'semester__nama')
        self.fields['tagihan'].label_from_instance = self._tagihan_label

        if tagihan_id and self.fields['tagihan'].queryset.filter(pk=tagihan_id).exists():
            self.fields['tagihan'].initial = tagihan_id
            selected_tagihan = self.fields['tagihan'].queryset.get(pk=tagihan_id)
            self.fields['jumlah_bayar'].initial = selected_tagihan.sisa_tagihan

    def _tagihan_label(self, obj):
        return (
            f"{obj.siswa.nama} - {obj.jenis.nama} - {obj.semester.nama} - "
            f"Sisa Rp {obj.sisa_tagihan:,}"
        )

    def clean(self):
        cleaned_data = super().clean()
        tagihan = cleaned_data.get('tagihan')
        jumlah_bayar = cleaned_data.get('jumlah_bayar')

        if not tagihan or jumlah_bayar is None:
            return cleaned_data

        if jumlah_bayar <= 0:
            self.add_error('jumlah_bayar', 'Jumlah bayar harus lebih dari 0.')
        elif jumlah_bayar > tagihan.sisa_tagihan:
            self.add_error(
                'jumlah_bayar',
                f'Jumlah bayar melebihi sisa tagihan Rp {tagihan.sisa_tagihan:,}.',
            )

        return cleaned_data


class PembayaranMultiForm(forms.Form):
    siswa = forms.ModelChoiceField(
        queryset=Siswa.objects.filter(aktif=True).order_by('nama'),
        label='Siswa',
        empty_label='Pilih siswa',
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all().order_by('-tanggal_mulai'),
        label='Semester',
        required=False,
        empty_label='Pilih semester',
    )
    metode = forms.CharField(label='Metode', max_length=50, required=False)
    keterangan = forms.CharField(label='Keterangan', required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        siswa_id = kwargs.pop('siswa_id', None)
        semester_id = kwargs.pop('semester_id', None)
        super().__init__(*args, **kwargs)

        active_semester = Semester.objects.filter(aktif=True).first()
        if active_semester and not semester_id:
            semester_id = active_semester.pk

        if siswa_id:
            self.fields['siswa'].initial = siswa_id
        if semester_id:
            self.fields['semester'].initial = semester_id

        self.fields['siswa'].widget.attrs.update({
            'data-searchable': 'true',
            'data-search-placeholder': 'Cari siswa berdasarkan nama, kelas, atau NIS',
        })
        self.fields['semester'].widget.attrs.update({
            'data-searchable': 'true',
            'data-search-placeholder': 'Cari semester',
        })
        self.fields['metode'].widget.attrs.update({
            'placeholder': 'Contoh: Tunai, Transfer, QRIS',
        })
        self.fields['keterangan'].widget.attrs.update({'rows': 4})


class BulkTagihanForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.filter(aktif=True),
        label='Semester',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-searchable': 'true',
            'data-search-placeholder': 'Cari semester',
        })
    )
    jenis_pembayaran = forms.ModelMultipleChoiceField(
        queryset=JenisPembayaran.objects.filter(aktif=True, wajib_per_semester=True),
        label='Jenis Pembayaran',
        widget=forms.CheckboxSelectMultiple
    )
    nominal = forms.IntegerField(
        label='Nominal per Siswa',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            **positive_integer_attrs(placeholder='Masukkan nominal per siswa'),
        })
    )
    jatuh_tempo = forms.DateField(
        label='Jatuh Tempo',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        nominal = cleaned_data.get('nominal')
        if nominal is not None and nominal <= 0:
            raise forms.ValidationError("Nominal harus lebih dari 0.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_semester = Semester.objects.filter(aktif=True).first()
        self.fields['semester'].queryset = Semester.objects.filter(aktif=True)
        if active_semester:
            self.fields['semester'].initial = active_semester


class KasKeluarForm(forms.ModelForm):
    class Meta:
        model = KasKeluar
        fields = ['judul', 'kategori', 'jumlah', 'tanggal_pengeluaran', 'semester', 'keterangan']
        widgets = {
            'tanggal_pengeluaran': forms.DateInput(attrs={'type': 'date'}),
            'keterangan': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_semester = Semester.objects.filter(aktif=True).first()
        self.available_jenis_queryset = JenisPembayaran.objects.filter(aktif=True).order_by('nama')
        self.fields['judul'].widget.attrs.update({
            'placeholder': 'Contoh: Belanja ATK semester genap',
        })
        self.fields['kategori'].widget.attrs.update({
            'placeholder': 'Contoh: Honor, Transport, Konsumsi, ATK',
        })
        self.fields['jumlah'].widget.attrs.update({
            **positive_integer_attrs(placeholder='Masukkan nominal tanpa titik atau koma'),
        })
        self.fields['semester'].queryset = Semester.objects.all().order_by('-tanggal_mulai')
        self.fields['semester'].required = False
        self.fields['semester'].widget.attrs.update({
            'data-searchable': 'true',
            'data-search-placeholder': 'Cari semester',
        })
        if active_semester:
            self.fields['semester'].initial = active_semester

    def clean_jumlah(self):
        jumlah = self.cleaned_data.get('jumlah')
        if jumlah is None or jumlah <= 0:
            raise forms.ValidationError('Jumlah pengeluaran harus lebih dari 0.')
        return jumlah

    def _get_list_data(self, key):
        if hasattr(self.data, 'getlist'):
            return self.data.getlist(key)

        value = self.data.get(key, [])
        if isinstance(value, list):
            return value
        if value in (None, ''):
            return []
        return [value]

    def get_allocation_rows(self):
        if self.is_bound:
            jenis_values = self._get_list_data('alokasi_jenis')
            nominal_values = self._get_list_data('alokasi_nominal')
            rows = []
            for jenis_value, nominal_value in zip_longest(jenis_values, nominal_values, fillvalue=''):
                rows.append({
                    'jenis_id': (jenis_value or '').strip(),
                    'nominal': (nominal_value or '').strip(),
                })
            return rows or [{'jenis_id': '', 'nominal': ''}]

        if self.instance.pk:
            allocation_rows = [
                {
                    'jenis_id': str(item.jenis_pembayaran_id),
                    'nominal': str(item.nominal),
                }
                for item in self.instance.alokasi_set.select_related('jenis_pembayaran').all()
            ]
            if allocation_rows:
                return allocation_rows

            if self.instance.jenis_pembayaran_id:
                return [{
                    'jenis_id': str(self.instance.jenis_pembayaran_id),
                    'nominal': str(self.instance.jumlah),
                }]

        return [{'jenis_id': '', 'nominal': ''}]

    def clean(self):
        cleaned_data = super().clean()
        jumlah = cleaned_data.get('jumlah')
        if jumlah is None:
            return cleaned_data

        jenis_values = self._get_list_data('alokasi_jenis')
        nominal_values = self._get_list_data('alokasi_nominal')
        jenis_map = {
            str(item.pk): item
            for item in self.available_jenis_queryset
        }
        allocation_rows = []
        total_alokasi = 0
        seen_jenis = set()

        for jenis_value, nominal_value in zip_longest(jenis_values, nominal_values, fillvalue=''):
            jenis_value = (jenis_value or '').strip()
            nominal_value = (nominal_value or '').strip()

            if not jenis_value and not nominal_value:
                continue

            if not jenis_value:
                raise forms.ValidationError('Pilih jenis pembayaran untuk setiap baris alokasi yang diisi.')

            jenis = jenis_map.get(jenis_value)
            if jenis is None:
                raise forms.ValidationError('Jenis pembayaran pada alokasi tidak valid.')

            if jenis.pk in seen_jenis:
                raise forms.ValidationError(f'Alokasi untuk {jenis.nama} cukup dibuat satu baris saja.')
            seen_jenis.add(jenis.pk)

            if not nominal_value:
                raise forms.ValidationError(f'Nominal alokasi untuk {jenis.nama} wajib diisi.')

            try:
                nominal = int(nominal_value)
            except ValueError:
                raise forms.ValidationError(f'Nominal alokasi untuk {jenis.nama} harus berupa angka.')

            if nominal <= 0:
                raise forms.ValidationError(f'Nominal alokasi untuk {jenis.nama} harus lebih dari 0.')

            allocation_rows.append({
                'jenis': jenis,
                'nominal': nominal,
            })
            total_alokasi += nominal

        if allocation_rows and total_alokasi != jumlah:
            raise forms.ValidationError(
                f'Total alokasi harus sama dengan jumlah pengeluaran, yaitu Rp {jumlah:,}.'
            )

        cleaned_data['allocation_rows'] = allocation_rows
        cleaned_data['total_alokasi'] = total_alokasi
        return cleaned_data
