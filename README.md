# Lottery Analysis and Prediction Tool

## Overview

This Python application analyzes historical lottery data to provide insights into number frequencies and predict potential future winning numbers. It is designed for lotteries with a 6+1 format (6 regular numbers and 1 special number) drawn from a range of 1 to 49.

## Features

*   **Input Historical Data**: Add past lottery draws to a CSV file.
*   **Frequency Analysis**: Identify the most and least common regular and special numbers.
*   **Number Tagging**:
    *   Automatic default tags: "Odd", "Even", "Small" (1-24), "Big" (25-49).
    *   Add custom string tags to numbers.
*   **Number Prediction**:
    *   **Basic Method**: Predicts numbers based on overall frequency and recent "hot" number trends.
    *   **Tag-Based Method**: Enhances basic prediction by considering trends of number tags in recent draws.

## Project Structure

The project is organized into several Python modules within the `lottery_analyzer` package:

*   `data_input.py`: Handles loading and saving of lottery history data from/to CSV.
*   `tagging.py`: Manages the tagging system for numbers.
*   `analysis.py`: Contains functions for frequency calculations.
*   `prediction.py`: Implements the number prediction algorithms.
*   `main.py`: Provides the command-line interface (CLI) to interact with the application.
*   `tests/`: Contains unit tests for various modules.

## Setup and Installation

1.  **Python Version**: Requires Python 3.7 or higher (due to dictionary insertion order being relied upon by `collections.Counter` in some tests and potentially in `prediction.py` logic, and f-string usage).
2.  **Libraries**: This project requires several external Python libraries. You can install them using pip and the provided `requirements.txt` file.
3.  **Clone the Repository (if applicable)**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **Data Directory**: The application will automatically create a `data/` directory in the project root if it doesn't exist, where `history.csv` will be stored.

## Data File Format (`data/history.csv`)

The historical lottery data is stored in `data/history.csv`.

*   **Format**: CSV (Comma Separated Values)
*   **Header Row**: `date,n1,n2,n3,n4,n5,n6,special_number`
*   **Columns**:
    *   `date`: The date of the draw in YYYY-MM-DD format.
    *   `n1` to `n6`: The six regular numbers drawn. These should be integers between 1 and 49, and unique within the draw.
    *   `special_number`: The special or bonus number. This should be an integer between 1 and 49 and distinct from the regular numbers in that draw.

*   **Example Row**:
    ```csv
    date,n1,n2,n3,n4,n5,n6,special_number
    2023-01-01,5,12,23,34,40,45,7
    ```

## Usage (CLI Examples)

All commands are run from the root directory of the project. The main entry point is `main.py` within the `lottery_analyzer` package.

**General Command Structure**:
`python -m lottery_analyzer.main <command> [options]`

You can get help for any command using `-h` or `--help`:
`python -m lottery_analyzer.main -h`
`python -m lottery_analyzer.main add_draw -h`

### 1. Adding a New Draw

```bash
# Add a draw with a specific date
python -m lottery_analyzer.main add_draw --numbers "1,2,3,4,5,6" --special "7" --date "2023-10-26"

# Add a draw (uses current date if --date is omitted)
python -m lottery_analyzer.main add_draw --numbers "10,15,20,25,30,35" --special "40"
```
*Input validation ensures numbers are within range (1-49), unique for regular numbers, and the special number is distinct from regular numbers.*

### 2. Showing Analysis

```bash
# Show overall analysis (top 5 by default)
python -m lottery_analyzer.main show_analysis

# Show top 3 most/least frequent numbers
python -m lottery_analyzer.main show_analysis --top 3

# Show analysis only for regular numbers (top 5)
python -m lottery_analyzer.main show_analysis --type regular --top 5

# Show analysis only for special numbers
python -m lottery_analyzer.main show_analysis --type special
```

### 查看分析结果并生成可视化

```bash
# 显示分析结果并生成可视化图表
python -m lottery_analyzer.main show_analysis --plot

# 查看特定类型的分析并生成图表
python -m lottery_analyzer.main show_analysis --type regular --plot
```

