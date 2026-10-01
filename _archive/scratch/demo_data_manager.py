"""Quick demo of data_manager.py functionality."""
from data_manager import DataStore, ImportConfig, DataRecord
import tempfile, os, json

# Create a sample CSV
csv_content = "cve,title,severity\nCVE-2023-1234,Sample Vulnerability,High\nCVE-2023-5678,Another Issue,Medium\nCVE-2023-9012,Lowy Risk Issue,Low\n"

with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write(csv_content)
    tmp = f.name

try:
    ds = DataStore()
    cfg = ImportConfig(
        source_path=tmp,
        table_name="vulns",
        field_mapping={"cve": "cve", "title": "title", "severity": "severity"},
    )
    rows, err = ds.import_csv(tmp, cfg)
    if err:
        print(f"ERROR: {err}")
    else:
        print(f"SUCCESS: imported {rows} rows into '{cfg.table_name}'")
        for rec in ds._tables["vulns"]:
            print(f"  CVE: {rec.get('cve')}, Title: {rec.get('title')}, Severity: {rec.get('severity')}")

    # Sort ascending by CVE
    sorted_recs = ds.sort_table("vulns", "cve", ascending=True)
    print("\nSorted by CVE (ascending):")
    for rec in sorted_recs:
        print(f"  {rec.get('cve')} - {rec.get('title')}")

    # Sort descending by severity
    sorted_recs2 = ds.sort_table("vulns", "severity", ascending=False)
    print("\nSorted by Severity (descending):")
    for rec in sorted_recs2:
        print(f"  {rec.get('severity')} - CVE {rec.get('cve')}")

    # Markdown export
    md = ds.table_to_markdown("vulns")
    print(f"\nMarkdown preview:\n{md}")

    # JSON import demo
    json_content = json.dumps(
        [{"cve": "CVE-2022-9999", "title": "JSON Issue", "severity": "Critical"}, {"cve": "CVE-2022-8888", "title": "Another JSON", "severity": "Low"}]
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write(json_content)
        tmp_json = f.name

    try:
        rows2, err2 = ds.import_json(tmp_json, ImportConfig(source_path=tmp_json, table_name="json_vulns"))
        if err2:
            print(f"\nJSON import ERROR: {err2}")
        else:
            print(f"\nJSON import SUCCESS: {rows2} rows")
            for rec in ds._tables["json_vulns"]:
                print(f"  CVE: {rec.get('cve')}, Title: {rec.get('title')}")
    finally:
        os.unlink(tmp_json)

finally:
    os.unlink(tmp)