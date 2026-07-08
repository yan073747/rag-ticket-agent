import os
import unittest

from app.services.llm_service import LLMServiceError, generate_rag_answer, is_llm_configured


class LLMServiceTest(unittest.TestCase):
    def test_missing_deepseek_api_key_disables_llm(self):
        original_api_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            self.assertFalse(is_llm_configured())
            with self.assertRaises(LLMServiceError):
                generate_rag_answer(
                    "How long do refunds take?",
                    [
                        {
                            "document_id": 1,
                            "chunk_id": 1,
                            "chunk_index": 0,
                            "content": "Refunds are handled within 7 business days.",
                            "distance": 0.1,
                        }
                    ],
                )
        finally:
            if original_api_key is not None:
                os.environ["DEEPSEEK_API_KEY"] = original_api_key


if __name__ == "__main__":
    unittest.main()
