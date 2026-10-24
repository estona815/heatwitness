"""Reproducible GHCN-Daily hot-day comparison; Python standard library only."""
import argparse
import calendar
import datetime as dt
import hashlib
import json
from pathlib import Path


def parse_tmax(text):
    records = {}
    stations = set()
    for line in text.splitlines():
        if len(line) != 269:
            raise ValueError('GHCN record must contain exactly 269 characters')
        stations.add(line[:11])
        if line[17:21] != 'TMAX':
            continue
        year, month = int(line[11:15]), int(line[15:17])
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            cell = line[21 + (day - 1) * 8:29 + (day - 1) * 8]
            value = int(cell[:5])
            date = dt.date(year, month, day).isoformat()
            if date in records:
                raise ValueError('Duplicate TMAX date: ' + date)
            records[date] = {'value_tenths_c': None if value == -9999 else value,
                             'measurement_flag': cell[5].strip(),
                             'quality_flag': cell[6].strip(),
                             'source_flag': cell[7].strip()}
    if len(stations) != 1:
        raise ValueError('Exactly one station required')
    return next(iter(stations)), records


def audit(records, start, end, threshold_tenths_c=300):
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    if first > last:
        raise ValueError('Start must precede end')
    if not isinstance(threshold_tenths_c, int):
        raise ValueError('Threshold must be integer tenths Celsius')
    days, hot, valid = [], 0, 0
    for offset in range((last - first).days + 1):
        date = (first + dt.timedelta(days=offset)).isoformat()
        record = records.get(date)
        if record is None:
            status = 'absent'
        elif record['value_tenths_c'] is None:
            status = 'missing'
        elif record['quality_flag']:
            status = 'quality_flagged'
        else:
            valid += 1
            status = 'hot' if record['value_tenths_c'] >= threshold_tenths_c else 'below'
            hot += status == 'hot'
        days.append({'date': date, 'status': status, 'source': record})
    unknown = len(days) - valid
    return {'start': start, 'end': end, 'threshold_tenths_c': threshold_tenths_c,
            'calendar_days': len(days), 'valid_days': valid, 'unknown_days': unknown,
            'hot_days_lower': hot, 'hot_days_upper': hot + unknown,
            'coverage': valid / len(days), 'days': days}


def compare(before, after):
    if before['calendar_days'] != after['calendar_days']:
        raise ValueError('Compare equal calendar exposure only')
    if before['threshold_tenths_c'] != after['threshold_tenths_c']:
        raise ValueError('Threshold mismatch')
    if before != after and max(before['start'],after['start']) <= min(before['end'],after['end']):
        raise ValueError('Partially overlapping periods require a shared-day analysis')
    lower = after['hot_days_lower'] - before['hot_days_upper']
    upper = after['hot_days_upper'] - before['hot_days_lower']
    if before == after:
        lower = upper = 0
    conclusion = ('MORE_HOT_DAYS' if lower > 0 else 'FEWER_HOT_DAYS' if upper < 0
                  else 'SAME_COUNT' if lower == upper == 0 else 'UNRESOLVED')
    return {'difference_lower': lower, 'difference_upper': upper,
            'conclusion': conclusion,
            'naive_known_count_difference': after['hot_days_lower'] - before['hot_days_lower'],
            'interpretation': 'Worst-case missing-data bounds, not confidence intervals. '
             'A two-period comparison cannot establish a climate trend or attribution.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=Path(__file__).parent/'data/KSM00047108.dly')
    parser.add_argument('--before', nargs=2, default=['2014-06-01', '2014-08-31'])
    parser.add_argument('--after', nargs=2, default=['2024-06-01', '2024-08-31'])
    parser.add_argument('--threshold-tenths-c', type=int, default=300)
    args = parser.parse_args()
    raw = args.data.read_bytes()
    station, records = parse_tmax(raw.decode('ascii'))
    before = audit(records, *args.before, args.threshold_tenths_c)
    after = audit(records, *args.after, args.threshold_tenths_c)
    result = {'schema': 'heatwitness/v1', 'station': station,
              'source_sha256': hashlib.sha256(raw).hexdigest(),
              'before': before, 'after': after, 'comparison': compare(before, after)}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
