import unittest
import main

class TestMain(unittest.TestCase):
    def test_main(self):
        with unittest.mock.patch('sys.stdout', new_callable=io.StringIO) as fake_out:
            main.main()
            self.assertEqual(fake_out.getvalue(), 'Hello, World!
')

if __name__ == '__main__':
    unittest.main()