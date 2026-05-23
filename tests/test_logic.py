import unittest
from currency_bot.logic import extract_currency_matches


class TestCurrencyLogic(unittest.TestCase):
    def test_base_amounts(self):
        self.assertEqual(extract_currency_matches("100 USD"), [(100.0, "USD")])
        self.assertEqual(extract_currency_matches("$100"), [(100.0, "USD")])
        self.assertEqual(extract_currency_matches("£50"), [(50.0, "GBP")])
        self.assertEqual(extract_currency_matches("50 GBP"), [(50.0, "GBP")])

    def test_k_suffix(self):
        self.assertEqual(extract_currency_matches("$80K"), [(80000.0, "USD")])
        self.assertEqual(extract_currency_matches("$80k"), [(80000.0, "USD")])
        self.assertEqual(extract_currency_matches("80k USD"), [(80000.0, "USD")])
        self.assertEqual(extract_currency_matches("80 K USD"), [(80000.0, "USD")])

    def test_l_suffix(self):
        self.assertEqual(extract_currency_matches("₹20L"), [(2000000.0, "INR")])
        self.assertEqual(extract_currency_matches("₹20l"), [(2000000.0, "INR")])
        self.assertEqual(extract_currency_matches("20L INR"), [(2000000.0, "INR")])

    def test_cr_suffix(self):
        self.assertEqual(extract_currency_matches("₹10cr"), [(100000000.0, "INR")])
        self.assertEqual(extract_currency_matches("₹10CR"), [(100000000.0, "INR")])
        self.assertEqual(extract_currency_matches("10cr INR"), [(100000000.0, "INR")])

    def test_m_b_t_suffixes(self):
        self.assertEqual(extract_currency_matches("1.5M EUR"), [(1500000.0, "EUR")])
        self.assertEqual(extract_currency_matches("2B USD"), [(2000000000.0, "USD")])
        self.assertEqual(extract_currency_matches("$1T"), [(1000000000000.0, "USD")])

    def test_decimals_with_suffixes(self):
        self.assertEqual(extract_currency_matches("$1.5K"), [(1500.0, "USD")])
        self.assertEqual(extract_currency_matches("₹2.5L"), [(250000.0, "INR")])
        self.assertEqual(extract_currency_matches("₹1.5cr"), [(15000000.0, "INR")])

    def test_whole_word_matching(self):
        self.assertEqual(extract_currency_matches("Call190Now"), [])
        self.assertEqual(extract_currency_matches("Actually 190"), [])
        self.assertEqual(extract_currency_matches("All190"), [(190.0, "ALL")])
        self.assertEqual(extract_currency_matches("190 EUR"), [(190.0, "EUR")])
        self.assertEqual(extract_currency_matches("EUR 190"), [(190.0, "EUR")])
        self.assertEqual(extract_currency_matches("190EUR"), [(190.0, "EUR")])
        self.assertEqual(extract_currency_matches("EUR190"), [(190.0, "EUR")])

    def test_num_attached_with_text(self):
        self.assertEqual(extract_currency_matches("5000brl"), [(5000.0, "BRL")])
        self.assertEqual(extract_currency_matches("eur1000"), [(1000.0, "EUR")])

    def test_commas(self):
        self.assertEqual(extract_currency_matches("$10,500"), [(10500.0, "USD")])
        self.assertEqual(extract_currency_matches("$10,000.65"), [(10000.65, "USD")])
        self.assertEqual(extract_currency_matches("10,00,000 INR"), [(1000000.0, "INR")])


if __name__ == "__main__":
    unittest.main()
