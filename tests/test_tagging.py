import unittest
from lottery_analyzer import tagging # Assumes tagging.py is in lottery_analyzer package

class TestTaggingFunctions(unittest.TestCase):

    def setUp(self):
        """
        Reset tags before each test to ensure test isolation.
        This involves clearing the global number_tags dictionary and re-applying defaults.
        """
        tagging.number_tags.clear()
        tagging.apply_default_tags()
        # print(f"Setup done for {self.id()}. Tags for 1: {tagging.get_tags_for_number(1)}") # For debugging setup

    def test_apply_default_tags(self):
        """Verify that all numbers (1-49) have correct default tags."""
        for i in range(tagging.MIN_NUMBER, tagging.MAX_NUMBER + 1):
            tags = tagging.get_tags_for_number(i)
            self.assertTrue(tags, f"Number {i} should have default tags.") # Check not empty

            # Odd/Even
            if i % 2 == 0:
                self.assertIn("Even", tags, f"Number {i} should have 'Even' tag.")
                self.assertNotIn("Odd", tags, f"Number {i} should not have 'Odd' tag.")
            else:
                self.assertIn("Odd", tags, f"Number {i} should have 'Odd' tag.")
                self.assertNotIn("Even", tags, f"Number {i} should not have 'Even' tag.")

            # Small/Big
            if tagging.MIN_NUMBER <= i <= tagging.MID_POINT: # MID_POINT is 24
                self.assertIn("Small", tags, f"Number {i} (<=24) should have 'Small' tag.")
                self.assertNotIn("Big", tags, f"Number {i} (<=24) should not have 'Big' tag.")
            else: # i > tagging.MID_POINT (25-49)
                self.assertIn("Big", tags, f"Number {i} (>24) should have 'Big' tag.")
                self.assertNotIn("Small", tags, f"Number {i} (>24) should not have 'Small' tag.")

        # Test a few specific cases explicitly
        self.assertEqual(tagging.get_tags_for_number(1), {"Odd", "Small"})
        self.assertEqual(tagging.get_tags_for_number(24), {"Even", "Small"})
        self.assertEqual(tagging.get_tags_for_number(25), {"Odd", "Big"})
        self.assertEqual(tagging.get_tags_for_number(49), {"Odd", "Big"})

    def test_add_custom_tag_new_and_multiple(self):
        """Test adding a new custom tag and multiple custom tags to a number."""
        tagging.add_custom_tag(7, "Lucky")
        self.assertIn("Lucky", tagging.get_tags_for_number(7))

        tagging.add_custom_tag(7, "Favorite")
        self.assertEqual(tagging.get_tags_for_number(7), {"Odd", "Small", "Lucky", "Favorite"})

    def test_add_custom_tag_preserves_defaults(self):
        """Test that adding a custom tag preserves default tags."""
        tagging.add_custom_tag(10, "Decade1")
        expected_tags = {"Even", "Small", "Decade1"}
        self.assertEqual(tagging.get_tags_for_number(10), expected_tags)

    def test_add_custom_tag_idempotent(self):
        """Test adding an existing tag (should not duplicate or error)."""
        tagging.add_custom_tag(15, "Special")
        tagging.add_custom_tag(15, "Special") # Add again
        expected_tags = {"Odd", "Small", "Special"}
        self.assertEqual(tagging.get_tags_for_number(15), expected_tags)
        self.assertEqual(len(tagging.number_tags[15]), 3) # Ensure no duplicates in set

    def test_add_custom_tag_edge_numbers(self):
        """Test adding tags to numbers at the edge of the valid range."""
        tagging.add_custom_tag(1, "First")
        self.assertIn("First", tagging.get_tags_for_number(1))

        tagging.add_custom_tag(49, "Last")
        self.assertIn("Last", tagging.get_tags_for_number(49))

    def test_add_custom_tag_invalid_numbers(self):
        """Test adding tags to invalid numbers (e.g., 0, 50). Expect no change/error message."""
        # These should print an error (checked by observing output if run manually)
        # but not raise an exception, and number_tags should not be modified for these keys.
        initial_tags_0 = tagging.number_tags.get(0, set())
        tagging.add_custom_tag(0, "InvalidLow")
        self.assertEqual(tagging.number_tags.get(0, set()), initial_tags_0) # No new key created
        self.assertNotIn(0, tagging.number_tags)


        initial_tags_50 = tagging.number_tags.get(50, set())
        tagging.add_custom_tag(50, "InvalidHigh")
        self.assertEqual(tagging.number_tags.get(50, set()), initial_tags_50)
        self.assertNotIn(50, tagging.number_tags)

    def test_add_custom_tag_invalid_tag_string(self):
        """Test adding invalid tags (empty or whitespace)."""
        tagging.add_custom_tag(10, "") # Should print error, no change
        self.assertEqual(tagging.get_tags_for_number(10), {"Even", "Small"})

        tagging.add_custom_tag(10, "  ") # Should print error, no change
        self.assertEqual(tagging.get_tags_for_number(10), {"Even", "Small"})


    def test_get_tags_for_number_default_only(self):
        """Test retrieving tags for a number with only default tags."""
        self.assertEqual(tagging.get_tags_for_number(2), {"Even", "Small"})

    def test_get_tags_for_number_with_custom(self):
        """Test retrieving tags for a number with custom tags."""
        tagging.add_custom_tag(30, "Round")
        self.assertEqual(tagging.get_tags_for_number(30), {"Even", "Big", "Round"})

    def test_get_tags_for_number_invalid_number(self):
        """Test retrieving tags for an invalid number."""
        self.assertEqual(tagging.get_tags_for_number(0), set())
        self.assertEqual(tagging.get_tags_for_number(50), set())
        self.assertEqual(tagging.get_tags_for_number(-5), set())

    def test_get_numbers_with_tag_default(self):
        """Test retrieving numbers for a default tag."""
        big_numbers = tagging.get_numbers_with_tag("Big")
        expected_big = list(range(25, 50)) # 25-49
        self.assertEqual(sorted(big_numbers), expected_big) # get_numbers_with_tag returns sorted

        even_numbers = tagging.get_numbers_with_tag("Even")
        expected_even = [i for i in range(1,50) if i%2==0]
        self.assertEqual(sorted(even_numbers), expected_even)


    def test_get_numbers_with_tag_custom(self):
        """Test retrieving numbers for a custom tag."""
        tagging.add_custom_tag(5, "MyTag")
        tagging.add_custom_tag(15, "MyTag")
        tagging.add_custom_tag(25, "MyTag")
        self.assertEqual(tagging.get_numbers_with_tag("MyTag"), [5, 15, 25])

    def test_get_numbers_with_tag_non_existent(self):
        """Test retrieving numbers for a tag that doesn't exist."""
        self.assertEqual(tagging.get_numbers_with_tag("NonExistentTag"), [])

    def test_get_numbers_with_tag_invalid_tag_string(self):
        """Test retrieving numbers with an invalid tag string."""
        self.assertEqual(tagging.get_numbers_with_tag(""), [])
        self.assertEqual(tagging.get_numbers_with_tag("  "), [])

    def test_default_tags_reapplication_idempotency(self):
        """Test that re-applying default tags doesn't change custom tags or duplicate defaults."""
        tagging.add_custom_tag(7, "Lucky")
        initial_tags_7 = tagging.get_tags_for_number(7).copy()

        tagging.apply_default_tags() # Re-apply

        self.assertEqual(tagging.get_tags_for_number(7), initial_tags_7, "Re-applying defaults changed tags for 7.")
        # Check a number without custom tags
        self.assertEqual(tagging.get_tags_for_number(2), {"Even", "Small"}, "Re-applying defaults changed tags for 2.")


