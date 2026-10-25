import tempfile
import unittest
from pathlib import Path
from leadops.core import process_csv, score_lead

class TestLeadOps(unittest.TestCase):
    def test_hot(self):
        item = dict(name="A", email="a@example.com", company="C",
                    industry="SaaS", company_size="50", job_title="VP Sales", source="referral")
        result = score_lead(item)
        self.assertEqual((result["score"], result["segment"]), (100, "HOT"))

    def test_duplicate_and_invalid(self):
        data = ("name,email,company,industry,company_size,job_title,source\n"
                "Ana,ana@example.com,Acme,saas,20,CEO,inbound\n"
                "Ana,ANA@example.com,Acme,saas,20,CEO,inbound\n"
                "Bob,invalid,Acme,saas,20,CEO,inbound\n"
                "Sam,sam@example.com,Acme,saas,0,CEO,inbound\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leads.csv"
            path.write_text(data, encoding="utf-8")
            out = process_csv(path)
        self.assertEqual(out["summary"]["processed"], 1)
        self.assertEqual(out["summary"]["rejected"], 3)
        self.assertEqual({e["reason"] for e in out["errors"]},
                         {"duplicate email", "invalid email", "invalid company size"})

    def test_missing_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("name,email\nX,x@example.com\n")
            with self.assertRaises(ValueError):
                process_csv(path)

if __name__ == "__main__":
    unittest.main()
