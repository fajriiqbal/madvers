from django import forms

from .models import (
    JenisPembayaran,
    KasKeluar,
    Pembayaran,
    Semester,
    Siswa,
    Tagihan,
)


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


class PembayaranForm(forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = ['tagihan', 'jumlah_bayar', 'metode', 'keterangan']

    def __init__(self, *args, **kwargs):
        siswa_id = kwargs.pop('siswa_id', None)
        tagihan_id = kwargs.pop('tagihan_id', None)
        semester_id = kwargs.pop('semester_id', None)
        super().__init__(*args, **kwargs)
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
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
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
        fields = ['judul', 'kategori', 'jenis_pembayaran', 'jumlah', 'tanggal_pengeluaran', 'semester', 'keterangan']
        widgets = {
            'tanggal_pengeluaran': forms.DateInput(attrs={'type': 'date'}),
            'keterangan': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_semester = Semester.objects.filter(aktif=True).first()
        self.fields['kategori'].widget.attrs.update({
            'placeholder': 'Contoh: Honor, Transport, Konsumsi, ATK',
        })
        self.fields['jenis_pembayaran'].label = 'Alokasi ke Jenis Pembayaran'
        self.fields['jenis_pembayaran'].required = False
        self.fields['jenis_pembayaran'].queryset = JenisPembayaran.objects.filter(aktif=True).order_by('nama')
        self.fields['jenis_pembayaran'].empty_label = 'Pengeluaran umum / tidak terkait jenis tertentu'
        self.fields['jenis_pembayaran'].widget.attrs.update({
            'data-searchable': 'true',
            'data-search-placeholder': 'Cari jenis pembayaran',
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
