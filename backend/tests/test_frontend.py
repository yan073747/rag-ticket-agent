import unittest
import warnings

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.main import create_app, find_frontend_dir


class FrontendServingTest(unittest.TestCase):
    def test_root_serves_frontend_workspace(self):
        with TestClient(create_app()) as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("企业知识库客服工作台", response.text)
        self.assertIn("上传、切分、向量化", response.text)
        self.assertIn("运营指标", response.text)
        self.assertIn("重置演示数据", response.text)
        self.assertIn('placeholder="请输入要向知识库提问的问题"', response.text)
        self.assertNotIn(">退款需要多长时间？</textarea>", response.text)
        self.assertIn('href="/styles.css"', response.text)
        self.assertIn('src="/app.js"', response.text)

    def test_frontend_assets_are_served(self):
        with TestClient(create_app()) as client:
            css_response = client.get("/styles.css")
            js_response = client.get("/app.js")

        self.assertEqual(css_response.status_code, 200)
        self.assertIn("text/css", css_response.headers["content-type"])
        self.assertEqual(js_response.status_code, 200)
        self.assertIn("javascript", js_response.headers["content-type"])
        self.assertIn("接口在线", js_response.text)
        self.assertIn("正在上传文档", js_response.text)
        self.assertIn("置信度", js_response.text)
        self.assertIn("/admin/reset-demo", js_response.text)
        self.assertIn("候选片段仅供人工处理参考", js_response.text)
        self.assertIn("不是可直接采信的答案来源", js_response.text)
        self.assertIn("resetQuestionWorkspace", js_response.text)

    def test_frontend_dir_can_be_found_in_container_layout(self):
        with self.subTest("container layout"):
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                app_dir = root / "app"
                frontend_dir = root / "frontend"
                app_dir.mkdir()
                frontend_dir.mkdir()
                app_file = app_dir / "main.py"
                app_file.write_text("", encoding="utf-8")

                self.assertEqual(find_frontend_dir(app_file), frontend_dir)


if __name__ == "__main__":
    unittest.main()
