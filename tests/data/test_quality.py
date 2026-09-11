import csv
import io
import unittest
import zipfile

from dcabot.data_adapters.quality import DataQualityError, _IssueCollector, quality_from_bytes


def bar_csv(*rows: str) -> bytes:
    return ("open_time_us,close_time_us,open,high,low,close,base_volume,is_closed\n" + "\n".join(rows) + "\n").encode()


class QualityTests(unittest.TestCase):
    def test_valid_bars_report_hash_schema_and_observed_gap(self):
        report = quality_from_bytes(
            "bars.csv",
            bar_csv(
                "1700000000000000,1700000060000000,100,101,99,100.5,2,true",
                "1700000060000000,1700000120000000,100.5,102,100,101,3,true",
                "1700000180000000,1700000240000000,101,103,100,102,4,true",
            ),
        )
        self.assertEqual(report["status"], "PASS_WITH_WARNINGS")
        self.assertEqual(report["kind"], "bar")
        self.assertIsNone(report["symbol"])
        self.assertEqual(report["symbols"], [])
        self.assertEqual(report["row_count"], 3)
        self.assertEqual(report["timestamp"]["unit"], "microseconds")
        self.assertEqual(report["timestamp"]["timezone"], "UTC")
        self.assertEqual(report["gaps"]["count"], 1)
        self.assertEqual(len(report["source_sha256"]), 64)

    def test_same_duplicate_is_counted_and_conflict_is_rejected(self):
        row = "1700000000000000,1700000060000000,100,101,99,100.5,2,true"
        same = quality_from_bytes("bars.csv", bar_csv(row, row))
        self.assertEqual(same["duplicates"]["same"], 1)
        self.assertEqual(same["status"], "PASS_WITH_WARNINGS")
        conflict = quality_from_bytes("bars.csv", bar_csv(row, row.replace(",2,true", ",3,true")))
        self.assertEqual(conflict["status"], "REJECTED")
        self.assertEqual(conflict["duplicates"]["conflicts"], 1)

    def test_mixed_symbols_and_open_bars_are_rejected(self):
        content = bar_csv(
            "1700000000000000,1700000060000000,100,101,99,100.5,2,true"
        ).decode().replace(
            "is_closed\n",
            "is_closed,symbol\n",
        ).replace(
            "2,true\n",
            "2,true,BTCUSDT\n",
        )
        content += "1700000060000000,1700000120000000,100.5,102,100,101.5,3,false,ETHUSDT\n"

        report = quality_from_bytes("bars.csv", content.encode())

        self.assertEqual(report["status"], "REJECTED")
        self.assertEqual(report["symbols"], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(
            {issue["code"] for issue in report["issues"]},
            {"mixed_symbol", "bar_not_closed"},
        )

    def test_zip_requires_one_safe_csv_candidate(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("nested/bars.csv", bar_csv("1700000000000000,1700000060000000,100,101,99,100.5,2,true"))
        report = quality_from_bytes("bars.zip", output.getvalue())
        self.assertEqual(report["source_filename"], "bars.csv")
        traversal = io.BytesIO()
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../bars.csv", bar_csv("1700000000000000,1700000060000000,100,101,99,100.5,2,true"))
        with self.assertRaises(DataQualityError):
            quality_from_bytes("bars.zip", traversal.getvalue())
        multiple = io.BytesIO()
        with zipfile.ZipFile(multiple, "w") as archive:
            archive.writestr("one.csv", bar_csv("1700000000000000,1700000060000000,100,101,99,100.5,2,true"))
            archive.writestr("two.csv", bar_csv("1700000000000000,1700000060000000,100,101,99,100.5,2,true"))
        with self.assertRaises(DataQualityError):
            quality_from_bytes("bars.zip", multiple.getvalue())

    def test_malformed_or_unsupported_files_are_not_silently_accepted(self):
        with self.assertRaises(DataQualityError):
            quality_from_bytes("bars.txt", b"anything")
        with self.assertRaises(DataQualityError):
            quality_from_bytes("bars.csv", b"\xff\xfe\x00")
        report = quality_from_bytes("bars.csv", b"open,high\n100,101\n")
        self.assertEqual(report["status"], "REJECTED")
        self.assertEqual(report["issues"][0]["code"], "unsupported_schema")

    def test_many_quality_issues_keep_bounded_sample_and_total_counts(self):
        invalid_rows = ["bad,bad,bad,bad,bad,bad,false"] * 210

        report = quality_from_bytes("bars.csv", bar_csv(*invalid_rows))

        self.assertEqual(len(report["issues"]), 200)
        self.assertTrue(report["issues_truncated"])
        self.assertEqual(report["issue_count"], 1_681)
        self.assertEqual(report["error_count"], 1_680)
        self.assertEqual(report["warning_count"], 1)

    def test_issue_sample_messages_are_bounded_by_utf8_bytes(self):
        collector = _IssueCollector()
        collector.append({"code": "test", "severity": "error", "message": "ş" * 1_000})

        self.assertLessEqual(len(collector[0]["message"].encode("utf-8")), 1_024)
