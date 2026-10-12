
---

# docs/decisions_log.md

```markdown
# Decisions Log

| ID | Keputusan | Alternatif | Alasan | Dampak | Status |
|---|---|---|---|---|---|
| DECISION-001 | Edit level run + lxml | Rebuild plain text | Preservasi format | Kompleksitas naik | FINAL |
| DECISION-002 | deepcopy rPr | Referensi langsung | Hindari side effect | Aman | FINAL |
| DECISION-003 | Fitur tidak didukung → skipped | Hapus | Transparansi | Temuan lebih banyak | FINAL |
| DECISION-004 | Apply order offset menurun | Offset menaik | Offset stabil | Sederhana | FINAL |
| DECISION-005 | Overlap → conflict | Auto-merge | Hindari konflik | Manual review | FINAL |
| DECISION-006 | Stale check per finding | Global | Akurat | Sedikit lebih lambat | FINAL |
| DECISION-007 | Unknown ≠ typo | Anggap typo | Hindari false positive | Review manual | FINAL |
| DECISION-008 | Threshold 0.85/0.60/0.40 | 0.9/0.7/0.5 | Seimbang | — | FINAL |
| DECISION-009 | Italic dari terminology | Auto English | Hindari over-italic | Manual kurasi | FINAL |
| DECISION-010 | Network guard lokal | Andalkan disiplin | Jaminan | Overhead kecil | FINAL |
| DECISION-011 | Update kamus manual | Auto-download | Privasi | Update manual | FINAL |
| DECISION-012 | Demo publik bukan privat | Klaim privat | Etika | Peringatan jelas | FINAL |
| DECISION-013 | Rollback in-memory | Tulis ulang file | Aman | Memori naik | FINAL |
| DECISION-014 | Blokir unduh jika failed kritis | Izinkan | Kualitas | UX lebih ketat | FINAL |
| DECISION-015 | Daftar fitur MVP | Dinamis | Jelas | Terbatas | FINAL |
| DECISION-016 | Skema YAML final | JSON | Terbaca | — | FINAL |
| DECISION-017 | Angka final batas | — | Konsistensi | — | FINAL |
| DECISION-018 | Sumber kamus final | — | Lisensi | — | OPEN |
| DECISION-019 | Format laporan ringkasan | — | UX | — | OPEN |
| DECISION-020 | Bahasa UI default | — | UX | — | OPEN |