生成的图表将保存在 `data/analysis_plots` 目录下:
- `frequency_distribution.png`: 显示号码频率分布
- `trend_analysis.png`: 显示近期开奖趋势

### 3. Managing Tags

Default tags ("Odd", "Even", "Small", "Big") are automatically applied. You can add custom tags.
**Note**: Custom tags are currently stored in-memory and are **not persisted** between different runs of the application. They will reset each time the application starts.

```bash
# Add a custom tag "MyFavorite" to number 10
python -m lottery_analyzer.main manage_tags --add_tag 10 "MyFavorite"

# View all tags for number 10 (will include default tags and any custom tags added in the current session)
python -m lottery_analyzer.main manage_tags --view_tags_for_number 10

# View all numbers that have the "Small" tag
python -m lottery_analyzer.main manage_tags --view_numbers_for_tag "Small"

# View numbers with a custom tag (if added in the same session)
python -m lottery_analyzer.main manage_tags --view_numbers_for_tag "MyFavorite"
```

### 4. Getting Predictions

```bash
# Get a prediction using the default 'tags' method
python -m lottery_analyzer.main predict

# Get a prediction using the 'basic' method
python -m lottery_analyzer.main predict --method basic

# Predict 5 regular numbers, using last 15 draws for recency analysis
python -m lottery_analyzer.main predict --num_to_predict 5 --recent_draws 15

# Use 'tags' method, considering last 25 draws for tag trend analysis
python -m lottery_analyzer.main predict --method tags --tag_trend_draws 25
```

## GUI 界面使用

启动图形界面:
```bash
python -m lottery_analyzer.main --gui
```

GUI功能包括:
- 数据输入: 通过表单添加新的开奖记录
- 数据分析: 查看频率分析并生成可视化图表
- 号码预测: 使用基础或标签方法进行预测
- 标签管理: 添加和查看号码标签

## Running Tests

Unit tests are provided for core modules. To run the tests, navigate to the project root directory and execute:

```bash
python -m unittest discover tests -v
```

## Future Enhancements (Optional)

*   **Persistent Custom Tags**: Implement saving and loading of custom tags to a file.
*   **Advanced Prediction Models**: Explore and integrate more sophisticated machine learning or statistical models for prediction.
*   **Data Visualization**: Add options to visualize number frequencies or trends.
*   **Graphical User Interface (GUI)**: Develop a GUI for easier interaction.
*   **Configuration File**: Allow configuration of parameters (e.g., lottery number range, count of numbers) via a config file.

# 六合彩分析预测系统

## 概述

这是一个基于 Python 开发的六合彩分析预测工具，支持分析历史开奖数据、预测号码、管理号码标签等功能。系统采用 6+1 的开奖格式（6个正码和1个特别号码），号码范围为1-49。

## 主要功能

### 1. 数据管理
- 录入历史开奖记录
- 导入/导出 CSV 格式的历史数据
- 数据自动备份

### 2. 数据分析
- 号码频率分析
- 冷热号码分析
- 自动生成频率分布图和趋势图

### 3. 号码预测
- 基础预测：基于频率和近期热门号码
- 标签预测：结合号码标签特征
- 马尔可夫预测：使用马尔可夫链模型
- 贝叶斯预测：基于贝叶斯概率
- 时间序列预测：分析号码趋势
- 灰度预测：使用灰色系统理论
- 综合预测：融合多种预测方法的结果

### 4. 标签系统
- 自动标签：奇偶、大小(1-24为小，25-49为大)
- 自定义标签：支持添加和管理自定义标签

## 环境要求

- Python 3.7+
- PyQt6
- pandas
- numpy
- matplotlib
- seaborn

## 安装

1. 克隆仓库:
```bash 
git clone https://github.com/YOUR_USERNAME/lottery.git
cd lottery
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 数据目录：应用程序会自动在项目根目录创建 `data/` 目录（如果尚不存在），历史数据将存储在此目录下。
