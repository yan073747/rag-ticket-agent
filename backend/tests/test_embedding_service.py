import unittest

from app.services.embedding_service import embed_text


class EmbeddingServiceTest(unittest.TestCase):
    def test_embed_text_returns_stable_fixed_size_vector(self):
        first_vector = embed_text("Refund policy")
        second_vector = embed_text("Refund policy")

        self.assertEqual(len(first_vector), 64)
        self.assertEqual(first_vector, second_vector)
        self.assertTrue(any(value != 0 for value in first_vector))

    def test_related_word_forms_are_closer_than_unrelated_words(self):
        query_vector = embed_text("refund")
        related_vector = embed_text("refunds")
        unrelated_vector = embed_text("warranty")

        related_score = sum(
            query_value * related_value
            for query_value, related_value in zip(query_vector, related_vector)
        )
        unrelated_score = sum(
            query_value * unrelated_value
            for query_value, unrelated_value in zip(query_vector, unrelated_vector)
        )

        self.assertGreater(related_score, unrelated_score)

    def test_chinese_query_is_closer_to_matching_chinese_policy(self):
        query_vector = embed_text("什么时候可以开发票")
        invoice_vector = embed_text("发票政策：客户可以在订单完成后 30 天内申请开具发票。")
        refund_vector = embed_text("退款政策：客户提交退款申请后，客服会在 7 个工作日内完成处理。")

        invoice_score = sum(
            query_value * invoice_value
            for query_value, invoice_value in zip(query_vector, invoice_vector)
        )
        refund_score = sum(
            query_value * refund_value
            for query_value, refund_value in zip(query_vector, refund_vector)
        )

        self.assertGreater(invoice_score, refund_score)


if __name__ == "__main__":
    unittest.main()
