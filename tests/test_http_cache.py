from __future__ import annotations

import os
import tempfile
import unittest
import urllib.error

from lib import cache, http


class HttpCacheTests(unittest.TestCase):
    def tearDown(self):
        http.configure_cache()
        os.environ.pop("DETECTORACLE_HOME", None)
        os.environ.pop("ISSUEORACLE_HOME", None)

    def test_parse_cache_ttl_seconds(self):
        self.assertEqual(http.parse_cache_ttl_seconds("30s"), 30)
        self.assertEqual(http.parse_cache_ttl_seconds("5m"), 300)
        self.assertEqual(http.parse_cache_ttl_seconds("2h"), 7200)
        self.assertEqual(http.parse_cache_ttl_seconds("7d"), 604800)
        self.assertEqual(http.parse_cache_ttl_seconds("42"), 42)

        with self.assertRaises(ValueError):
            http.parse_cache_ttl_seconds("0s")
        with self.assertRaises(ValueError):
            http.parse_cache_ttl_seconds("forever")

    def test_offline_cache_hit_uses_cached_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DETECTORACLE_HOME"] = tmp
            url = f"{http.GITHUB_API}/rate_limit"
            cache.set("GET", url, {"_data": {"ok": True}}, ttl_seconds=60)
            http.configure_cache(offline_cache=True, cache_ttl_seconds="1h")

            data, meta = http.get_json("/rate_limit")

        self.assertEqual(data, {"ok": True})
        self.assertEqual(meta["source"], "cache")

    def test_offline_cache_miss_does_not_use_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["DETECTORACLE_HOME"] = tmp
            http.configure_cache(offline_cache=True, cache_ttl_seconds="1h")

            with self.assertRaises(urllib.error.URLError):
                http.get_json("/rate_limit")


if __name__ == "__main__":
    unittest.main()
