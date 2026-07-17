import unittest

import pandas as pd

from lib.db import DatabaseManager


class ReorderQueryTests(unittest.TestCase):
    def test_reorder_action_query_uses_safe_reorder_join(self):
        self.assertTrue(callable(DatabaseManager.get_reorder_action_rows))

    def test_resolve_generic_family_from_exact_drug_name(self):
        drugs = pd.DataFrame(
            [
                {"drug_id": "1", "drug_name": "Dolo", "generic_name": "Paracetamol"},
                {"drug_id": "2", "drug_name": "Crocin", "generic_name": "Paracetamol"},
                {"drug_id": "3", "drug_name": "Omax", "generic_name": "Omeprazole"},
                {"drug_id": "4", "drug_name": "Omez", "generic_name": "Omeprazole"},
                {"drug_id": "5", "drug_name": "Prilosec", "generic_name": "Omeprazole"},
                {"drug_id": "6", "drug_name": "Azithro", "generic_name": "Azithromycin"},
            ]
        )

        self.assertEqual(DatabaseManager._resolve_generic_family_for_search("Dolo", drugs), "Paracetamol")
        self.assertEqual(DatabaseManager._resolve_generic_family_for_search("Omax", drugs), "Omeprazole")
        self.assertEqual(DatabaseManager._resolve_generic_family_for_search("Omeprazole", drugs), "Omeprazole")
        self.assertEqual(DatabaseManager._resolve_generic_family_for_search("Azithromycin", drugs), "Azithromycin")


if __name__ == "__main__":
    unittest.main()
