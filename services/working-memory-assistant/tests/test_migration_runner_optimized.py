
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the directory to sys.path so we can import migration_runner
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from migration_runner import WMAMigrationRunner

class TestWMAMigrationRunnerOptimized(unittest.TestCase):
    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.runner = WMAMigrationRunner()
        self.runner.connection = self.mock_conn

    def test_check_existing_tables_all_exist(self):
        # Mock fetchall to return all 4 tables
        self.mock_cursor.fetchall.return_value = [
            ('wma_context_snapshots',),
            ('wma_recovery_sessions',),
            ('wma_recovery_patterns',),
            ('wma_conport_links',)
        ]

        existing = self.runner.check_existing_tables()

        self.assertEqual(len(existing), 4)
        self.assertIn('wma_context_snapshots', existing)
        self.assertEqual(self.mock_cursor.execute.call_count, 1)

    def test_check_existing_tables_some_exist(self):
        # Mock fetchall to return only 2 tables
        self.mock_cursor.fetchall.return_value = [
            ('wma_context_snapshots',),
            ('wma_recovery_sessions',)
        ]

        existing = self.runner.check_existing_tables()

        self.assertEqual(len(existing), 2)
        self.assertIn('wma_context_snapshots', existing)
        self.assertIn('wma_recovery_sessions', existing)
        self.assertNotIn('wma_recovery_patterns', existing)
        self.assertEqual(self.mock_cursor.execute.call_count, 1)

    def test_check_existing_tables_none_exist(self):
        # Mock fetchall to return empty list
        self.mock_cursor.fetchall.return_value = []

        existing = self.runner.check_existing_tables()

        self.assertEqual(len(existing), 0)
        self.assertEqual(self.mock_cursor.execute.call_count, 1)

    def test_verify_migration_success(self):
        # Mock fetchall for tables existence check
        # Then mock fetchall for views existence check
        self.mock_cursor.fetchall.side_effect = [
            [
                ('wma_context_snapshots',),
                ('wma_recovery_sessions',),
                ('wma_recovery_patterns',),
                ('wma_conport_links',)
            ],
            [
                ('wma_recovery_performance',),
                ('wma_snapshot_analytics',)
            ]
        ]
        # Mock fetchone for 4 COUNT(*) checks
        self.mock_cursor.fetchone.side_effect = [[0], [0], [0], [0]]

        success = self.runner.verify_migration()

        self.assertTrue(success)
        # 1 (tables existence) + 4 (counts) + 1 (views existence) = 6
        self.assertEqual(self.mock_cursor.execute.call_count, 6)

    def test_verify_migration_table_missing(self):
        # Mock fetchall for tables existence check (one missing)
        self.mock_cursor.fetchall.return_value = [
            ('wma_context_snapshots',),
            ('wma_recovery_sessions',),
            ('wma_recovery_patterns',)
            # wma_conport_links missing at the end
        ]
        # Mock fetchone for the 3 COUNT(*) checks that will be performed
        self.mock_cursor.fetchone.side_effect = [[0], [0], [0]]

        success = self.runner.verify_migration()

        self.assertFalse(success)
        # 1 (existence check) + 3 (counts for those that exist) = 4
        self.assertEqual(self.mock_cursor.execute.call_count, 4)

if __name__ == '__main__':
    unittest.main()
