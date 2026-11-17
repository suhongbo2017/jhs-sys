"""PDF 翻译：上传校验、路径穿越防护、mock 全流程（不调用模型、不花钱）。"""

import time
import unittest

from tests import support
import pdf_translate_jobs


class PdfUploadValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_post_without_files_is_friendly(self):
        resp = self.client.post('/pdf_translate', data={})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('请先选择'.encode('utf-8'), resp.data)

    def test_rejects_disallowed_suffix(self):
        import io
        resp = self.client.post(
            '/pdf_translate',
            data={'files': (io.BytesIO(b'MZ'), 'evil.exe'), 'mock': 'on'},
            content_type='multipart/form-data',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('不支持的文件类型'.encode('utf-8'), resp.data)

    def test_oversized_upload_uses_custom_error_page(self):
        """总大小超限（MAX_CONTENT_LENGTH）要走中文错误页，而不是 Flask 默认英文页。"""
        import io
        original = support.app.config['MAX_CONTENT_LENGTH']
        support.app.config['MAX_CONTENT_LENGTH'] = 1024
        try:
            resp = self.client.post(
                '/pdf_translate',
                data={'files': (io.BytesIO(b'%PDF-1.4' + b'x' * 4096), 'big.pdf')},
                content_type='multipart/form-data',
            )
        finally:
            support.app.config['MAX_CONTENT_LENGTH'] = original
        self.assertEqual(resp.status_code, 413)
        self.assertIn('上传内容过大'.encode('utf-8'), resp.data)


class PdfJobAccessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_status_unknown_job_404(self):
        resp = self.client.get('/pdf_translate/status/nope')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.get_json())

    def test_download_unknown_job_redirects(self):
        resp = self.client.get('/pdf_translate/download/nope/a.pdf')
        self.assertEqual(resp.status_code, 302)

    def test_download_path_traversal_blocked(self):
        job_id, err = pdf_translate_jobs.create_job(
            files=[('a.pdf', support.make_sample_pdf())],
            model_id=pdf_translate_jobs.default_model(), mock=True,
        )
        self.assertIsNone(err, err)
        for name in ['../../../../Windows/win.ini', '..%2f..%2fetc%2fpasswd', '../in/a.pdf']:
            resp = self.client.get(f'/pdf_translate/download/{job_id}/{name}')
            self.assertIn(resp.status_code, (302, 404), f'{name} 未被拦截')
            self.assertNotIn(b'[fonts]', resp.data)


class PdfMockPipelineTest(unittest.TestCase):
    """mock 模式跑完整流水线：文本层路由 + 产物生成 + 下载。"""

    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_mock_job_end_to_end(self):
        import io

        pdf = support.make_sample_pdf('Hello World 测试页')
        resp = self.client.post(
            '/pdf_translate',
            data={
                'files': (io.BytesIO(pdf), 'sample.pdf'),
                'mock': 'on',
                'model': pdf_translate_jobs.default_model(),
                'want_pdf': 'on', 'want_html': 'on', 'want_md': 'on',
            },
            content_type='multipart/form-data',
        )
        self.assertEqual(resp.status_code, 302)
        location = resp.headers['Location']
        from urllib.parse import parse_qs, urlparse

        job_id = parse_qs(urlparse(location).query).get('job', [''])[0]
        self.assertTrue(job_id, location)

        deadline = time.time() + 120
        job = None
        while time.time() < deadline:
            job = self.client.get(f'/pdf_translate/status/{job_id}').get_json()
            if job['status'] in ('done', 'failed'):
                break
            time.sleep(1.0)

        self.assertIsNotNone(job)
        self.assertEqual(job['status'], 'done', job.get('error') or job.get('logs'))
        self.assertEqual(job['progress'], 100)
        self.assertGreaterEqual(len(job['outputs']), 1)

        for out in job['outputs']:
            dl = self.client.get(f"/pdf_translate/download/{job_id}/{out['name']}")
            self.assertEqual(dl.status_code, 200, out['name'])
            self.assertGreater(len(dl.data), 0, out['name'])
            dl.close()


if __name__ == '__main__':
    unittest.main()
