import argparse
import datetime
import json
import pathlib
import urllib.request

SOURCE_URL = "https://yc-oss.github.io/api/companies/all.json"
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def fetch() -> list[dict]:
    with urllib.request.urlopen(SOURCE_URL) as resp:
        return json.load(resp)
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    companies = fetch()
    print(f"fetched {len(companies)} companies")

    if args.dry_run:
        return

    date = datetime.date.today().isoformat()
    out_path = DATA_DIR / f"yc-snapshot-{date}.json"
    out_path.write_text(json.dumps(companies, indent=2))
    print(f"wrote {out_path}")
    print("remember: facets.json and embeddings.npy must be regenerated "
          "from this new snapshot before it replaces the pinned one")


if __name__ == "__main__":
    main()
