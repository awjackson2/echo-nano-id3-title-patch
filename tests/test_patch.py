import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import apply_patch


class PatchTests(unittest.TestCase):
    def test_patch_is_exactly_44_bytes(self):
        self.assertEqual(len(apply_patch.ORIGINAL_PATCH), 44)
        self.assertEqual(len(apply_patch.REPLACEMENT_PATCH), 44)
        self.assertNotEqual(apply_patch.ORIGINAL_PATCH, apply_patch.REPLACEMENT_PATCH)

    def test_crc_reference_vector(self):
        self.assertEqual(apply_patch.crc32_rknano(b"123456789"), 0x889A9615)

    def test_wrong_image_is_rejected(self):
        with self.assertRaises(apply_patch.InvalidFirmware):
            apply_patch.validate_source(b"not firmware")

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "stock.img")
            output = Path(directory, "output.img")
            source.write_bytes(b"source")
            output.write_bytes(b"keep me")
            with patch.object(apply_patch, "build_image") as builder:
                self.assertEqual(apply_patch.main([str(source), str(output)]), 1)
                builder.assert_not_called()
            self.assertEqual(output.read_bytes(), b"keep me")

    @unittest.skipUnless(os.environ.get("ECHO_NANO_STOCK_IMAGE"), "set ECHO_NANO_STOCK_IMAGE for integration test")
    def test_official_image_builds_verified_output(self):
        source = Path(os.environ["ECHO_NANO_STOCK_IMAGE"]).read_bytes()
        output = apply_patch.build_image(source)
        self.assertEqual(apply_patch.sha256(source), apply_patch.SOURCE_SHA256)
        self.assertEqual(apply_patch.sha256(output), apply_patch.OUTPUT_SHA256)
        changed = [index for index, pair in enumerate(zip(source, output)) if pair[0] != pair[1]]
        self.assertTrue(all(
            apply_patch.PATCH_OFFSET <= index < apply_patch.PATCH_OFFSET + 44
            or index >= len(source) - 4
            for index in changed
        ))


if __name__ == "__main__":
    unittest.main()
