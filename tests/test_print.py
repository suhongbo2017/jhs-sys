"""打印路由行为测试：空输入、命中、未命中、多单号（数据层打桩）。"""

import unittest
from unittest.mock import patch

import pandas as pd

from tests import support
import server_connect

PRINT_ROUTES = [
    ('/yunHaiPrint', 1),
    ('/jinLiPrint', 2),
    ('/jiuMaoPrint', 3),
    ('/qianJi', 4),
    ('/tongtaiying', 5),
    ('/fengzhenchang', 6),
    ('/fengzhenchang_copy', 6),
]


class PrintRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_post_without_input_flashes_prompt(self):
        for path, _ in PRINT_ROUTES:
            resp = self.client.post(path, data={'inputEntry': ''})
            self.assertEqual(resp.status_code, 200, path)
            self.assertIn('请输入查询内容', resp.get_data(as_text=True), path)

    def test_post_unknown_bill_number_is_friendly(self):
        with patch.object(server_connect, 'query_SEord', return_value=pd.DataFrame()):
            for path, _ in PRINT_ROUTES:
                resp = self.client.post(path, data={'inputEntry': 'JHS9999999'})
                self.assertEqual(resp.status_code, 200, path)
                self.assertIn('未查询到数据', resp.get_data(as_text=True), path)

    def test_post_hit_renders_rows(self):
        """每个 codeName 都要能渲染出自己的模板（列名与模板字段对齐）。"""
        for path, code in PRINT_ROUTES:
            sample = support.sample_entry_df(code)
            with patch.object(server_connect, 'query_SEord', return_value=sample):
                resp = self.client.post(path, data={'inputEntry': 'JHS0282102'})
            self.assertEqual(resp.status_code, 200, path)
            body = resp.get_data(as_text=True)
            self.assertIn('JHS0282102', body, f'{path} 未渲染出单号')

    def test_multiple_bill_numbers(self):
        with patch.object(server_connect, 'query_SEord',
                          side_effect=lambda bill_no, cn: support.sample_entry_df(cn)):
            resp = self.client.post('/yunHaiPrint', data={'inputEntry': 'JHS0001/JHS0002'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('JHS0001/JHS0002', resp.get_data(as_text=True))

    def test_zhidongli_hit(self):
        with patch.object(server_connect, 'query_SEord',
                          return_value=support.sample_entry_df(2)):
            resp = self.client.post('/zhidongli', data={'inputEntry': 'JHS0001'})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('智动力编码', body)

    def test_zhidongli_bad_spec_does_not_500(self):
        broken = support.sample_entry_df(2)
        broken['整支规格'] = '???'
        with patch.object(server_connect, 'query_SEord', return_value=broken):
            resp = self.client.post('/zhidongli', data={'inputEntry': 'JHS0001'})
        self.assertEqual(resp.status_code, 200)


class MaterialQueryRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = support.make_client()

    def test_get_without_query_renders_cleanly(self):
        for path in ['/queryMaterial', '/LSMqueryMaterial']:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, path)
            self.assertNotIn('未查询到数据', resp.get_data(as_text=True), path)

    def test_post_hit_renders_table(self):
        with patch.object(server_connect, 'queryMaterial',
                          return_value=support.sample_material_df(3)):
            resp = self.client.post('/queryMaterial', data={'material': 'PET'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('测试物料0', resp.get_data(as_text=True))

    def test_post_miss_shows_inline_message(self):
        with patch.object(server_connect, 'queryMaterial', return_value=pd.DataFrame()):
            resp = self.client.post('/queryMaterial', data={'material': 'zzz'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('未查询到数据', resp.get_data(as_text=True))

    def test_post_bad_format_shows_inline_message(self):
        resp = self.client.post('/queryMaterial', data={'material': 'a/b/c'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('查询格式错误', resp.get_data(as_text=True))

    def test_lsm_miss_shows_inline_message(self):
        with patch.object(server_connect, 'LSMqueryMaterial', return_value=pd.DataFrame()):
            resp = self.client.post('/LSMqueryMaterial', data={'material': 'zzz'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('未查询到数据', resp.get_data(as_text=True))

    def test_db_error_does_not_leak_details(self):
        """异常对外只给通用文案，不得泄露异常内容（AGENTS §9-6）。"""
        with patch.object(server_connect, 'queryMaterial',
                          side_effect=RuntimeError('secret-password-in-dsn')):
            resp = self.client.post('/queryMaterial', data={'material': 'PET'})
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('secret-password-in-dsn', resp.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
