"""Cross-check the browser audit against NOAA's alternate CSV serialization.

Does not import the production parser/calculator. This verifies implementation,
not independently measured weather: both serializations originate at NOAA.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def verify():
    raw = (ROOT/'data/KSM00047108.csv.gz').read_bytes()
    rows = list(csv.reader(gzip.decompress(raw).decode('ascii').splitlines()))
    daily = {}
    for r in rows:
        if r[0] != 'KSM00047108':
            raise ValueError('Unexpected station')
        if r[2] != 'TMAX':
            continue
        if r[1] in daily:
            raise ValueError('Duplicate CSV date')
        daily[r[1]] = r
    bundle = json.loads((ROOT/'audits.json').read_text())
    checked = []
    for threshold, years in bundle['audits'].items():
        for year, audit in years.items():
            hot = valid = 0
            for day in audit['days']:
                key = day['date'].replace('-', '')
                r = daily.get(key)
                if r:
                    src=day['source']
                    value=None if int(r[3]) == -9999 else int(r[3])
                    if src is None or (src['value_tenths_c'],src['measurement_flag'],src['quality_flag'],src['source_flag']) != (value,r[4].strip(),r[5].strip(),r[6].strip()):
                        raise AssertionError('Raw flag/value mismatch: '+key)
                    if value is None and day['status'] != 'missing':
                        raise AssertionError('Missing sentinel mismatch: '+key)
                    if value is not None and r[5].strip() and day['status'] != 'quality_flagged':
                        raise AssertionError('Quality classification mismatch: '+key)
                if r and int(r[3]) != -9999 and not r[5].strip():
                    valid += 1
                    hot += int(r[3]) >= int(threshold)
                    expected = 'hot' if int(r[3]) >= int(threshold) else 'below'
                    if day['status'] != expected:
                        raise AssertionError((key, expected, day['status']))
                elif day['status'] in ('hot', 'below'):
                    raise AssertionError('Accepted day unsupported by CSV: '+key)
            unknown = 92 - valid
            observed = [audit['calendar_days'], audit['valid_days'], audit['hot_days_lower'], audit['hot_days_upper']]
            expected = [92, valid, hot, hot + unknown]
            if observed != expected:
                raise AssertionError((year,threshold,observed,expected))
            checked.append({'year':int(year),'threshold_tenths_c':int(threshold),'usable':valid,'hot_lower':hot,'hot_upper':hot+unknown})
    return {'status':'PASS','period_audits':len(checked),'calendar_day_checks':sum(len(a['days']) for y in bundle['audits'].values() for a in y.values()),'csv_sha256':hashlib.sha256(raw).hexdigest(),'limits':'Alternate NOAA serialization; not independent observations or independent reviewer.','results':checked}


if __name__=='__main__':
    print(json.dumps(verify(),indent=2))
