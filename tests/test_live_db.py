"""真连数据库用例：需要内网环境，默认跳过。

启用：
    set RUN_LIVE_DB=1 && .venv/Scripts/python.exe -m unittest tests.test_live_db -v
可选指定单号：
    set LIVE_BILL_NO=JHS0282102
"""

import os
import unittest

import pandas as pd

import server_connect

RUN_LIVE = os.environ.get('RUN_LIVE_DB') == '1'
BILL_NO = os.environ.get('LIVE_BILL_NO', 'JHS0282102')


@unittest.skipUnless(RUN_LIVE, '需要内网数据库：设置 RUN_LIVE_DB=1 后运行')
class LiveDatabaseTest(unittest.TestCase):
    def test_query_seord_all_code_names(self):
        for code in sorted(server_connect.ENTRY_CONFIGS):
            df = server_connect.query_SEord(BILL_NO, code)
            self.assertIsInstance(df, pd.DataFrame, code)
            if df.empty:
                continue
            # 各 codeName 的 post_process 会裁剪/聚合列，只能验公共部分
            self.assertIn('数量', df.columns, f'codeName={code} 缺数量列')
            self.assertIn('ID', df.columns, f'codeName={code} 缺 ID 列')

    def test_query_seord_unknown_bill_number_is_empty(self):
        self.assertTrue(server_connect.query_SEord('JHS_NOT_EXIST_9999', 1).empty)

    def test_material_queries(self):
        self.assertIsInstance(server_connect.queryMaterial('240'), pd.DataFrame)
        self.assertIsInstance(server_connect.LSMqueryMaterial('胶'), pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
