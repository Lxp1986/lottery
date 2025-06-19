import argparse
import os
from datetime import datetime
import sys
from typing import Dict, List, Optional, Any
from argparse import Namespace

# Project modules
from lottery_analyzer import config  # 确保引入config模块
from lottery_analyzer import data_input
from lottery_analyzer import tagging
from lottery_analyzer import analysis
from lottery_analyzer import prediction
from lottery_analyzer import visualization

# Constants
DATA_DIR = config.DATA_DIR
DATA_FILE_PATH = config.DATA_FILE_PATH
MIN_NUMBER = config.MIN_NUMBER
MAX_NUMBER = config.MAX_NUMBER
NUM_REGULAR = config.NUM_REGULAR
NUM_SPECIAL = config.NUM_SPECIAL

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

def parse_numbers_input(numbers_str: str, expected_count: int, label: str) -> Optional[List[int]]:
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

def handle_add_draw(args: Namespace) -> None:
    """Handles the 'add_draw' command."""
    print("Action: Add new draw...")
    regular_numbers = parse_numbers_input(args.numbers, config.NUM_REGULAR, "regular")
    if not regular_numbers:
        return

    special_number_list = parse_numbers_input(args.special, config.NUM_SPECIAL, "special")
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

    # Load existing history
    try:
        history = data_input.load_history(config.DATA_FILE_PATH)
    except ValueError as e:
        # Handle cases where the history file might be corrupt or not loadable
        # For this fix, we'll assume a fresh start if loading fails,
        # or you could choose to abort.
        print(f"Warning: Could not load existing history: {e}. Starting with new draw as the only entry.")
        history = []

    # Append the new draw
    history.append(new_draw)

    # Save the updated history
    # data_input.save_history expects a list of draws
    try:
        data_input.save_history(history, config.DATA_FILE_PATH)
        print(f"Successfully added draw for date {date_str} and saved updated history.")
    except IOError as e:
        print(f"Error: Failed to save history: {e}")
        # Optionally, you might want to revert the history.append(new_draw) here
        # or handle the error more gracefully. For now, just printing error.

def format_number(num: int) -> str:
    """格式化号码，个位数前面添加0"""
    return f"{num:02d}"

def handle_predict(args):
    """处理预测命令"""
    print("Action: Predict numbers...")
    history = data_input.load_history(DATA_FILE_PATH)
    if not history:
        print("Warning: No history data found. Predictions will be based on random fallback or very limited data.")
        return

    reg_freq, spec_freq = analysis.calculate_frequencies(history)
    
    print(f"\n=== 生成 {args.num_predictions} 组预测号码 ===\n")
    
    for i in range(args.num_predictions):
        print(f"\n--- 第 {i+1} 组预测 ---")
        if args.method == "all":
            # 使用所有预测方法的综合结果
            prediction_result = prediction.predict_all_methods(
                history_data=history, # Pass history directly
                num_to_predict=args.num_to_predict,
                recent_draws_count=args.recent_draws,
                tag_trend_draws=args.tag_trend_draws
            )
            print("综合预测结果:")
        else:
            # 使用单一方法的预测结果
            prediction_result = get_prediction_by_method(
                args.method, history, reg_freq, spec_freq, tagging.number_tags,
                args.num_to_predict, args.recent_draws, args.tag_trend_draws
            )
            print(f"使用 {args.method} 方法:")
            
        if prediction_result and 'regular' in prediction_result and 'special' in prediction_result:
            regular_nums = [f"{num:02d}" for num in prediction_result['regular']]
            special_num = f"{prediction_result['special']:02d}"
            print(f"预测正码: {', '.join(regular_nums)}")
            print(f"预测特码: {special_num}")
            
            if args.method == "all":
                print("\n各方法预测结果:")
                for method, result in prediction_result['method_results'].items():
                    regular_nums = [f"{num:02d}" for num in result['regular']]
                    special_num = f"{result['special']:02d}"
                    print(f"{method:10}: {', '.join(regular_nums)} + [{special_num}]")

            # Display label predictions if available (primarily for 'all' method)
            if 'label_predictions' in prediction_result:
                print("\n--- 标签预测 ---")
                label_preds = prediction_result['label_predictions']
                if label_preds:
                    all_categories_empty = True
                    for category, tags_list in label_preds.items():
                        if tags_list:
                            all_categories_empty = False
                            print(f"{category}: {', '.join(tags_list)}")
                        else:
                            print(f"{category}: (无预测结果)")
                    if all_categories_empty:
                        print("所有标签类别均无预测结果。")
                else:
                    # This case implies label_preds itself is empty or None
                    print("未能生成标签预测。")
        else:
            print("Error: Invalid prediction result structure.")
            
def get_prediction_by_method(method, history, reg_freq, spec_freq, number_tags, 
                           num_to_predict, recent_draws, tag_trend_draws):
    """根据指定方法获取预测结果"""
    if method == "basic":
        return prediction.predict_numbers_basic(
            history, reg_freq, spec_freq,
            num_to_predict=num_to_predict,
            recent_draws_count=recent_draws
        )
    elif method == "tags":
        return prediction.predict_numbers_with_tags(
            history, reg_freq, spec_freq, number_tags,
            num_to_predict=num_to_predict,
            recent_draws_count=recent_draws,
            tag_trend_draws=tag_trend_draws
        )
    else:
        return prediction.predict_numbers_advanced(
            history, method=method,
            num_to_predict=num_to_predict
        )

def handle_show_analysis(args):
    """Handles the 'show_analysis' command."""
    print("Action: Show analysis...")
    history = data_input.load_history(config.DATA_FILE_PATH)
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
            most_freq = [(format_number(n), f) for n, f in analysis.get_most_frequent(reg_freq, top_n)]
            least_freq = [(format_number(n), f) for n, f in analysis.get_least_frequent(reg_freq, top_n)]
            print("Most Frequent:", most_freq)
            print("Least Frequent:", least_freq)
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


def handle_initialize(args):
    """处理初始化命令"""
    if not args.force:
        response = input("警告：这将清空所有历史数据！是否继续？(y/N) ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    if data_input.initialize_data():
        print("数据已成功初始化")
        print(f"备份文件保存在: {data_input.BACKUP_DIR}")
    else:
        print("初始化失败")

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
                              choices=["basic", "tags", "markov", "bayes", "timeseries", "hybrid", "all"],
                              default="all",
                              help="预测方法 (默认: all - 使用所有方法)")
    parser_predict.add_argument("--num_predictions", type=int, default=5,
                              help="生成预测组数 (默认: 5)")
    parser_predict.add_argument("--num_to_predict", type=int, default=config.NUM_REGULAR,
                                help=f"Number of regular numbers to predict (default: {config.NUM_REGULAR})")
    parser_predict.add_argument("--recent_draws", type=int, default=10,
                                help="Number of recent draws to consider for hot/cold analysis (default: 10)")
    parser_predict.add_argument("--tag_trend_draws", type=int, default=20,
                                help="Number of recent draws for tag trend analysis (default: 20, for 'tags' method)")
    parser_predict.set_defaults(func=handle_predict)

    # --- Initialize Subparser ---
    parser_init = subparsers.add_parser("initialize", help="初始化系统，清空所有数据")
    parser_init.add_argument("--force", action="store_true", help="强制初始化，不提示确认")
    parser_init.set_defaults(func=handle_initialize)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # This case should ideally not be reached if subparsers are required.
        # This case should ideally not be reached if subparsers are required.if __name__ == '__main__':
        parser.print_help()

if __name__ == '__main__':
    main()
