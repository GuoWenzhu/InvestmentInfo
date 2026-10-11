"""Synthetic fixtures only; never written into production data."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('validate', Path(__file__).parents[1] / 'scripts/validate.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def fixture(**changes):
    event = dict(event_id='test-1', company_id='test-company', round_raw='Series A',
                 round_normalized='A', stage='early', currency='USD', disclosed_date='2026-10-10',
                 collected_at='2026-10-11T10:00:00Z', event_type='equity', status='announced',
                 amount=None, amount_status='undisclosed', financing_date=None, date_precision='unknown',
                 confidence='high', evidence_urls=['https://example.com/news?id=1'],
                 investors=[{'investor_id': 'test-investor', 'role': 'undisclosed'}],
                 hq_country=None, operating_regions=[], sector='test', business_scenario='test',
                 event_group_id=None, historical_backfill=False)
    event.update(changes)
    return event


class ValidationTests(unittest.TestCase):
    def test_schedule_rejects_conflicting_mode_and_timezone(self):
        approved = dict(mode='autopilot', schedule_enabled=True,
                        autopilot_id='050525a9-5f7a-4de2-9558-05efaf6fe8e1',
                        timezone='Asia/Shanghai',
                        schedule={'cron': '0 8 * * *', 'timezone': 'Asia/Shanghai'})
        v.validate_project(approved)
        v.validate_project(dict(mode='manual', schedule_enabled=False))
        for changes in ({'mode': 'manual'}, {'schedule_enabled': False},
                        {'autopilot_id': 'invalid'}, {'timezone': 'UTC'},
                        {'schedule': {'cron': '0 8 * * *', 'timezone': 'UTC'}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                v.validate_project(dict(approved, **changes))

    def test_undisclosed_is_not_zero(self):
        v.validate_event(fixture())
        with self.assertRaises(ValueError):
            v.validate_event(fixture(amount=0))

    def test_url_preserves_semantics(self):
        self.assertEqual(v.canonical_url('https://example.com/a?id=1&utm_source=x#top'),
                         'https://example.com/a?id=1')
        self.assertNotEqual(v.canonical_url('https://example.com/a?id=1'),
                            v.canonical_url('https://example.com/a?id=2'))

    def test_extension_requires_review(self):
        events = [fixture(), fixture(event_id='test-2', round_raw='Series A extension')]
        self.assertEqual(v.validate_events(events), [['test-1', 'test-2']])
        self.assertEqual(len(events), 2)

    def test_two_rounds_and_debt_separate(self):
        self.assertEqual(v.validate_events([fixture(), fixture(event_id='test-2', round_normalized='B'),
                                           fixture(event_id='test-3', event_type='debt')]), [])

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            v.validate_events([fixture(), fixture()])

    def test_invalid_dates_currency_and_role(self):
        for changes in ({'disclosed_date': '2026-02-30'}, {'currency': 'usd'},
                        {'collected_at': '2026-10-11T10:00:00'},
                        {'investors': [{'investor_id': 'x', 'role': 'guessed'}]},
                        {'event_type': 'directory'}, {'amount': True, 'amount_status': 'exact'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                v.validate_event(fixture(**changes))


if __name__ == '__main__':
    unittest.main()
