import unittest
import itertools
from heatwitness import audit, compare, parse_tmax


def row(value=310, flag=''):
    return {'value_tenths_c': value, 'quality_flag': flag,
            'measurement_flag': '', 'source_flag': 'S'}


class AuditTests(unittest.TestCase):
    def test_same_unknown_period_is_identical(self):
        a=audit({},'2024-06-01','2024-06-03')
        self.assertEqual(compare(a,a)['conclusion'],'SAME_COUNT')

    def test_partial_overlap_rejected(self):
        with self.assertRaises(ValueError):
            compare(audit({},'2024-06-01','2024-06-03'),audit({},'2024-06-02','2024-06-04'))
    def test_bounds_match_all_completions(self):
        # Exhaust all three-day hot/cold/unknown patterns in both periods.
        patterns=list(itertools.product([290,310,None],repeat=3))
        for left,right in itertools.product(patterns,repeat=2):
            a=audit({f'2023-06-0{i+1}':row(v) for i,v in enumerate(left)},'2023-06-01','2023-06-03')
            b=audit({f'2024-06-0{i+1}':row(v) for i,v in enumerate(right)},'2024-06-01','2024-06-03')
            def totals(values):
                return [sum(v>=300 for v in completed) for completed in itertools.product(*[[290,310] if v is None else [v] for v in values])]
            diffs=[y-x for x in totals(left) for y in totals(right)]
            c=compare(a,b)
            self.assertEqual((c['difference_lower'],c['difference_upper']),(min(diffs),max(diffs)))

    def test_missing_is_unknown_not_cold(self):
        a = audit({'2024-06-01': row(310), '2024-06-02': row(None)}, '2024-06-01','2024-06-03')
        self.assertEqual((a['hot_days_lower'], a['hot_days_upper']), (1, 3))
        self.assertEqual([d['status'] for d in a['days']], ['hot','missing','absent'])

    def test_flagged_high_value_cannot_prove_heat(self):
        a = audit({'2024-06-01':row(500,'X')},'2024-06-01','2024-06-01')
        self.assertEqual((a['hot_days_lower'],a['hot_days_upper']), (0,1))

    def test_naive_direction_can_be_unsupported(self):
        before=audit({'2023-06-01':row(),'2023-06-02':row()},'2023-06-01','2023-06-03')
        after=audit({'2024-06-01':row()},'2024-06-01','2024-06-03')
        c=compare(before,after)
        self.assertEqual(c['naive_known_count_difference'],-1)
        self.assertEqual((c['difference_lower'],c['difference_upper']),(-2,1))
        self.assertEqual(c['conclusion'],'UNRESOLVED')

    def test_inclusive_threshold_and_leap_day(self):
        a=audit({'2024-02-29':row(300)},'2024-02-28','2024-03-01')
        self.assertEqual((a['calendar_days'],a['hot_days_lower']), (3,1))

    def test_different_exposure_rejected(self):
        with self.assertRaises(ValueError):
            compare(audit({},'2024-01-01','2024-01-02'),audit({},'2023-01-01','2023-01-01'))

    def test_fixed_width_flags_and_duplicate_rejection(self):
        line='KSM00047108'+'202402'+'TMAX'+f'{300:5d} SX'+f'{-9999:5d}   '*30
        station,data=parse_tmax(line)
        self.assertEqual(station,'KSM00047108')
        self.assertEqual(len(data),29)
        self.assertEqual(data['2024-02-01']['quality_flag'],'S')
        self.assertEqual(data['2024-02-01']['source_flag'],'X')
        with self.assertRaises(ValueError):parse_tmax(line+'\n'+line)


if __name__=='__main__':unittest.main()
