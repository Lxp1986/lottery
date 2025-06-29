import collections

def calculate_frequencies(history_data: list[dict]) -> tuple[collections.defaultdict[int, int], collections.defaultdict[int, int]]:
    """
    Calculates the frequency of each regular and special number from lottery history data.

    Args:
        history_data: A list of draw dictionaries, where each dictionary should have
                      'numbers' (a list of ints) and 'special' (an int) keys.
                      Example: [{'date': '2023-01-01', 'numbers': [1,2,3,4,5,6], 'special': 7}, ...]

    Returns:
        A tuple containing two defaultdicts:
        - regular_num_freq: Frequencies of regular numbers.
        - special_num_freq: Frequencies of special numbers.
    """
    regular_num_freq = collections.defaultdict(int)
    special_num_freq = collections.defaultdict(int)

    if not history_data:
        print("Warning: History data is empty. Returning empty frequency counts.")
        return regular_num_freq, special_num_freq

    for draw in history_data:
        if not isinstance(draw, dict):
            print(f"Warning: Skipping invalid draw entry (not a dict): {draw}")
            continue

        numbers = draw.get('numbers')
        special = draw.get('special')

        if numbers is None or not isinstance(numbers, list):
            print(f"Warning: Skipping draw due to missing or invalid 'numbers' field: {draw}")
            # Decide if we should skip just numbers or the whole draw entry
            # For now, if numbers are bad, we might still process special if it's good.
        else:
            for num in numbers:
                if not isinstance(num, int):
                    print(f"Warning: Skipping invalid number (not an int) in 'numbers' list: {num} in draw {draw}")
                    continue
                regular_num_freq[num] += 1

        if special is None or not isinstance(special, int):
            print(f"Warning: Skipping draw due to missing or invalid 'special' field: {draw}")
        else:
            special_num_freq[special] += 1

    return regular_num_freq, special_num_freq

def get_most_frequent(frequencies: collections.defaultdict[int, int] | dict[int, int], count: int = 5) -> list[tuple[int, int]]:
    """
    Gets the most frequent numbers from a frequency dictionary.

    Args:
        frequencies: A dictionary or defaultdict where keys are numbers and values are their frequencies.
        count: The number of most frequent items to return. Defaults to 5.

    Returns:
        A list of (number, frequency) tuples, sorted by frequency in descending order.
        Returns an empty list if frequencies is empty or count is non-positive.
    """
    if not frequencies:
        return []
    if count <= 0:
        print("Warning: 'count' must be positive for get_most_frequent. Returning empty list.")
        return []

    # collections.Counter is efficient for this
    counter = collections.Counter(frequencies)
    return counter.most_common(count)

def get_least_frequent(frequencies: collections.defaultdict[int, int] | dict[int, int], count: int = 5) -> list[tuple[int, int]]:
    """
    Gets the least frequent numbers from a frequency dictionary.

    Args:
        frequencies: A dictionary or defaultdict where keys are numbers and values are their frequencies.
        count: The number of least frequent items to return. Defaults to 5.

    Returns:
        A list of (number, frequency) tuples, sorted by frequency in ascending order.
        Returns an empty list if frequencies is empty or count is non-positive.
    """
    if not frequencies:
        return []
    if count <= 0:
        print("Warning: 'count' must be positive for get_least_frequent. Returning empty list.")
        return []

    # Sort items by frequency (value), then by number (key) for tie-breaking
    sorted_items = sorted(frequencies.items(), key=lambda item: (item[1], item[0]))

    return sorted_items[:count]


if __name__ == '__main__':
    print("--- Testing analysis functions ---")

    # Sample history data (mimicking output from data_input.load_history)
    sample_history = [
        {'date': '2023-01-01', 'numbers': [1, 2, 3, 4, 5, 6], 'special': 7},
        {'date': '2023-01-08', 'numbers': [1, 10, 11, 12, 13, 14], 'special': 7},
        {'date': '2023-01-15', 'numbers': [2, 20, 21, 22, 23, 24], 'special': 8},
        {'date': '2023-01-22', 'numbers': [1, 30, 31, 32, 33, 34], 'special': 9},
        {'date': '2023-01-29', 'numbers': [1, 2, 10, 40, 41, 42], 'special': 7},
        # Malformed data
        {'date': '2023-02-05', 'numbers': [50, 51, 'invalid', 53, 54, 55], 'special': 10},
        {'date': '2023-02-12', 'numbers': [60, 61, 62, 63, 64, 65], 'special': 'bad_special'},
        {'foo': 'bar'}, # Completely invalid structure
        None, # Also invalid
    ]

    # 1. Test calculate_frequencies
    print("\n1. Testing calculate_frequencies:")
    reg_freq, spec_freq = calculate_frequencies(sample_history)
    print("Regular Number Frequencies:")
    # Sort for consistent output in test
    for num, freq in sorted(reg_freq.items()):
        print(f"Number {num}: {freq}")
    print("\nSpecial Number Frequencies:")
    for num, freq in sorted(spec_freq.items()):
        print(f"Number {num}: {freq}")

    # Test with empty history
    print("\nTesting calculate_frequencies with empty list:")
    empty_reg_freq, empty_spec_freq = calculate_frequencies([])
    print(f"Empty Regular Frequencies: {dict(empty_reg_freq)}") # Convert to dict for print
    print(f"Empty Special Frequencies: {dict(empty_spec_freq)}")


    # 2. Test get_most_frequent
    print("\n2. Testing get_most_frequent:")
    print("Most frequent regular numbers (top 3):", get_most_frequent(reg_freq, 3))
    print("Most frequent regular numbers (top 5):", get_most_frequent(reg_freq, 5))
    print("Most frequent special numbers (top 2):", get_most_frequent(spec_freq, 2))
    print("Most frequent from empty dict:", get_most_frequent({}))
    print("Most frequent with count 0:", get_most_frequent(reg_freq, 0))
    print("Most frequent with count larger than items:", get_most_frequent(reg_freq, 100))


    # 3. Test get_least_frequent
    print("\n3. Testing get_least_frequent:")
    print("Least frequent regular numbers (top 3):", get_least_frequent(reg_freq, 3))
    print("Least frequent regular numbers (top 5):", get_least_frequent(reg_freq, 5))
    # Example: numbers with frequency 1, then numbers with frequency 2 etc.
    # For numbers 3,4,5,6,11,12,13,14,20,21,22,23,24,30,31,32,33,34,40,41,42,50,51,53,54,55,60,61,62,63,64,65 (all freq 1)
    # For numbers 10 (freq 2)
    # For numbers 2 (freq 2)
    # For numbers 1 (freq 4)

    print("Least frequent special numbers (top 2):", get_least_frequent(spec_freq, 2))
    print("Least frequent from empty dict:", get_least_frequent({}))
    print("Least frequent with count 0:", get_least_frequent(reg_freq, 0))
    print("Least frequent with count larger than items:", get_least_frequent(reg_freq, 100))


    print("\n--- End of analysis function tests ---")
