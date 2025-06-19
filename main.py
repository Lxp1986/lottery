import argparse
import os
import csv # For validating CSV structure in add_draw more easily
from datetime import datetime
import sys

# Project modules
from lottery_analyzer import data_input
from lottery_analyzer import tagging
from lottery_analyzer import analysis
from lottery_analyzer import prediction
from lottery_analyzer import visualization

# Constants
DATA_DIR = "data"
DATA_FILE_PATH = os.path.join(DATA_DIR, "history.csv")
MIN_NUMBER = 1
MAX_NUMBER = 49
NUM_REGULAR = 6
NUM_SPECIAL = 1

def ensure_data_dir_exists():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR)
            print(f"Info: Data directory '{DATA_DIR}' created.")
        except OSError as e:
            print(f"Error: Could not create data directory '{DATA_DIR}'. Reason: {e}")
            # Depending on the command, we might want to exit here.
            # For now, let functions that need the dir handle its absence.

def parse_numbers_input(numbers_str: str, expected_count: int, label: str) -> list[int] | None:
    """Parses and validates a comma-separated string of numbers."""
    try:
        numbers = [int(n.strip()) for n in numbers_str.split(',')]
        if len(numbers) != expected_count:
            print(f"Error: Exactly {expected_count} {label} numbers are required. Got {len(numbers)}.")
            return None
        if label == "regular" and len(set(numbers)) != expected_count : # Uniqueness only for regular numbers
             print(f"Error: Regular numbers must be unique. Input: {numbers}")
             return None
        if not all(MIN_NUMBER <= num <= MAX_NUMBER for num in numbers):
            print(f"Error: All {label} numbers must be between {MIN_NUMBER} and {MAX_NUMBER}. Input: {numbers}")
            return None
        return numbers
    except ValueError:
        print(f"Error: Numbers must be integers. Invalid input: '{numbers_str}'")
        return None

def handle_add_draw(args):
    """Handles the 'add_draw' command."""
    print("Action: Add new draw...")
    regular_numbers = parse_numbers_input(args.numbers, NUM_REGULAR, "regular")
    if not regular_numbers:
        return

    special_number_list = parse_numbers_input(args.special, NUM_SPECIAL, "special")
    if not special_number_list:
        return
    special_number = special_number_list[0]

    # Validate special number is not in regular numbers
    if special_number in regular_numbers:
        print(f"Error: Special number {special_number} cannot be one of the regular numbers {regular_numbers}.")
        return

    date_str = args.date
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Date format should be YYYY-MM-DD. Got: '{date_str}'")
            return
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        print(f"Info: No date provided, using current date: {date_str}")

    new_draw = {
        'date': date_str,
        'numbers': sorted(regular_numbers), # Store sorted
        'special': special_number
    }

    # data_input.save_history expects a list of draws
    data_input.save_history([new_draw])  # 使用默认路径
    # save_history prints its own confirmation, so we might not need another one here
    # print(f"Successfully added draw: {new_draw} to {DATA_FILE_PATH}")

def handle_show_analysis(args):
    """Handles the 'show_analysis' command."""
    print("Action: Show analysis...")
    history = data_input.load_history(DATA_FILE_PATH)
    if not history:
        print("No history data found. Please add draws first using the 'add_draw' command.")
        return

    reg_freq, spec_freq = analysis.calculate_frequencies(history)

    if not reg_freq and not spec_freq and history: # if history is not empty but freqs are
        print("Frequency data is empty, though history was loaded. This might indicate all data in history was invalid.")
        return
    elif not reg_freq and not spec_freq: # if history was empty and freqs are too
        print("No frequency data to analyze.") # Should have been caught by 'if not history' already
        return


    top_n = args.top
    analysis_type = args.type

    if analysis_type in ["all", "regular"]:
        if reg_freq:
            print(f"\n--- Regular Numbers (Top {top_n}) ---")
            print("Most Frequent:", analysis.get_most_frequent(reg_freq, top_n))
            print("Least Frequent:", analysis.get_least_frequent(reg_freq, top_n))
        else:
            print("\nNo frequency data for regular numbers.")

    if analysis_type in ["all", "special"]:
        if spec_freq:
            print(f"\n--- Special Numbers (Top {top_n}) ---")
            print("Most Frequent:", analysis.get_most_frequent(spec_freq, top_n))
            print("Least Frequent:", analysis.get_least_frequent(spec_freq, top_n))
        else:
            print("\nNo frequency data for special numbers.")

    if args.plot:
        print("\nGenerating visualizations...")
        plot_path = os.path.join(DATA_DIR, 'analysis_plots')
        if not os.path.exists(plot_path):
            os.makedirs(plot_path)
            
        freq_plot_path = os.path.join(plot_path, 'frequency_distribution.png')
        trend_plot_path = os.path.join(plot_path, 'trend_analysis.png')
        
        visualization.plot_number_frequencies(reg_freq, spec_freq, freq_plot_path)
        visualization.plot_trend_analysis(history, trend_plot_path)
        print(f"Plots saved to {plot_path}")

