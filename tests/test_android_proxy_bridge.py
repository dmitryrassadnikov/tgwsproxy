import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(
    Path(__file__).resolve().parents[1] / "android" / "app" / "src" / "main" / "python"
))

import android_proxy_bridge  # noqa: E402


class FakeJavaArrayList:
    def __init__(self, items):
        self._items = list(items)

    def size(self):
        return len(self._items)

    def get(self, index):
        return self._items[index]


class AndroidProxyBridgeTests(unittest.TestCase):
    def test_normalize_dc_ip_list_with_python_iterable(self):
        result = android_proxy_bridge._normalize_dc_ip_list([
            "2:149.154.167.220",
            "  ",
            "4:149.154.167.220 ",
        ])

        self.assertEqual(result, [
            "2:149.154.167.220",
            "4:149.154.167.220",
        ])

    def test_normalize_dc_ip_list_with_java_array_list_shape(self):
        result = android_proxy_bridge._normalize_dc_ip_list(FakeJavaArrayList([
            "2:149.154.167.220",
            "4:149.154.167.220",
        ]))

        self.assertEqual(result, [
            "2:149.154.167.220",
            "4:149.154.167.220",
        ])


if __name__ == "__main__":
    unittest.main()
