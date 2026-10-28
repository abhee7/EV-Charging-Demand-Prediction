import os
import csv
import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests


BASE_URL = "https://ev.caltech.edu/api/v1/"

SITES = {
    "caltech": "caltech",
    "jpl": "jpl",
    "office001": "office1",
}

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = 12
TIMEOUT = (15, 180)

# Caltech already has pages 1-675 saved.
# JPL and Office 1 have not been downloaded yet.
START_PAGES = {
    "caltech": 676,
    "jpl": 1,
    "office001": 1,
}


def get_token():
    token = os.getenv("ACN_API_TOKEN")

    if not token:
        raise RuntimeError(
            "ACN_API_TOKEN is not set.\n"
            'Run: $env:ACN_API_TOKEN="YOUR_NEW_TOKEN"'
        )

    return token


def request_with_retry(session, url, auth, site_id, page):

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            print(
                f"[{site_id}] Requesting page {page} "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = session.get(
                url,
                auth=auth,
                headers={"Accept": "application/json"},
                timeout=TIMEOUT,
            )

            # Explicit handling for temporary server errors.
            if response.status_code in (502, 503, 504):

                print(
                    f"[{site_id}] Server returned "
                    f"HTTP {response.status_code}"
                )

                if attempt < MAX_RETRIES:

                    wait_time = min(
                        10 * attempt,
                        120
                    )

                    print(
                        f"[{site_id}] Waiting "
                        f"{wait_time} seconds before retry..."
                    )

                    time.sleep(wait_time)
                    continue

            response.raise_for_status()

            return response

        except requests.RequestException as e:

            print(
                f"[{site_id}] Request failed: "
                f"{type(e).__name__}: {e}"
            )

            if attempt == MAX_RETRIES:
                raise

            wait_time = min(
                10 * attempt,
                120
            )

            print(
                f"[{site_id}] Retrying in "
                f"{wait_time} seconds..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        f"[{site_id}] Unable to download page {page}"
    )


def flatten_value(value):

    if isinstance(value, (dict, list)):

        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return value


def append_sessions_to_csv(output_file, sessions):

    if not sessions:
        return

    file_exists = output_file.exists()

    fieldnames = set()

    for session in sessions:
        fieldnames.update(session.keys())

    fieldnames = sorted(fieldnames)

    if file_exists:

        with open(
            output_file,
            "r",
            newline="",
            encoding="utf-8",
        ) as f:

            reader = csv.reader(f)
            existing_header = next(reader)

        fieldnames = sorted(
            set(existing_header).union(fieldnames)
        )

        # If schema changes, rewrite the existing file.
        if fieldnames != existing_header:

            with open(
                output_file,
                "r",
                newline="",
                encoding="utf-8",
            ) as f:

                reader = csv.DictReader(f)
                old_rows = list(reader)

            with open(
                output_file,
                "w",
                newline="",
                encoding="utf-8",
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                )

                writer.writeheader()

                for row in old_rows:
                    writer.writerow(row)

    with open(
        output_file,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        for session in sessions:

            row = {
                key: flatten_value(
                    session.get(key)
                )
                for key in fieldnames
            }

            writer.writerow(row)


def download_site(
    site_id,
    output_name,
    token,
):

    output_file = (
        OUTPUT_DIR /
        f"acndata_{output_name}.csv"
    )

    start_page = START_PAGES.get(
        site_id,
        1
    )

    url = urljoin(
        BASE_URL,
        f"sessions/{site_id}?page={start_page}",
    )

    auth = (token, "")

    total_sessions = 0
    page = start_page

    print()
    print("=" * 60)
    print(
        f"Starting {site_id} "
        f"from page {start_page}"
    )
    print("=" * 60)

    with requests.Session() as session:

        while url:

            response = request_with_retry(
                session,
                url,
                auth,
                site_id,
                page,
            )

            data = response.json()

            sessions = data.get(
                "_items",
                []
            )

            if not sessions:

                print(
                    f"[{site_id}] "
                    f"No sessions returned."
                )

                break

            append_sessions_to_csv(
                output_file,
                sessions,
            )

            total_sessions += len(
                sessions
            )

            print(
                f"[{site_id}] received "
                f"{len(sessions)} sessions "
                f"(this run: "
                f"{total_sessions})"
            )

            next_link = (
                data
                .get("_links", {})
                .get("next")
            )

            if (
                next_link
                and next_link.get("href")
            ):

                url = urljoin(
                    BASE_URL,
                    next_link["href"],
                )

                page += 1

                time.sleep(1)

            else:

                url = None

    print()
    print(
        f"[{site_id}] COMPLETE"
    )

    print(
        f"Saved to: {output_file}"
    )

    print()


def main():

    token = get_token()

    print("=" * 60)
    print("ACN-Data Downloader")
    print("RESUMABLE + RETRY ENABLED")
    print("=" * 60)

    for site_id, output_name in SITES.items():

        download_site(
            site_id,
            output_name,
            token,
        )

    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()