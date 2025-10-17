import unittest
from nodes.common.get_files_node import get_files_node

class TestGetFilesNode(unittest.TestCase):
    def test_get_files(self):
        n = get_files_node()
        ctx = {'project_root': '.'}
        params = {'patterns': ['*.py']}
        prep = n['prep'](ctx, params)
        result = n['exec'](prep, params)
        self.assertIsInstance(result, list)

if __name__ == '__main__':
    unittest.main()
