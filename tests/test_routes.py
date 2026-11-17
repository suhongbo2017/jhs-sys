"""页面可达性冒烟：所有 GET 路由必须 200，404 走自定义错误页。"""

import unittest

from tests import support

ROUTES = [
    '/',
    '/qrcode',
    '/date_tag/',
    '/date_tag_view',
    '/bartender_tag/',
    '/queryMaterial',
    '/LSMqueryMaterial',
    '/pdf_translate',
    '/yunHaiPrint',
    '/jinLiPrint',
    '/jiuMaoPrint',
    '/qianJi',
    '/tongtaiying',
    '/fengzhenchang',
    '/fengzhenchang_copy',
    '/zhidongli',
]


class RouteSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_all_pages_return_200(self):
        failures = {}
        for path in ROUTES:
            resp = self.client.get(path)
            if resp.status_code != 200:
                failures[path] = resp.status_code
            resp.close()
        self.assertEqual(failures, {}, f'以下页面未返回 200: {failures}')

    def test_404_uses_custom_error_page(self):
        resp = self.client.get('/definitely-not-a-route')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('页面未找到'.encode('utf-8'), resp.data)

    def test_date_tag_assets_served(self):
        resp = self.client.get('/date_tag/index.html')
        self.assertEqual(resp.status_code, 200)
        resp.close()

    def test_get_on_query_pages_has_no_prompt(self):
        """GET 直接访问不得弹提示（AGENTS §9-7）。"""
        for path in ['/queryMaterial', '/LSMqueryMaterial', '/yunHaiPrint', '/zhidongli']:
            resp = self.client.get(path)
            self.assertNotIn('请输入查询内容', resp.get_data(as_text=True), path)
            resp.close()

    def test_no_external_cdn_in_rendered_pages(self):
        """内网断外网是硬要求：页面不得引用外网 CDN（AGENTS §9-4）。"""
        for path in ROUTES:
            resp = self.client.get(path)
            body = resp.get_data(as_text=True).lower()
            resp.close()
            for token in ('https://cdn.', 'http://cdn.', 'unpkg.com', 'jsdelivr'):
                self.assertNotIn(token, body, f'{path} 引用了外网资源 {token}')


if __name__ == '__main__':
    unittest.main()
