# Traceability Matrix

| FR/NFR | Desain | Test Case |
|---|---|---|
| FR-01 | UI upload | IT-01 |
| FR-02 | security validate | UT-01, IT-02 |
| FR-03 | docx_reader | IT-03 |
| FR-04 | rule_engine | UT-02..UT-10 |
| FR-05 | data_model | UT-11 |
| FR-06 | UI review | IT-04 |
| FR-07 | docx_writer | IT-05 |
| FR-08 | format_preservation | IT-06 |
| FR-09 | location_mapping stale | UT-12 |
| FR-10 | overlap | UT-13 |
| FR-11 | docx_writer save | IT-07 |
| FR-12 | supported_features | UT-14 |
| FR-13 | config_schema | UT-15 |
| FR-14 | dictionary/terminology | UT-16 |
| FR-15 | reporting | IT-08 |
| FR-16 | formatting rules | UT-17 |
| FR-17 | format repair | IT-09 |
| FR-18 | local_mode_enforcement | UT-18 |
| FR-19 | security demo | IT-10 |
| FR-20 | security cleanup | IT-11 |
| NFR-01 | local_mode_enforcement | UT-18 |
| NFR-02 | security_privacy | IT-11 |
| NFR-03 | security | UT-01, UT-19 |
| NFR-04 | limits | IT-12 |
| NFR-05 | malformed tests | UT-20 |
| NFR-06 | format_preservation | IT-06 |
| NFR-07 | data_model | UT-11 |
| NFR-08 | portability | IT-13 |
| NFR-09 | architecture | Review |
| NFR-10 | security demo | IT-10 |

## Aturan
- Tidak ada FR/NFR tanpa test case.
- Setiap test case punya fixture atau mock.