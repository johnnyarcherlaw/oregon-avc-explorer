from pathlib import Path
import csv
import hashlib
from datetime import date


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "reference" / "source_manifest.csv"

PUBLISHER = "Oregon Department of Justice"

SOURCE_URLS = {
    "2010_omnicare_avc.pdf":
        "https://www.doj.state.or.us/wp-content/uploads/2017/06/12810_filed_omnicare_avc.pdf",

    "2011_united_telecom_avc.pdf":
        "https://www.doj.state.or.us/wp-content/uploads/2017/06/united_telecom_filed_avc_060811.pdf",

    "2021_gustafson_avc.pdf":
        "https://www.doj.state.or.us/wp-content/uploads/2021/10/AVC_Gustafson_and_Company_LLC_2021.pdf",

    "2022_avalon_avc.pdf":
        "https://www.doj.state.or.us/wp-content/uploads/2022/12/AVC_Avalon_2022.pdf",

    "2024_verizon_tracfone_avc.pdf":
        "https://www.doj.state.or.us/wp-content/uploads/2024/05/Verizon-AVC-ACCEPTED-20240509.pdf",
}


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_manifest():
    rows = []

    for pdf in sorted(RAW_DIR.glob("*.pdf")):
        rows.append({
            "filename": pdf.name,
            "source_url": SOURCE_URLS.get(pdf.name, ""),
            "publisher": PUBLISHER,
            "date_acquired": date.today().isoformat(),
            "sha256": sha256_file(pdf),
        })

    with MANIFEST.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filename",
                "source_url",
                "publisher",
                "date_acquired",
                "sha256",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} records to {MANIFEST}")


if __name__ == "__main__":
    build_manifest()