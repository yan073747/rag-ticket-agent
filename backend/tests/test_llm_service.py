import os
import unittest

from app.services.llm_service import (
    LLMServiceError,
    _build_system_prompt,
    _build_user_prompt,
    generate_rag_answer,
    is_llm_configured,
)


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

    def test_prompts_require_plain_text_without_markdown(self):
        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(
            "How much is the hotel allowance?",
            [
                {
                    "document_id": 1,
                    "chunk_id": 1,
                    "chunk_index": 0,
                    "content": "Hotel allowance is 350 yuan per night.",
                    "distance": 0.1,
                }
            ],
        )

        self.assertIn("纯文本", system_prompt)
        self.assertIn("不要使用 Markdown", system_prompt)
        self.assertIn("不要使用 Markdown", user_prompt)


if __name__ == "__main__":
    unittest.main()