def handle_manage_tags(args):
    """Handles the 'manage_tags' command."""
    # apply_default_tags is called when tagging module is imported.
    # tagging.number_tags is populated.
    print("Action: Manage tags...")

    if args.add_tag:
        try:
            num_str, tag_str = args.add_tag
            number = int(num_str)
            tagging.add_custom_tag(number, tag_str)
        except ValueError:
            print("Error: For --add_tag, number must be an integer. Format: <number> <tag>")
        except TypeError: # If args.add_tag is not a list of two items
            print("Error: For --add_tag, please provide number and tag. Format: <number> <tag>")
    elif args.view_tags_for_number:
        try:
            number = int(args.view_tags_for_number)
            tags = tagging.get_tags_for_number(number)
            if tags: # get_tags_for_number returns empty set for invalid or untagged numbers
                print(f"Tags for number {number}: {tags}")
            else: # Custom message if number is valid but has no tags, or if number is invalid
                if tagging.MIN_NUMBER <= number <= tagging.MAX_NUMBER:
                     print(f"No custom tags found for number {number}. Default tags might apply if not cleared (e.g. Odd/Even, Small/Big).")
                     print(f"To see all current tags including defaults: {tagging.number_tags.get(number, 'Not found or no tags at all')}")
                else:
                     print(f"Number {number} is invalid. Please use a number between {tagging.MIN_NUMBER} and {tagging.MAX_NUMBER}.")
        except ValueError:
            print("Error: For --view_tags_for_number, provide a valid integer.")
    elif args.view_numbers_for_tag:
        tag_str = args.view_numbers_for_tag
        numbers = tagging.get_numbers_with_tag(tag_str)
        if numbers:
            print(f"Numbers with tag '{tag_str}': {numbers}")
        else:
            # get_numbers_with_tag prints "Info: No numbers found with tag..."
            # So an additional print here might be redundant unless we want to customize it.
            print(f"No numbers found with tag '{tag_str}' (or tag is invalid).")
    else:
        # This case should not be reached if one of the group arguments is required.
        print("No action specified for manage_tags. Use --add_tag, --view_tags_for_number, or --view_numbers_for_tag.")


def handle_predict(args):
    """Handles the 'predict' command."""
    print("Action: Predict numbers...")
    history = data_input.load_history(DATA_FILE_PATH)
    if not history:
        print("Warning: No history data found. Predictions will be based on random fallback or very limited data.")
        # Allow prediction even with no history, functions have fallbacks.

    reg_freq, spec_freq = analysis.calculate_frequencies(history)

    print(f"Using method: {args.method}")
    if args.method == "basic":
        prediction_result = prediction.predict_numbers_basic(
            history,
            reg_freq,
            spec_freq,
            num_to_predict=args.num_to_predict,
            recent_draws_count=args.recent_draws
        )
    elif args.method == "tags":
        prediction_result = prediction.predict_numbers_with_tags(
            history,
            reg_freq,
            spec_freq,
            tagging.number_tags,
            num_to_predict=args.num_to_predict,
            recent_draws_count=args.recent_draws,
            tag_trend_draws=args.tag_trend_draws
        )
    elif args.method in ["markov", "bayes", "timeseries", "hybrid"]:
        prediction_result = prediction.predict_numbers_advanced(
            history,
            method=args.method,
            num_to_predict=args.num_to_predict
        )
    else:
        print(f"Error: Unknown prediction method '{args.method}'.")
        return

    print("\n--- Prediction ---")
    if prediction_result and 'regular' in prediction_result and 'special' in prediction_result:
        print(f"Predicted Regular Numbers: {prediction_result['regular']}")
        print(f"Predicted Special Number: {prediction_result['special']}")
    else:
        print("Error: Prediction did not return the expected result structure.")


