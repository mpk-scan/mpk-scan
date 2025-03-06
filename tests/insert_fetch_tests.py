import unittest
import sys
import os

sys.path.append(os.path.abspath("../src/storage"))

from insert_file import insert, insert_with_external, insert_inline
from fetch_js import fetch

class TestStorer(unittest.TestCase):

    def test_insert(self):
        self.assertEqual(insert('google.com/|docs/document'), 'google.com/|docs/document')
        self.assertEqual(insert('https://example.com/path'), 'example.com/path')
        self.assertEqual(insert('sub.example.com/path'), 'example.com/|sub/path')
        self.assertEqual(insert('https://www.example.com'), 'example.com/|www')
        self.assertEqual(insert('example.com'), 'example.com')
        self.assertEqual(insert('https://sub2.sub1.example.com'), 'example.com/|sub1/|sub2')

    def test_insert_with_external(self):
        self.assertEqual(
            insert_with_external('example.com/path', 'external.com/resource'),
            'example.com/path/||/external.com/resource'
        )
        self.assertEqual(
            insert_with_external('https://main.com', 'https://external.com'),
            'main.com/||/external.com'
        )
        self.assertEqual(
            insert_with_external('sub.main.com/path', 'sub.external.com/res'),
            'main.com/|sub/path/||/external.com/|sub/res'
        )
        self.assertEqual(
            insert_with_external('www.example.com', 'external.com'),
            'example.com/|www/||/external.com'
        )
        self.assertEqual(
            insert_with_external('example.com', 'sub.external.com/path'),
            'example.com/||/external.com/|sub/path'
        )

    def test_insert_inline(self):
        self.assertEqual(insert_inline('example.com/path'), 'example.com/path/|||/inline.js')
        self.assertEqual(insert_inline('https://example.com'), 'example.com/|||/inline.js')
        self.assertEqual(insert_inline('sub.example.com/path'), 'example.com/|sub/path/|||/inline.js')
        self.assertEqual(insert_inline('example.com'), 'example.com/|||/inline.js')

    def test_fetch(self):
        self.assertEqual(fetch('example.com/path'), ['0', 'https://example.com/path'])
        self.assertEqual(fetch('example.com/|sub/path'), ['0', 'https://sub.example.com/path'])
        self.assertEqual(fetch('example.com/path/||/external.com/resource'), ['1', 'https://example.com/path https://external.com/resource'])
        self.assertEqual(fetch('example.com/path/|||/inline.js'), ['2', 'https://example.com/path'])
        self.assertEqual(fetch('example.com/|www/|||/inline.js'), ['2', 'https://www.example.com'])
        self.assertEqual(fetch('example.com/||/external.com/|sub/resource'), ['1', 'https://example.com https://sub.external.com/resource'])

if __name__ == '__main__':
    unittest.main()
