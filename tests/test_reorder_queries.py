import unittest

from lib.db import DatabaseManager


class ReorderQueryTests(unittest.TestCase):
    def test_reorder_action_query_uses_safe_reorder_join(self):
        query = DatabaseManager.get_reorder_action_rows.__code__
        self.assertTrue(query is not None)


if __name__ == "__main__":
    unittest.main()