def main():
    """Main function to drive the CLI/GUI application."""
    # 添加GUI启动支持
    if "--gui" in sys.argv:
        from lottery_analyzer.gui import launch_gui
        launch_gui()
        return
    
    ensure_data_dir_exists() # Ensure data directory is there before any operations.
    # Default tags are applied when 'tagging' module is imported.

    parser = argparse.ArgumentParser(description="Lottery Analyzer CLI", formatter_class=argparse.RawTextHelpFormatter)
    subparsers = parser.add_subparsers(title="actions", dest="action", required=True,
                                       help="Available actions to perform. Use <action> -h for more help.")

    # --- Add Draw Subparser ---
    parser_add = subparsers.add_parser("add_draw", help="Add a new lottery draw to the history.")
    parser_add.add_argument("--numbers", required=True, type=str, help="Comma-separated regular numbers (e.g., '1,2,3,4,5,6')")
    parser_add.add_argument("--special", required=True, type=str, help="The special number (e.g., '7')")
    parser_add.add_argument("--date", type=str, help="Date of the draw (YYYY-MM-DD). Defaults to current date.")
    parser_add.set_defaults(func=handle_add_draw)

    # --- Show Analysis Subparser ---
    parser_analysis = subparsers.add_parser("show_analysis", help="Show frequency analysis of lottery numbers.")
    parser_analysis.add_argument("--top", type=int, default=5, help="Number of most/least frequent numbers to show (default: 5)")
    parser_analysis.add_argument("--type", choices=["all", "regular", "special"], default="all",
                                 help="Type of numbers to analyze (default: all)")
    parser_analysis.add_argument("--plot", action="store_true",
                               help="Generate visualization plots")
    parser_analysis.set_defaults(func=handle_show_analysis)

    # --- Manage Tags Subparser ---
    parser_tags = subparsers.add_parser("manage_tags", help="Manage tags for numbers.")
    group_tags = parser_tags.add_mutually_exclusive_group(required=True)
    group_tags.add_argument("--add_tag", nargs=2, metavar=('NUMBER', 'TAG'),
                            help="Add a custom tag to a number (e.g., --add_tag 7 Lucky)")
    group_tags.add_argument("--view_tags_for_number", metavar='NUMBER',
                            help="View all tags for a specific number.")
    group_tags.add_argument("--view_numbers_for_tag", metavar='TAG',
                            help="View all numbers associated with a specific tag.")
    parser_tags.set_defaults(func=handle_manage_tags)

    # --- Predict Subparser ---
    parser_predict = subparsers.add_parser("predict", help="Predict lottery numbers based on historical data.")
    parser_predict.add_argument("--method", 
                              choices=["basic", "tags", "markov", "bayes", "timeseries", "hybrid"],
                              default="hybrid",
                              help="预测方法 (默认: hybrid)")
    parser_predict.add_argument("--num_to_predict", type=int, default=NUM_REGULAR,
                                help=f"Number of regular numbers to predict (default: {NUM_REGULAR})")
    parser_predict.add_argument("--recent_draws", type=int, default=10,
                                help="Number of recent draws to consider for hot/cold analysis (default: 10)")
    parser_predict.add_argument("--tag_trend_draws", type=int, default=20,
                                help="Number of recent draws for tag trend analysis (default: 20, for 'tags' method)")
    parser_predict.set_defaults(func=handle_predict)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This case should ideally not be reached if subparsers are required.
        parser.print_help()

if __name__ == '__main__':
    main()
