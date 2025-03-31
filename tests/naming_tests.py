import unittest
import sys
import os

sys.path.append(os.path.abspath("../src/storage"))

from name_file import name_js, name_with_external, name_inline
from unname_file import unname_js

class TestStorer(unittest.TestCase):

    def test_name(self):
        self.assertEqual(name_js('google.com/|docs/document'), 'google.com/|docs/document')
        self.assertEqual(name_js('https://example.com/path'), 'example.com/path')
        self.assertEqual(name_js('sub.example.com/path'), 'example.com/|sub/path')
        self.assertEqual(name_js('https://www.example.com'), 'example.com/|www')
        self.assertEqual(name_js('example.com'), 'example.com')
        self.assertEqual(name_js('https://sub2.sub1.example.com'), 'example.com/|sub1/|sub2')

    def test_name_with_external(self):
        self.assertEqual(
            name_with_external('example.com/path', 'external.com/resource'),
            'example.com/path/||/external.com/resource'
        )
        self.assertEqual(
            name_with_external('https://main.com', 'https://external.com'),
            'main.com/||/external.com'
        )
        self.assertEqual(
            name_with_external('sub.main.com/path', 'sub.external.com/res'),
            'main.com/|sub/path/||/external.com/|sub/res'
        )
        self.assertEqual(
            name_with_external('www.example.com', 'external.com'),
            'example.com/|www/||/external.com'
        )
        self.assertEqual(
            name_with_external('example.com', 'sub.external.com/path'),
            'example.com/||/external.com/|sub/path'
        )

    def test_name_inline(self):
        self.assertEqual(name_inline('example.com/path'), 'example.com/path/|||/inline.js')
        self.assertEqual(name_inline('https://example.com'), 'example.com/|||/inline.js')
        self.assertEqual(name_inline('sub.example.com/path'), 'example.com/|sub/path/|||/inline.js')
        self.assertEqual(name_inline('example.com'), 'example.com/|||/inline.js')

    def test_unname(self):
        self.assertEqual(unname_js('example.com/path'), ['0', 'https://example.com/path'])
        self.assertEqual(unname_js('example.com/|sub/path'), ['0', 'https://sub.example.com/path'])
        self.assertEqual(unname_js('example.com/path/||/external.com/resource'), ['1', 'https://example.com/path https://external.com/resource'])
        self.assertEqual(unname_js('example.com/path/|||/inline.js'), ['2', 'https://example.com/path'])
        self.assertEqual(unname_js('example.com/|www/|||/inline.js'), ['2', 'https://www.example.com'])
        self.assertEqual(unname_js('example.com/||/external.com/|sub/resource'), ['1', 'https://example.com https://sub.external.com/resource'])

if __name__ == '__main__':
    unittest.main()