class TestTagHelperFunctions(unittest.TestCase):
    """Tests for the individual tag getter helper functions."""

    def test_get_dx_tag(self):
        """Test get_dx_tag for single/double (奇偶) property."""
        self.assertEqual(tagging.get_dx_tag(1), "单")
        self.assertEqual(tagging.get_dx_tag(2), "双")
        self.assertEqual(tagging.get_dx_tag(25), "单")
        self.assertEqual(tagging.get_dx_tag(49), "单")
        self.assertEqual(tagging.get_dx_tag(48), "双")
        # Test invalid numbers
        self.assertIsNone(tagging.get_dx_tag(0))
        self.assertIsNone(tagging.get_dx_tag(50))
        self.assertIsNone(tagging.get_dx_tag(tagging.MIN_NUMBER - 1))
        self.assertIsNone(tagging.get_dx_tag(tagging.MAX_NUMBER + 1))

    def test_get_ds_tag(self):
        """Test get_ds_tag for big/small (大小) property."""
        # Boundary is 25 (>=25 is 大)
        self.assertEqual(tagging.get_ds_tag(1), "小")
        self.assertEqual(tagging.get_ds_tag(24), "小")
        self.assertEqual(tagging.get_ds_tag(25), "大")
        self.assertEqual(tagging.get_ds_tag(49), "大")
        # Test invalid numbers
        self.assertIsNone(tagging.get_ds_tag(0))
        self.assertIsNone(tagging.get_ds_tag(50))

    def test_get_sum_feature_tag(self):
        """Test get_sum_feature_tag for sum of digits (合单/合双)."""
        self.assertEqual(tagging.get_sum_feature_tag(1), "合单")  # 0+1=1
        self.assertEqual(tagging.get_sum_feature_tag(10), "合单") # 1+0=1
        self.assertEqual(tagging.get_sum_feature_tag(11), "合双") # 1+1=2
        self.assertEqual(tagging.get_sum_feature_tag(23), "合单") # 2+3=5
        self.assertEqual(tagging.get_sum_feature_tag(49), "合单") # 4+9=13
        self.assertEqual(tagging.get_sum_feature_tag(48), "合双") # 4+8=12
        # Test invalid numbers
        self.assertIsNone(tagging.get_sum_feature_tag(0))
        self.assertIsNone(tagging.get_sum_feature_tag(50))

    def test_get_tail_feature_tag(self):
        """Test get_tail_feature_tag for tail digit (X尾)."""
        self.assertEqual(tagging.get_tail_feature_tag(1), "1尾")
        self.assertEqual(tagging.get_tail_feature_tag(10), "0尾")
        self.assertEqual(tagging.get_tail_feature_tag(9), "9尾")
        self.assertEqual(tagging.get_tail_feature_tag(29), "9尾")
        self.assertEqual(tagging.get_tail_feature_tag(40), "0尾")
        # Test invalid numbers
        self.assertIsNone(tagging.get_tail_feature_tag(0))
        self.assertIsNone(tagging.get_tail_feature_tag(50))

    def test_get_zodiac_tag(self):
        """Test get_zodiac_tag based on ZODIAC_MAPPING."""
        # Examples from ZODIAC_MAPPING
        self.assertEqual(tagging.get_zodiac_tag(1), "生肖-蛇") # Snake
        self.assertEqual(tagging.get_zodiac_tag(6), "生肖-鼠") # Rat
        self.assertEqual(tagging.get_zodiac_tag(13), "生肖-蛇")# Snake
        self.assertEqual(tagging.get_zodiac_tag(49), "生肖-蛇")# Snake
        self.assertEqual(tagging.get_zodiac_tag(12), "生肖-马")# Horse
        # Test invalid numbers
        self.assertIsNone(tagging.get_zodiac_tag(0))
        self.assertIsNone(tagging.get_zodiac_tag(50))
        # Test a number that might be missing if mapping is incomplete (though current is complete)
        # Assuming all numbers 1-49 are mapped. If a number was unmapped, it should return None.

    def test_get_element_tag(self):
        """Test get_element_tag based on ELEMENTS_MAPPING."""
        # Examples from ELEMENTS_MAPPING
        self.assertEqual(tagging.get_element_tag(1), "五行-火")  # Fire
        self.assertEqual(tagging.get_element_tag(3), "五行-金")  # Gold
        self.assertEqual(tagging.get_element_tag(49), "五行-土") # Earth
        self.assertEqual(tagging.get_element_tag(14), "五行-水") # Water
        self.assertEqual(tagging.get_element_tag(23), "五行-木") # Wood
        # Test invalid numbers
        self.assertIsNone(tagging.get_element_tag(0))
        self.assertIsNone(tagging.get_element_tag(50))

    def test_get_color_tag(self):
        """Test get_color_tag based on COLOR_MAPPING."""
        # Examples from COLOR_MAPPING
        self.assertEqual(tagging.get_color_tag(1), "红波")  # Red
        self.assertEqual(tagging.get_color_tag(3), "蓝波")  # Blue
        self.assertEqual(tagging.get_color_tag(5), "绿波")  # Green
        self.assertEqual(tagging.get_color_tag(49), "绿波") # Green
        # Test invalid numbers
        self.assertIsNone(tagging.get_color_tag(0))
        self.assertIsNone(tagging.get_color_tag(50))

if __name__ == '__main__':
    unittest.main()
