"""User-facing text in English (default) and Indonesian.

Every string shown in the UI lives here, keyed by an id. Use `tr(key, lang, **params)` outside
Streamlit, or `pdftools.ui.t(key, **params)` inside a page (it picks the language from the session).
Placeholders look like {name}; text that must show a literal placeholder (e.g. the page-number
format "{n}") simply isn't passed that parameter.
"""

from __future__ import annotations

import os

LANGUAGES = {"en": "English", "id": "Bahasa Indonesia"}
DEFAULT_LANG = os.environ.get("PDFTOOLS_LANG", "en") if os.environ.get("PDFTOOLS_LANG", "en") in LANGUAGES else "en"

# key: (English, Indonesian)
STRINGS: dict[str, tuple[str, str]] = {
    # --- app shell ---------------------------------------------------------------------------------
    "nav_home": ("Home", "Beranda"),
    "home_title": ("📄 PDF Tools", "📄 PDF Tools"),
    "home_caption": (
        "Files are processed on the internal server and deleted right after processing.",
        "Semua file diproses di server internal dan langsung dihapus setelah selesai.",
    ),
    "sec_format": ("Size & format", "Ukuran & format"),
    "sec_pages": ("Organize pages", "Susun halaman"),
    "sec_security": ("Security", "Keamanan"),
    # navigation: title + one-line description for the home page
    "nav_compress": ("Compress PDF", "Kompres PDF"),
    "desc_compress": ("Shrink a PDF to a target size, text stays sharp", "Perkecil PDF sampai target ukuran, teks tetap tajam"),
    "nav_pdf2img": ("PDF → Images", "PDF → Gambar"),
    "desc_pdf2img": ("Turn PDF pages into PNG/JPG", "Ubah halaman PDF jadi PNG/JPG"),
    "nav_img2pdf": ("Images → PDF", "Gambar → PDF"),
    "desc_img2pdf": ("Combine photos/scans into a print-ready PDF", "Gabungkan foto/scan jadi PDF siap cetak"),
    "nav_word": ("PDF → Word", "PDF → Word"),
    "desc_word": ("Turn a digital PDF into a Word document", "Ubah PDF digital jadi dokumen Word"),
    "nav_ocrdocx": ("Scanned PDF → Word (OCR)", "PDF Scan → Word (OCR)"),
    "desc_ocrdocx": ("Extract text from scanned PDFs into Word", "Ambil teks dari PDF hasil scan ke Word"),
    "nav_ocrpdf": ("OCR: Searchable PDF", "OCR: PDF Bisa Dicari"),
    "desc_ocrpdf": ("Make scanned PDFs searchable & copyable", "Tambahkan teks ke PDF scan supaya bisa dicari & di-copy"),
    "nav_office": ("Office → PDF", "Office → PDF"),
    "desc_office": ("Word/Excel/PowerPoint to PDF, plus metadata", "Word/Excel/PowerPoint ke PDF, plus metadata"),
    "nav_merge": ("Merge PDF", "Gabung PDF"),
    "desc_merge": ("Combine several PDFs into one", "Gabungkan beberapa PDF jadi satu"),
    "nav_split": ("Split PDF", "Pecah PDF"),
    "desc_split": ("Split by page, page range, or file size", "Pecah per halaman, per rentang, atau per ukuran file"),
    "nav_organize": ("Organize Pages", "Atur Halaman"),
    "desc_organize": ("Reorder, delete, or rotate pages", "Urutkan ulang, hapus, atau putar halaman"),
    "nav_numbers": ("Page Numbers", "Nomor Halaman"),
    "desc_numbers": ("Add page numbers", "Tambahkan nomor halaman"),
    "nav_watermark": ("Watermark", "Watermark"),
    "desc_watermark": ("Add a text watermark (e.g. CONFIDENTIAL, DRAFT)", "Tambahkan teks watermark (mis. RAHASIA, DRAFT)"),
    "nav_unlock": ("Unlock PDF", "Buka Kunci PDF"),
    "desc_unlock": ("Remove a PDF password (you must know it)", "Hapus password dari PDF (password wajib diketahui)"),
    "nav_protect": ("Lock PDF", "Kunci PDF"),
    "desc_protect": ("Add a password & restrict print/copy (AES-256)", "Pasang password & batasi print/copy (AES-256)"),
    "nav_redact": ("Redact Data", "Sensor Data (Redact)"),
    "desc_redact": ("Permanently remove ID numbers, emails, phones, etc.", "Hapus permanen NIK, NPWP, email, nomor HP, dll."),
    "nav_metadata": ("PDF Metadata", "Metadata PDF"),
    "desc_metadata": ("Edit or remove metadata (author, title, etc.)", "Ubah atau hapus metadata (penulis, judul, dll.)"),
    # --- login & errors ----------------------------------------------------------------------------
    "login_title": ("🔐 PDF Tools", "🔐 PDF Tools"),
    "password": ("Password", "Password"),
    "login": ("Sign in", "Masuk"),
    "login_wrong": ("Wrong password.", "Password salah."),
    "queue_wait": ("⏳ Waiting in queue (another job is running)...", "⏳ Menunggu antrian (ada proses lain yang sedang jalan)..."),
    "err_locked": ("🔒 {msg} Unlock it first via **Unlock PDF**.", "🔒 {msg} Buka dulu lewat menu **Buka Kunci PDF**."),
    "err_invalid": ("❌ {msg}", "❌ {msg}"),
    "err_timeout": (
        "⏱ The process took too long and was stopped. Try splitting the PDF first, then process it part by part.",
        "⏱ Proses terlalu lama dan dihentikan. Coba pecah PDF-nya dulu, lalu proses per bagian.",
    ),
    "err_generic": ("❌ Failed to process the file: {err}", "❌ Gagal memproses file: {err}"),
    # errors raised by pdftools.core / pdftools.office (UserError keys)
    "not_pdf": ("This file is not a valid PDF.", "File ini bukan PDF yang valid."),
    "pdf_corrupt": ("The PDF is damaged or cannot be read.", "PDF rusak atau tidak bisa dibaca."),
    "pdf_locked": ("This PDF is password-protected.", "PDF ini terkunci password."),
    "wrong_password": ("Wrong password.", "Password salah."),
    "bad_page_format": ("Unknown page format: '{part}'. Example: 1-3, 5, 8-", "Format halaman tidak dikenal: '{part}'. Contoh: 1-3, 5, 8-"),
    "page_out_of_range": ("Pages {part} are out of range (this PDF has {n} pages).", "Halaman {part} di luar jangkauan (PDF ini {n} halaman)."),
    "no_pages_selected": ("No pages selected.", "Tidak ada halaman yang dipilih."),
    "no_ranges": ("Enter at least one page range.", "Isi minimal satu rentang halaman."),
    "pages_per_file_min": ("Pages per file must be at least 1.", "Jumlah halaman per file minimal 1."),
    "password_required": ("A password to open the file is required.", "Password untuk membuka file wajib diisi."),
    "watermark_text_required": ("Watermark text is required.", "Teks watermark wajib diisi."),
    "page_number_format": ("The format must contain {n}, e.g. Page {n} of {total}", "Format wajib memuat {n}, contoh: Halaman {n} dari {total}"),
    "no_images": ("No images could be processed.", "Tidak ada gambar yang bisa diproses."),
    "libreoffice_missing": ("LibreOffice is not installed on this server.", "LibreOffice tidak terpasang di server ini."),
    "office_convert_failed": (
        "LibreOffice could not convert this file (damaged file or unsupported format).",
        "LibreOffice gagal mengonversi file ini (file rusak atau format tidak didukung).",
    ),
    # --- shared widgets ----------------------------------------------------------------------------
    "upload_pdf": ("Upload PDF", "Upload PDF"),
    "pages_input": ("Pages", "Halaman"),
    "pages_placeholder": ("Leave empty = all pages. Example: 1-3, 7", "Kosongkan = semua halaman. Contoh: 1-3, 7"),
    "processing": ("Processing...", "Memproses..."),
    "preparing": ("Preparing...", "Menyiapkan..."),
    "converting": ("Converting...", "Mengonversi..."),
    "reading_text": ("Reading text...", "Membaca teks..."),
    "done": ("Done", "Selesai"),
    "failed": ("Failed", "Gagal"),
    "download": ("⬇ Download result", "⬇ Download hasil"),
    "download_zip": ("⬇ Download ZIP", "⬇ Download ZIP"),
    "file_list": ("File list", "Daftar file"),
    "format": ("Format", "Format"),
    "seconds": ("s", "dtk"),
    "ocr_missing": (
        "OCR language data (Tesseract) is not installed on this server. Please contact IT.",
        "Data bahasa OCR (Tesseract) belum terpasang di server ini. Hubungi tim IT.",
    ),
    "doc_language": ("Document language", "Bahasa dokumen"),
    "lang_ind": ("Indonesian", "Indonesia"),
    "lang_eng": ("English", "Inggris"),
    "lang_ind+eng": ("Indonesian + English", "Indonesia + Inggris"),
    "meta_title": ("Title", "Judul"),
    "meta_author": ("Author", "Penulis"),
    "meta_subject": ("Subject", "Subjek"),
    "meta_keywords": ("Keywords", "Kata kunci"),
    "meta_creator": ("Creator", "Aplikasi pembuat"),
    "meta_producer": ("Producer", "Producer"),
    # --- compress ----------------------------------------------------------------------------------
    "compress_title": ("🗜 Compress PDF", "🗜 Kompres PDF"),
    "compress_caption": (
        "Shrink a PDF to a target size with the best possible quality. Text and vector graphics are never "
        "turned into images, so they stay sharp and copyable.",
        "Perkecil PDF sampai target ukuran dengan kualitas setinggi mungkin. Teks dan grafik vektor "
        "tidak diubah jadi gambar, jadi tetap tajam dan bisa di-copy.",
    ),
    "target_mb": ("Maximum target size (MB)", "Target ukuran maksimal (MB)"),
    "fallback_label": ("If the target is hard to reach", "Kalau target sulit dicapai"),
    "fallback_single": (
        "Keep 1 file: lower image quality as needed (down to 72 DPI)",
        "Tetap 1 file: turunkan kualitas gambar seperlunya (sampai 72 DPI)",
    ),
    "fallback_split": (
        "Split into several files, keep high quality (min. 100 DPI)",
        "Pecah jadi beberapa file, kualitas tetap tinggi (min. 100 DPI)",
    ),
    "fallback_stop": ("Stop at 100 DPI quality even if above target", "Berhenti di kualitas 100 DPI walau di atas target"),
    "gray_label": ("Convert images to grayscale", "Ubah gambar ke abu-abu"),
    "gray_help": ("For documents that don't need color. Images get much smaller.", "Untuk dokumen yang tidak butuh warna. Ukuran gambar jauh lebih kecil."),
    "compress_button": ("🗜 Compress", "🗜 Kompres"),
    "pdf_summary": ("📄 {pages} pages, {mb} MB, {images} images ({share} of file size)", "📄 {pages} halaman, {mb} MB, {images} gambar ({share} dari ukuran file)"),
    "scanned_suffix": (", scanned", ", hasil scan"),
    "progress_lossless": (
        "Cleaning up the PDF structure and removing duplicates (quality unchanged)...",
        "Membersihkan struktur PDF dan menghapus duplikat (kualitas tidak berubah)...",
    ),
    "progress_attempt": ("Attempt {step}: images at {label}...", "Percobaan {step}: gambar {label}..."),
    "splitting_to_target": ("Splitting into files under the target...", "Memecah file supaya tiap bagian di bawah target..."),
    "metric_original": ("Original size", "Ukuran asli"),
    "metric_result": ("Result", "Hasil"),
    "metric_saved": ("Reduced", "Berkurang"),
    "label_original": ("Original (cannot be reduced)", "Asli (tidak bisa diperkecil)"),
    "split_to_target_ok": ("✅ Split into {n} files, each under {target} MB (quality: {label}).", "✅ Dipecah jadi {n} file, masing-masing di bawah {target} MB (kualitas: {label})."),
    "oversize_pages": ("⚠️ Page(s) {pages} alone already exceed the target.", "⚠️ Halaman {pages} sendirian pun sudah di atas target."),
    "kept_original": (
        "ℹ️ This PDF is already optimal; compression didn't make it smaller, so the original file is returned.",
        "ℹ️ PDF ini sudah optimal; hasil kompres tidak lebih kecil, jadi file asli yang dikembalikan.",
    ),
    "target_met": ("✅ Under the {target} MB target. Quality used: **{label}**.", "✅ Di bawah target {target} MB. Kualitas yang dipakai: **{label}**."),
    "target_missed": (
        "⚠️ The {target} MB target was not reached. This is the smallest result ({label}). Choose **Keep 1 file** "
        "or **Split into several files**, or tick **Convert images to grayscale**.",
        "⚠️ Target {target} MB belum tercapai. Ini hasil terkecil ({label}). Pilih **Tetap 1 file** atau "
        "**Pecah jadi beberapa file**, atau centang **Ubah gambar ke abu-abu**.",
    ),
    "compare_title": ("Comparison of page {page}", "Perbandingan halaman {page}"),
    "compare_caption": (
        "The page with the largest image, i.e. the one most affected by compression. Click an image to enlarge.",
        "Halaman dengan gambar terbesar, yang paling terdampak kompres. Klik gambar untuk memperbesar.",
    ),
    "before": ("Original", "Asli"),
    "after": ("Result", "Hasil"),
    "attempt_details": ("Attempt details", "Detail percobaan"),
    # --- merge -------------------------------------------------------------------------------------
    "merge_title": ("🔗 Merge PDF", "🔗 Gabung PDF"),
    "merge_caption": ("Combine several PDFs into one. Bookmarks from each file are kept.", "Gabungkan beberapa PDF jadi satu. Bookmark dari tiap file tetap dipertahankan."),
    "merge_upload": ("Upload PDFs (at least 2)", "Upload PDF (minimal 2)"),
    "merge_order": ("**File order** (change the numbers if needed):", "**Urutan file** (ubah angka urutan kalau perlu):"),
    "order": ("Order", "Urutan"),
    "bookmark_per_file": ("Add a bookmark for each file name", "Tambahkan bookmark per nama file"),
    "merge_button": ("🔗 Merge", "🔗 Gabungkan"),
    "merging": ("Merging...", "Menggabungkan..."),
    "merge_ok": ("✅ Merged: {pages} pages.", "✅ Berhasil digabung: {pages} halaman."),
    # --- split -------------------------------------------------------------------------------------
    "split_title": ("✂ Split PDF", "✂ Pecah PDF"),
    "split_caption": ("Split a PDF by page, by page ranges, or by maximum file size.", "Pecah PDF per halaman, per rentang halaman, atau per ukuran file maksimal."),
    "split_mode": ("How to split", "Cara memecah"),
    "split_every": ("Every N pages", "Setiap N halaman"),
    "split_ranges": ("By page ranges", "Per rentang halaman"),
    "split_size": ("By maximum file size (e.g. email attachment limit)", "Per ukuran file maksimal (mis. batas lampiran email)"),
    "pages_per_file": ("Pages per file", "Jumlah halaman per file"),
    "ranges_input": ("Page ranges, one file per line (or separate with ;)", "Rentang halaman, satu file per baris (atau pisahkan dengan ;)"),
    "max_mb_per_file": ("Maximum size per file (MB)", "Ukuran maksimal per file (MB)"),
    "split_button": ("✂ Split", "✂ Pecah"),
    "splitting": ("Splitting...", "Memecah..."),
    "split_ok": ("✅ {n} files created.", "✅ Jadi {n} file."),
    "split_oversize": (
        "⚠️ Page(s) {pages} alone exceed the limit. Compress first via **Compress PDF**.",
        "⚠️ Halaman {pages} sendirian sudah di atas batas. Kompres dulu lewat menu **Kompres PDF**.",
    ),
    # --- organize ----------------------------------------------------------------------------------
    "organize_title": ("🗂 Organize Pages", "🗂 Atur Halaman"),
    "organize_caption": ("Reorder, delete, or rotate PDF pages.", "Urutkan ulang, hapus, atau putar halaman PDF."),
    "making_preview": ("Creating preview...", "Membuat pratinjau..."),
    "organize_preview": ("{n} pages. Preview (first 60 pages max):", "{n} halaman. Pratinjau (maks. 60 halaman pertama):"),
    "organize_order": ("Pages to keep, in the new order", "Halaman yang dipakai, sesuai urutan baru"),
    "organize_order_help": (
        "Example: '3, 1-2, 5-' = page 3 first, then 1-2, then 5 to the end (page 4 removed). '10-1' = reversed.",
        "Contoh: '3, 1-2, 5-' = halaman 3 dulu, lalu 1-2, lalu 5 sampai akhir (halaman 4 dibuang). '10-1' = urutan terbalik.",
    ),
    "rotate_pages": ("Rotate pages (page numbers in the RESULT)", "Putar halaman (nomor halaman di HASIL)"),
    "rotate_placeholder": ("e.g. 1, 4-6", "mis. 1, 4-6"),
    "angle": ("Angle", "Sudut"),
    "angle_fmt": ("{a}° clockwise", "{a}° searah jarum jam"),
    "apply": ("🗂 Apply", "🗂 Terapkan"),
    "organize_ok": ("✅ Done: {pages} pages.", "✅ Selesai: {pages} halaman."),
    # --- page numbers ------------------------------------------------------------------------------
    "numbers_title": ("🔢 Page Numbers", "🔢 Nomor Halaman"),
    "numbers_caption": ("Add page numbers to a PDF.", "Tambahkan nomor halaman ke PDF."),
    "position": ("Position", "Posisi"),
    "pos_bottom-center": ("Bottom center", "Bawah tengah"),
    "pos_bottom-right": ("Bottom right", "Bawah kanan"),
    "pos_bottom-left": ("Bottom left", "Bawah kiri"),
    "pos_top-center": ("Top center", "Atas tengah"),
    "pos_top-right": ("Top right", "Atas kanan"),
    "pos_top-left": ("Top left", "Atas kiri"),
    "format_help": (
        "{n} = page number, {total} = page count. Example: 'Page {n} of {total}'",
        "{n} = nomor halaman, {total} = jumlah halaman. Contoh: 'Halaman {n} dari {total}'",
    ),
    "start_at": ("Start at number", "Mulai dari angka"),
    "font_size": ("Font size", "Ukuran huruf"),
    "margin_edge": ("Distance from edge (mm)", "Jarak dari tepi (mm)"),
    "skip_first": ("Don't number the first page (cover)", "Jangan beri nomor di halaman pertama (sampul)"),
    "numbers_button": ("🔢 Add numbers", "🔢 Tambahkan nomor"),
    "numbers_ok": ("✅ Page numbers added.", "✅ Nomor halaman ditambahkan."),
    # --- watermark ---------------------------------------------------------------------------------
    "wm_title": ("💧 Watermark", "💧 Watermark"),
    "wm_caption": (
        "Add a diagonal text watermark in the middle of the page, e.g. CONFIDENTIAL or DRAFT.",
        "Tambahkan teks watermark miring di tengah halaman, misalnya RAHASIA atau DRAFT.",
    ),
    "wm_text": ("Watermark text", "Teks watermark"),
    "wm_default": ("CONFIDENTIAL", "RAHASIA"),
    "opacity": ("Opacity", "Transparansi"),
    "opacity_help": ("Lower = fainter", "Makin kecil makin samar"),
    "color": ("Color", "Warna"),
    "tilt": ("Tilt (°)", "Kemiringan (°)"),
    "wm_size": ("Font size (relative to the page)", "Ukuran huruf (relatif terhadap halaman)"),
    "wm_button": ("💧 Add watermark", "💧 Tambahkan watermark"),
    "wm_ok": ("✅ Watermark added.", "✅ Watermark ditambahkan."),
    # --- images -> pdf -----------------------------------------------------------------------------
    "img_title": ("📷 Images → PDF", "📷 Gambar → PDF"),
    "img_caption": (
        "Combine photos/scans into a PDF. Images are not recompressed (original quality), and phone photos "
        "are rotated automatically.",
        "Gabungkan foto/scan jadi PDF. Gambar tidak dikompres ulang (kualitas asli), dan foto dari HP "
        "otomatis diputar sesuai orientasinya.",
    ),
    "img_upload": ("Upload images (in upload order)", "Upload gambar (urutan sesuai urutan upload)"),
    "paper": ("Paper size", "Ukuran kertas"),
    "paper_original": ("Original image size", "Ukuran asli gambar"),
    "paper_a4": ("A4 (210 x 297 mm)", "A4 (210 x 297 mm)"),
    "paper_f4": ("F4 / Folio (215 x 330 mm)", "F4 / Folio (215 x 330 mm)"),
    "paper_letter": ("Letter (8.5 x 11 in)", "Letter (8.5 x 11 in)"),
    "paper_legal": ("Legal (8.5 x 14 in)", "Legal (8.5 x 14 in)"),
    "margin": ("Margin (mm)", "Margin (mm)"),
    "auto_landscape": ("Use landscape automatically for wide images", "Otomatis landscape untuk gambar yang melebar"),
    "img_button": ("📷 Create PDF", "📷 Buat PDF"),
    "creating_pdf": ("Creating PDF...", "Membuat PDF..."),
    "img_ok": ("✅ PDF created: {pages} pages.", "✅ PDF jadi: {pages} halaman."),
    # --- pdf -> images -----------------------------------------------------------------------------
    "pdf2img_title": ("🖼 PDF → Images", "🖼 PDF → Gambar"),
    "pdf2img_caption": ("Turn PDF pages into PNG or JPG images.", "Ubah halaman PDF jadi gambar PNG atau JPG."),
    "resolution": ("Resolution", "Resolusi"),
    "dpi_hint": ("150 DPI is enough for screens. 300 DPI for printing (larger files).", "150 DPI cukup untuk layar. 300 DPI untuk cetak (file lebih besar)."),
    "pdf2img_button": ("🖼 Convert to images", "🖼 Ubah ke gambar"),
    "rendering": ("Rendering pages...", "Merender halaman..."),
    "pdf2img_ok": ("✅ {n} images ({mb} MB).", "✅ {n} gambar ({mb} MB)."),
    # --- pdf -> word -------------------------------------------------------------------------------
    "word_title": ("📝 PDF → Word", "📝 PDF → Word"),
    "word_caption": (
        "Turn a digital (not scanned) PDF into an editable Word document. For scanned PDFs use "
        "**Scanned PDF → Word (OCR)**.",
        "Ubah PDF digital (bukan hasil scan) jadi dokumen Word yang bisa diedit. Untuk PDF hasil scan, "
        "pakai **PDF Scan → Word (OCR)**.",
    ),
    "word_button": ("📝 Convert to Word", "📝 Ubah ke Word"),
    "word_ok": ("✅ Conversion finished. Please check the layout in Word.", "✅ Konversi selesai. Periksa kembali tata letaknya di Word."),
    # --- ocr ---------------------------------------------------------------------------------------
    "ocrdocx_title": ("🔎 Scanned PDF → Word (OCR)", "🔎 PDF Scan → Word (OCR)"),
    "ocrdocx_caption": (
        "Extract text from scanned PDFs / document photos and save it as Word.",
        "Ambil teks dari PDF hasil scan / foto dokumen, lalu simpan sebagai Word.",
    ),
    "ocrdocx_button": ("🔎 Extract text to Word", "🔎 Ambil teks ke Word"),
    "ocrdocx_ok": (
        "✅ Done. OCR can misread characters; double-check important numbers and names.",
        "✅ Selesai. Hasil OCR bisa ada salah baca; periksa kembali angka dan nama penting.",
    ),
    "ocrpdf_title": ("🔤 OCR: Searchable PDF", "🔤 OCR: PDF Bisa Dicari"),
    "ocrpdf_caption": (
        "Add an invisible text layer to scanned PDFs. The look doesn't change, but the text becomes "
        "searchable (Ctrl+F), copyable, and can be removed via Redact Data.",
        "Tambahkan lapisan teks tak terlihat di PDF hasil scan. Tampilan tidak berubah, tapi teksnya jadi "
        "bisa dicari (Ctrl+F), di-copy, dan disensor lewat menu Sensor Data.",
    ),
    "ocrpdf_upload": ("Upload scanned PDF", "Upload PDF hasil scan"),
    "ocr_all_pages": ("Also OCR pages that already contain text", "OCR juga halaman yang sudah punya teks"),
    "ocr_all_help": ("Usually unnecessary; digital pages are already searchable.", "Biasanya tidak perlu; halaman digital sudah bisa dicari."),
    "ocrpdf_button": ("🔤 Run OCR", "🔤 Proses OCR"),
    "ocrpdf_ok": ("✅ {n} pages OCR'd. Try searching with Ctrl+F in the result.", "✅ {n} halaman di-OCR. Coba cari teks dengan Ctrl+F di PDF hasilnya."),
    "ocrpdf_none": ("ℹ️ All pages already contain text, so nothing was OCR'd.", "ℹ️ Semua halaman sudah punya teks, jadi tidak ada yang di-OCR."),
    # --- office -> pdf -----------------------------------------------------------------------------
    "office_title": ("📄 Office → PDF", "📄 Office → PDF"),
    "office_caption": (
        "Convert Word, Excel, or PowerPoint to PDF and set its metadata.",
        "Ubah Word, Excel, atau PowerPoint jadi PDF, sekaligus atur metadata-nya.",
    ),
    "lo_missing": ("LibreOffice is not installed on this server. Please contact IT.", "LibreOffice belum terpasang di server ini. Hubungi tim IT."),
    "office_upload": ("Upload document", "Upload dokumen"),
    "meta_optional": ("PDF metadata (optional)", "Metadata PDF (opsional)"),
    "meta_empty_hint": (
        "Leave everything empty if you don't want an author name or other info in the PDF.",
        "Kosongkan semua kalau tidak ingin ada nama penulis / info lain di file PDF.",
    ),
    "office_button": ("📄 Convert to PDF", "📄 Ubah ke PDF"),
    "office_ok": ("✅ Conversion finished.", "✅ Konversi selesai."),
    # --- unlock ------------------------------------------------------------------------------------
    "unlock_title": ("🔓 Unlock PDF", "🔓 Buka Kunci PDF"),
    "unlock_caption": (
        "Remove the password from a PDF. You must know the password; this tool does not guess passwords.",
        "Hapus password dari PDF. Password-nya harus Anda ketahui; alat ini tidak menebak password.",
    ),
    "unlock_upload": ("Upload the locked PDF", "Upload PDF yang terkunci"),
    "pdf_password": ("PDF password", "Password PDF"),
    "unlock_button": ("🔓 Unlock", "🔓 Buka kunci"),
    "unlock_ok": ("✅ Password and restrictions (print/copy) removed.", "✅ Password dan pembatasan (print/copy) sudah dihapus."),
    "unlock_not_locked": ("ℹ️ This PDF was not locked.", "ℹ️ PDF ini memang tidak terkunci."),
    # --- protect -----------------------------------------------------------------------------------
    "protect_title": ("🔒 Lock PDF", "🔒 Kunci PDF"),
    "protect_caption": (
        "Add a password (AES-256 encryption) and limit what recipients can do.",
        "Pasang password (enkripsi AES-256) dan batasi apa yang boleh dilakukan penerima.",
    ),
    "pw_open": ("Password to open the file", "Password untuk membuka file"),
    "pw_repeat": ("Repeat password", "Ulangi password"),
    "permissions": ("**Recipient permissions**", "**Izin untuk penerima**"),
    "allow_print": ("Allow printing", "Boleh print"),
    "allow_copy": ("Allow copying text", "Boleh copy teks"),
    "allow_edit": ("Allow editing / filling forms", "Boleh edit / isi form"),
    "owner_pw": ("Owner password (optional)", "Password pemilik (opsional)"),
    "owner_pw_help": (
        "Needed to change these permissions later. If empty, a random one is generated.",
        "Dipakai untuk mengubah izin di atas nanti. Kalau kosong, dibuat acak otomatis.",
    ),
    "pw_short": ("The password is shorter than 8 characters; a longer one is safer.", "Password kurang dari 8 karakter; sebaiknya lebih panjang."),
    "protect_button": ("🔒 Lock PDF", "🔒 Kunci PDF"),
    "pw_mismatch": ("❌ The passwords don't match.", "❌ Password dan ulangan password tidak sama."),
    "locking": ("Locking...", "Mengunci..."),
    "protect_ok": (
        "✅ PDF locked. Send the password through a different channel than the file (e.g. file by email, password by chat).",
        "✅ PDF terkunci. Kirim password lewat jalur berbeda dari file-nya (mis. file via email, password via chat).",
    ),
    # --- redact ------------------------------------------------------------------------------------
    "redact_title": ("⬛ Redact Data", "⬛ Sensor Data (Redact)"),
    "redact_caption": (
        "Permanently remove sensitive data from a PDF. The text is actually deleted from the file, not just "
        "covered with a black box, so it cannot be copied or recovered.",
        "Hapus permanen data sensitif dari PDF. Teksnya benar-benar dihapus dari file, bukan sekadar ditutup "
        "kotak hitam, jadi tidak bisa di-copy atau dipulihkan.",
    ),
    "redact_scan_info": (
        "Digital text only. Scanned PDFs must first go through **OCR: Searchable PDF**.",
        "Hanya untuk teks digital. PDF hasil scan perlu diproses dulu lewat **OCR: PDF Bisa Dicari**.",
    ),
    "redact_presets": ("Automatic redaction", "Sensor otomatis"),
    "preset_nik": ("NIK (16-digit ID number)", "NIK (16 digit)"),
    "preset_npwp": ("NPWP (tax ID)", "NPWP"),
    "preset_email": ("Email", "Email"),
    "preset_phone": ("Indonesian phone number", "Nomor HP Indonesia"),
    "redact_terms": ("Other words / phrases to redact (one per line)", "Kata / kalimat lain yang disensor (satu per baris)"),
    "strip_meta": ("Also remove file metadata (author, title, etc.)", "Hapus juga metadata file (penulis, judul, dll.)"),
    "redact_button": ("⬛ Redact", "⬛ Sensor"),
    "redacting": ("Searching and redacting...", "Mencari dan menyensor..."),
    "redact_ok": (
        "✅ {hits} items redacted on {pages} pages. Please review the result before sending.",
        "✅ {hits} bagian disensor di {pages} halaman. Periksa lagi hasilnya sebelum dikirim.",
    ),
    "redact_none": ("⚠️ No matching text found. If this is a scanned PDF, run OCR first.", "⚠️ Tidak ada teks yang cocok. Kalau PDF hasil scan, jalankan OCR dulu."),
    # --- metadata ----------------------------------------------------------------------------------
    "metadata_title": ("🏷 PDF Metadata", "🏷 Metadata PDF"),
    "metadata_caption": (
        "View, change, or remove PDF metadata (title, author, creating app, etc.).",
        "Lihat, ubah, atau hapus metadata PDF (judul, penulis, aplikasi pembuat, dll.).",
    ),
    "meta_xmp_note": (
        "This file also has XMP metadata; it will be removed on save so old values don't reappear.",
        "File ini juga punya metadata XMP; akan dihapus saat disimpan supaya nilai lama tidak muncul lagi.",
    ),
    "action": ("Action", "Aksi"),
    "meta_edit": ("Edit metadata", "Ubah metadata"),
    "meta_strip": ("Remove all metadata (privacy)", "Hapus semua metadata (privasi)"),
    "save": ("💾 Save", "💾 Simpan"),
    "saving": ("Saving...", "Menyimpan..."),
    "meta_ok": ("✅ Metadata saved.", "✅ Metadata disimpan."),
}


def tr(key: str, lang: str = DEFAULT_LANG, **params) -> str:
    """Translate `key`; unknown keys are returned as-is so a missing string never crashes a page."""
    pair = STRINGS.get(key)
    if pair is None:
        return key
    text = pair[1] if lang == "id" else pair[0]
    for name, value in params.items():
        text = text.replace("{" + name + "}", str(value))
    return text


class UserError(Exception):
    """An error whose message is safe to show to the user. Carries a STRINGS key + parameters."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        super().__init__(tr(key, "en", **params))
