import unittest

from cheuph import AT

__all__ = ["TestAttributedText"]

class TestAttributedText(unittest.TestCase):

    SAMPLE_STRINGS = [
            "Hello world",
            "\n",
            "            ",
            "multiline\nstring\nwith\nmultiple\nlines",
    ]

    def setUp(self):
        self.text = AT("This is a sample string.")
        self.text = self.text.set("attribute", "value", 5, 21)
        self.text = self.text.set_at("attribute2", "value2", 13)

    def test_equality_of_empty_text(self):
        self.assertEqual(AT(), AT())
        self.assertEqual(AT(), AT(attribute="value"))

    def test_string_to_AT_to_string(self):
        for string in self.SAMPLE_STRINGS:
            with self.subTest(string=repr(string)):
                self.assertEqual(string, str(AT(string)))

    def test_homomorphism_on_string_concatenation(self):
        self.assertEqual("hello world", str(AT("hello") + AT(" world")))

        result_1 = "".join(self.SAMPLE_STRINGS)
        result_2 = AT().join(AT(string) for string in self.SAMPLE_STRINGS)
        self.assertEqual(result_1, str(result_2))

    def test_setting_and_getting_an_attribute(self):
        # Lower and upper bounds

        self.assertIsNone(self.text.get(4, "attribute"))
        self.assertEqual("value", self.text.get(5, "attribute"))
        self.assertEqual("value", self.text.get(20, "attribute"))
        self.assertIsNone(self.text.get(21, "attribute"))

        self.assertIsNone(self.text.get(12, "attribute2"))
        self.assertEqual("value2", self.text.get(13, "attribute2"))
        self.assertIsNone(self.text.get(14, "attribute2"))

        # Variants on get()

        self.assertEqual({"attribute": "value"}, self.text.at(10))
        self.assertEqual("value", self.text.at(10).get("attribute"))
        self.assertEqual("value", self.text.get(10, "attribute"))

        self.assertEqual({}, self.text.at(2))
        self.assertIsNone(self.text.get(2, "attribute"))


        self.assertEqual({"attribute": "value", "attribute2": "value2"},
                self.text.at(13))

    def test_slicing_and_putting_back_together_with_attributes(self):
        text2 = self.text[:4] + self.text[4:11] + self.text[11:22] + self.text[22:]
        text3 = self.text[:-20] + self.text[-20:-4] + self.text[-4:]
        text4 = self.text[:3] + self.text[3] + self.text[4:]

        self.assertEqual(self.text, text2)
        self.assertEqual(self.text, text3)
        self.assertEqual(self.text, text4)

    def test_removing_attributes(self):
        text = self.text.remove("attribute", 9, 15)

        # Lower and upper bounds

        self.assertEqual("value", text.get(8, "attribute"))
        self.assertIsNone(text.get(9, "attribute"))
        self.assertIsNone(text.get(14, "attribute"))
        self.assertEqual("value", text.get(15, "attribute"))

        # Other attribute wasn't touched

        self.assertIsNone(text.get(12, "attribute2"))
        self.assertEqual("value2", text.get(13, "attribute2"))
        self.assertIsNone(text.get(14, "attribute2"))

    def test_immutability(self):
        text = self.text
        text2 = text.remove("attribute", 10, 12)
        text3 = text2.set("attribute", "bar", 10, 14)
        text4 = text3.set_at("attribute", "xyz", 11)

        for i in range(5, 21):
            self.assertEqual("value", text.get(i, "attribute"))

        for i in range(10, 12):
            self.assertIsNone(text2.get(i, "attribute"))

        for i in range(10, 14):
            self.assertEqual("bar", text3.get(i, "attribute"))

        self.assertEqual("xyz", text4.get(11, "attribute"))

    def test_joining_with_attributes(self):
        snippet1 = AT("hello", foo="bar")
        snippet2 = AT("world", foo="qux")
        space = AT(" ", space=True, foo="herbert")

        text1 = snippet1 + space + snippet2
        text2 = space.join([snippet1, snippet2])

        self.assertEqual(text1, text2)

    def test_repeating_by_multiplication(self):
        text = AT("a", x=1) + AT("b", y=2)
        repeated_1 = text + text + text + text + text
        repeated_2 = text * 5
        repeated_3 = AT().join([text] * 5)

        self.assertEqual(repeated_1, repeated_2)
        self.assertEqual(repeated_1, repeated_3)

    def test_split_by(self):
        split = self.text.split_by("attribute")
        expected = [
                (AT("This "), None),
                (
                    AT("is a sam", attribute="value") +
                    AT("p", attribute="value", attribute2="value2") +
                    AT("le stri", attribute="value"),
                    "value"
                ),
                (AT("ng."), None),
        ]
        self.assertEqual(split, expected)

        split = self.text.split_by("attribute2")
        expected = [
                (
                    AT("This ") +
                    AT("is a sam", attribute="value"),
                    None
                ),
                (
                    AT("p", attribute="value", attribute2="value2"),
                    "value2"
                ),
                (
                    AT("le stri", attribute="value") + AT("ng."),
                    None
                ),
        ]
        self.assertEqual(split, expected)
