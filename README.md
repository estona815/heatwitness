# HeatWitness

A local, reproducible audit of hot-day comparisons when weather data is incomplete.
Prepared for IEEE ClimateChain 2026, Climate Data & Environmental Monitoring track.
A reproducible one-station prototype. Publication is not evidence of contest acceptance.

## The question

Did the number of days at or above a chosen daily maximum temperature increase?
A plain count silently treats missing observations as days below the threshold.
HeatWitness retains every calendar day, checks NOAA quality flags, and calculates
the sharp possible bounds without imputing observations.

For a period with H accepted hot days and U unknown days, the count is in [H,H+U].
For equal-length periods A and B, the difference is in [B.lower-A.upper,
B.upper-A.lower]. Only a wholly positive/negative interval supports a direction.
These are worst-case missing-data bounds, **not statistical confidence intervals**.

## Reproduce

Python 3.9+; standard library only; no installation, key, network access or API charge.

```sh
python3 -m unittest -v test_heatwitness.py
python3 heatwitness.py
python3 heatwitness.py --after 2022-06-01 2022-08-31
python3 heatwitness.py --after 2023-06-01 2023-08-31
python3 build_data.py
python3 verify_csv.py
python3 -m http.server 4189 --bind 127.0.0.1
```

Open http://127.0.0.1:4189/ to choose two summers (2010–2025), select a
threshold (30/32/35°C), inspect the calendar and download the complete audit JSON.
The checked-in browser dataset contains 48 source-derived period audits. It can be
rebuilt with `build_data.py`. Browser control and export were exercised locally.
`verify_csv.py` uses a separately implemented parser to compare all 48 audits
and 4,416 date entries against NOAA's alternate CSV file. The stored result is
`csv-crosscheck-v002.json`. This is a serialization cross-check of the same NOAA
database, not independent observations or an independent reviewer.

The result contains the original source SHA-256 and every day's raw numeric value,
measurement, quality and source flags. Missing rows, -9999 and failed quality checks
remain distinct explanations, all treated as unknown for the count.

## Source and limits

NOAA GHCN-Daily v3, SEOUL CITY KSM00047108. Download metadata and exact raw hash:
`data/provenance.json`; original format description: `data/ghcn-readme.txt`.
Dataset DOI: https://doi.org/10.7289/V5D21VHZ
Format: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt

30°C is a demonstration threshold chosen for this prototype, not an official
heatwave definition. One station does not represent the city; two summers do not
establish a climate trend, climate attribution, health risk, or avoided emissions.
An empty period means absent usable values in this downloaded series, not proof
that the weather service never observed the temperatures. Hashes identify bytes;
they do not certify measurement truth. There is no blockchain or trained AI model
in this version. Codex assisted the concept, code, tests and writing.

## Why this approach

Alternative 1: impute missing observations from nearby stations. Potentially useful,
but adds model assumptions and requires careful validation before comparison.
Alternative 2: publish a single count after dropping bad observations. Simpler,
but hides unequal coverage. Selected approach: carry uncertainty into the claim
and provide a replayable audit. It makes less ambitious claims with clear evidence.

Largest remaining weakness: this is a one-station demonstration with no user study.
A useful next validation is an additional station or independently sourced archive.
A 3 minute 14.53 second narrated demonstration of actual app screenshots has been
prepared. The 390px layout was visually checked in an iframe; this is not native
phone or touch testing. No award probability or measured climate benefit is claimed.
