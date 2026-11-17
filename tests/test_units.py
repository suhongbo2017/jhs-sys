"""数据层纯逻辑单测：不需要数据库连接（query_SEord 被打桩）。"""

import unittest
from unittest.mock import patch

import pandas as pd

from tests import support  # noqa: F401  （注入 sys.path 与 werkzeug 补丁）
import new_main
import server_connect


class ProcessDeliveryDataTest(unittest.TestCase):
    def test_empty_input_returns_none(self):
        self.assertEqual(new_main.process_delivery_data('', 1), (None, None))

    def test_all_bill_numbers_miss_returns_none(self):
        """全部未命中时不能 pd.concat([]) 抛 ValueError（AGENTS §12-4）。"""
        with patch.object(server_connect, 'query_SEord', return_value=pd.DataFrame()):
            self.assertEqual(new_main.process_delivery_data('JHS0001/JHS0002', 1), (None, None))

    def test_partial_hit_returns_only_hit_rows(self):
        hit = support.sample_entry_df(1)
        empty = pd.DataFrame()

        def fake_query(bill_no, code_name):
            return hit if bill_no == 'JHS0002' else empty

        with patch.object(server_connect, 'query_SEord', side_effect=fake_query):
            df, seout_id = new_main.process_delivery_data('jhs0001/jhs0002', 1)

        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)
        self.assertEqual(seout_id, 'JHS0001/JHS0002')  # 输入被统一大写
        self.assertIn('物料名称', df.columns)

    def test_multiple_hits_are_concatenated(self):
        with patch.object(server_connect, 'query_SEord',
                          side_effect=lambda bill_no, cn: support.sample_entry_df(cn)):
            df, _ = new_main.process_delivery_data('A/B/C', 2)
        self.assertEqual(len(df), 3)

    def test_whitespace_and_empty_segments_tolerated(self):
        """从文档粘贴的 “ JHS1 / JHS2 ” 要能正常查（历史上会因空格查不到）。"""
        calls = []

        def fake_query(bill_no, code_name):
            calls.append(bill_no)
            return support.sample_entry_df(code_name)

        with patch.object(server_connect, 'query_SEord', side_effect=fake_query):
            df, seout_id = new_main.process_delivery_data(' jhs1 / jhs2 / ', 1)

        self.assertEqual(calls, ['JHS1', 'JHS2'])
        self.assertEqual(seout_id, 'JHS1/JHS2')
        self.assertEqual(len(df), 2)

    def test_only_separators_returns_none(self):
        self.assertEqual(new_main.process_delivery_data(' / / ', 1), (None, None))

    def test_query_error_propagates_and_route_survives(self):
        """数据层抛异常时，打印路由要兜底渲染错误提示而不是 500。"""
        client = support.make_client()
        with patch.object(server_connect, 'query_SEord', side_effect=RuntimeError('db down')):
            resp = client.post('/yunHaiPrint', data={'inputEntry': 'JHS0001'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('操作出错'.encode('utf-8'), resp.data)


class ParseSpecStringTest(unittest.TestCase):
    def test_full_spec(self):
        self.assertEqual(new_main._parse_spec_string('1.2*200*300*4'), [1.2, 200.0, 300.0, 4.0])

    def test_short_spec_padded_with_none(self):
        self.assertEqual(new_main._parse_spec_string('200*300'), [200.0, 300.0, None, None])

    def test_garbage_does_not_raise(self):
        self.assertEqual(new_main._parse_spec_string(None), [None, None, None, None])
        self.assertEqual(new_main._parse_spec_string(''), [None, None, None, None])


class ProcessZhidongliDataTest(unittest.TestCase):
    def _df(self):
        return pd.DataFrame([{
            '订单号': 'PO1', '批次号': 'B1', '物料名称': '隔膜',
            '数量': '3.14159', '整支规格': '1.2*200*300*4', '备注': '2026-01-01',
        }])

    def test_columns_and_rounding(self):
        out = new_main.process_zhidongli_data(self._df())
        self.assertEqual(
            list(out.columns),
            ['订单号', '智动力编码', '品名', '宽', '长', '厚', '支', '数量', '生产日期'],
        )
        self.assertEqual(out.iloc[0]['数量'], 3.14)
        self.assertEqual(out.iloc[0]['宽'], 200.0)
        self.assertEqual(out.iloc[0]['智动力编码'], 'B1')


class ProcessMaterialQueryTest(unittest.TestCase):
    def test_single_condition(self):
        queried = []

        def fake(q):
            queried.append(q)
            return support.sample_material_df()

        result, kind = new_main.process_material_query('240', fake)
        self.assertEqual(queried, ['240'])
        self.assertEqual(kind, '单条件查询')
        self.assertEqual(len(result), 2)

    def test_two_conditions_filter_name_or_spec(self):
        df = pd.DataFrame({
            '物料名称': ['PET膜', '铝箔', 'PET膜'],
            '规格型号': ['10*200', '12*300', '20*400'],
            '物料代码': ['M1', 'M2', 'M3'],
            '短代码': ['S1', 'S2', 'S3'],
        })

        result, kind = new_main.process_material_query('PET/20*', lambda q: df)
        self.assertEqual(kind, '多条件查询')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['规格型号'], '20*400')

    def test_second_condition_also_matches_codes(self):
        """页面文案是“名称 / 规格 / 代码”，第二个条件要能搜代码。"""
        df = pd.DataFrame({
            '物料名称': ['PET膜', 'PET膜'],
            '规格型号': ['', ''],
            '物料代码': ['1.1.01.00.001', '1.1.01.00.002'],
            '短代码': ['001', '002'],
        })
        result, _ = new_main.process_material_query('PET/00.002', lambda q: df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['短代码'], '002')

    def test_invalid_format_raises_value_error(self):
        for bad in ['a/b/c', 'a/', '/b', '/']:
            with self.assertRaises(ValueError, msg=bad):
                new_main.process_material_query(bad, lambda q: support.sample_material_df())

    def test_regex_special_chars_are_literal(self):
        """“20*”、“(” 这类字符必须按字面量匹配（默认 regex=True 会误匹配/抛错）。"""
        df = pd.DataFrame({
            '物料名称': ['PET膜', 'PET膜'],
            '规格型号': ['10*200', '20*300'],
        })
        result, _ = new_main.process_material_query('PET/20*', lambda q: df)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]['规格型号'], '20*300')

        result, _ = new_main.process_material_query('PET/(', lambda q: df)
        self.assertEqual(len(result), 0)

    def test_rows_with_null_cells_do_not_break(self):
        df = pd.DataFrame({
            '物料名称': ['PET膜', None],
            '规格型号': [None, '10*200'],
            '物料代码': [None, 'M2'],
            '短代码': [None, 'S2'],
        })
        result, _ = new_main.process_material_query('PET/PET', lambda q: df)
        self.assertEqual(len(result), 1)

    def test_conditions_are_stripped(self):
        seen = []

        def fake(q):
            seen.append(q)
            return support.sample_material_df()

        new_main.process_material_query('  PET / 10*  ', fake)
        self.assertEqual(seen, ['PET'])


class AllowedFileTest(unittest.TestCase):
    def test_extensions(self):
        self.assertTrue(new_main.allowed_file('a.PDF'))
        self.assertFalse(new_main.allowed_file('a.exe'))
        self.assertFalse(new_main.allowed_file('noext'))


class EnvFileTest(unittest.TestCase):
    def test_parse_and_no_override(self):
        import os
        import tempfile

        with tempfile.NamedTemporaryFile('w', suffix='.env', delete=False, encoding='utf-8') as f:
            f.write('# comment\n\nFOO_TEST_KEY=hello\nBAR_TEST_KEY = "quoted"\n')
            path = f.name
        try:
            os.environ.pop('FOO_TEST_KEY', None)
            os.environ['BAR_TEST_KEY'] = 'existing'
            new_main._load_env_file(path)
            self.assertEqual(os.environ['FOO_TEST_KEY'], 'hello')
            self.assertEqual(os.environ['BAR_TEST_KEY'], 'existing')  # 不覆盖已有变量
        finally:
            os.environ.pop('FOO_TEST_KEY', None)
            os.environ.pop('BAR_TEST_KEY', None)
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
