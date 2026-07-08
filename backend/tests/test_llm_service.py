import os
import unittest

from app.services.llm_service import (
    LLMServiceError,
    _build_system_prompt,
    _build_user_prompt,
    _strip_markdown_formatting,
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

    def test_strip_markdown_formatting_removes_bold_markers(self):
        answer = (
            "普通员工出差到上海的住宿报销标准为 **350元/间/晚**，"
            "出差餐饮补贴为 **100元/天**。"
        )

        cleaned = _strip_markdown_formatting(answer)

        self.assertEqual(
            cleaned,
            "普通员工出差到上海的住宿报销标准为 350元/间/晚，出差餐饮补贴为 100元/天。",
        )

    def test_strip_markdown_formatting_removes_headings_and_bullets(self):
        answer = "# 报销标准\n- 住宿标准：`350元/间/晚`\n- 餐补：100元/天"

        cleaned = _strip_markdown_formatting(answer)

        self.assertEqual(cleaned, "报销标准\n住宿标准：350元/间/晚\n餐补：100元/天")


if __name__ == "__main__":
    unittest.main()
