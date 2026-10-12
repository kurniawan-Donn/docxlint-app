# Config Schema

## 1. Skema YAML Final

```yaml
version: 1
language: id
limits:
  max_file_size_mb: 10
  max_uncompressed_mb: 100
  max_zip_entries: 2000
  max_compression_ratio: 100
  timeout_seconds: 60
  max_findings: 5000
confidence:
  high: 0.85
  medium: 0.60
  low: 0.40
spelling:
  dictionary_path: config/dictionary_id.txt
  exceptions_path: config/exceptions.csv
  whitelist_path: config/whitelist.txt
  enable_morphology: true
  enable_acronym_detection: true
punctuation:
  check_double_space: true
  check_space_before_punct: true
  check_hyphen: true
repeated_word:
  enabled: true
  min_word_length: 3
foreign_italic:
  terminology_path: config/terminology.csv
  auto_italic: false
formatting:
  font:
    enabled: true
    allowed: ["Times New Roman", "Arial", "Calibri"]
  font_size:
    enabled: true
    allowed: [11, 12]
  margin:
    enabled: false
  line_spacing:
    enabled: false
  paragraph_spacing:
    enabled: false
  indentation:
    enabled: false
  alignment:
    enabled: false
  headings:
    enabled: true
    style_map:
      "Heading 1": 1
      "Heading 2": 2
  lists:
    enabled: true
privacy:
  local_mode: true
  block_network: true
  log_content: false