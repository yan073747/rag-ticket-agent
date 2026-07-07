import unittest

from app.services.text_splitter import split_text


class TextSplitterTest(unittest.TestCase):
    def test_split_text_creates_overlapping_chunks(self):
        text = "ABCDEFGHIJ" * 5

        chunks = split_text(text, chunk_size=20, chunk_overlap=5)

        self.assertEqual(chunks, [
            "ABCDEFGHIJABCDEFGHIJ",
            "FGHIJABCDEFGHIJABCDE",
            "ABCDEFGHIJABCDEFGHIJ",
        ])
        self.assertEqual(chunks[0][-5:], chunks[1][:5])


if __name__ == "__main__":
    unittest.main()
