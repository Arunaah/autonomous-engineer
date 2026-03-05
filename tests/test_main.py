import unittest
import main

class TestMain(unittest.TestCase):
    def test_simulate_production(self):
        # Capture the output of the function to test
        with unittest.mock.patch('sys.stdout', new_callable=io.StringIO) as fake_out:
            main.simulate_production()
            output = fake_out.getvalue()
            self.assertIn('Production simulation started', output)

if __name__ == '__main__':
    unittest.main()