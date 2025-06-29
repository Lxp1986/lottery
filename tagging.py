import json
import os
import shutil
from datetime import datetime
from typing import Dict, Set, List

# 基础配置
MIN_NUMBER = 1
MAX_NUMBER = 49

# 默认标签文件路径
DEFAULT_TAGS_FILE = os.path.join("data", "tags.json")

# 标签类型顺序定义
class TagTypes:
    BASIC = "基础特征"    # 单双、大小
    SUM = "合数特征"      # 合单合双
    TAIL = "尾数特征"     # 0-9尾
    ZODIAC = "生肖"      # 12生肖
    ELEMENTS = "五行"     # 金木水火土
    COLOR = "波色"        # 红绿蓝

# 表情符号定义
ZODIAC_EMOJI = {
    "鼠": "🐭", "牛": "🐮", "虎": "🐯", "兔": "🐰",
    "龙": "🐲", "蛇": "🐍", "马": "🐴", "羊": "🐑",
    "猴": "🐵", "鸡": "🐔", "狗": "🐕", "猪": "🐷"
}

ELEMENTS_EMOJI = {
    "金": "💰",
    "木": "🌳",
    "水": "💧",
    "火": "🔥",
    "土": "🌍"
}

COLOR_EMOJI = {
    "红波": "🔴",
    "蓝波": "🔵",
    "绿波": "🟢"
}

# 重新定义固定的映射关系
ZODIAC_MAPPING = {
    "蛇": [1, 13, 25, 37, 49],
    "龙": [2, 14, 26, 38],
    "兔": [3, 15, 27, 39],
    "虎": [4, 16, 28, 40],
    "牛": [5, 17, 29, 41],
    "鼠": [6, 18, 30, 42],
    "猪": [7, 19, 31, 43],
    "狗": [8, 20, 32, 44],
    "鸡": [9, 21, 33, 45],
    "猴": [10, 22, 34, 46],
    "羊": [11, 23, 35, 47],
    "马": [12, 24, 36, 48]
}

ELEMENTS_MAPPING = {
    "金": [3, 4, 11, 12, 25, 26, 33, 34, 41, 42],
    "木": [7, 8, 15, 16, 23, 24, 37, 38, 45, 46],
    "水": [13, 14, 21, 22, 29, 30, 43, 44],
    "火": [1, 2, 9, 10, 17, 18, 31, 32, 39, 40, 47, 48],
    "土": [5, 6, 19, 20, 27, 28, 35, 36, 49]
}

COLOR_MAPPING = {
    "红波": [1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46],
    "蓝波": [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48],
    "绿波": [5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49]
}

# 全局变量
number_tags: Dict[int, Set[str]] = {}

def get_number_features(num: int) -> Dict[str, Set[str]]:
    """获取号码的所有特征，按类型分组返回"""
    features = {
        TagTypes.BASIC: set(),     # 基础特征
        TagTypes.SUM: set(),       # 合数特征
        TagTypes.TAIL: set(),      # 尾数特征
    }
    
    # 1. 基础特征 (单双、大小)
    features[TagTypes.BASIC].add("单" if num % 2 == 1 else "双")
    features[TagTypes.BASIC].add("大" if num >= 25 else "小")
    
    # 2. 合数特征 (十位+个位的单双)
    tens = num // 10
    ones = num % 10
    digit_sum = tens + ones
    features[TagTypes.SUM].add("合单" if digit_sum % 2 == 1 else "合双")
    
    # 3. 尾数特征
    features[TagTypes.TAIL].add(f"{ones}尾" if ones > 0 else "0尾")
    
    return features

def generate_zodiac_mapping(current_year: int = None) -> dict:
    """根据年份生成生肖号码映射"""
    if current_year is None:
        current_year = datetime.now().year
        
    # 2025年蛇年的基础映射，倒序排列(固定不变的映射关系)
    BASE_MAPPING = {
        "蛇": [1, 13, 25, 37, 49],
        "龙": [2, 14, 26, 38],
        "兔": [3, 15, 27, 39],
        "虎": [4, 16, 28, 40],
        "牛": [5, 17, 29, 41],
        "鼠": [6, 18, 30, 42],
        "猪": [7, 19, 31, 43],
        "狗": [8, 20, 32, 44],
        "鸡": [9, 21, 33, 45],
        "猴": [10, 22, 34, 46],
        "羊": [11, 23, 35, 47],
        "马": [12, 24, 36, 48]
    }
    
    # 修改基准年份为2025
    BASE_YEAR = 2025
    
    # 计算年份差值
    years_diff = current_year - BASE_YEAR
    shift = years_diff % 12
    
    # 生成新的映射
    zodiac_order = list(BASE_MAPPING.keys())
    new_mapping = {}
    
    # 根据年份调整顺序，保持倒序
    for i, zodiac in enumerate(zodiac_order):
        new_index = (i + shift) % 12
        new_zodiac = zodiac_order[new_index]
        new_mapping[new_zodiac] = BASE_MAPPING[zodiac]
    
    return new_mapping  # 确保总是返回一个有效的字典

def apply_default_tags() -> None:
    """应用所有默认标签"""
    global number_tags
    number_tags = {num: set() for num in range(MIN_NUMBER, MAX_NUMBER + 1)}
    
    # 获取当前年份的生肖映射
    # current_zodiac_mapping = generate_zodiac_mapping() # Modified to use fixed ZODIAC_MAPPING for consistency with examples
    
    for num in range(MIN_NUMBER, MAX_NUMBER + 1):
        # 应用基础特征
        features = get_number_features(num)
        for feature_type, feature_set in features.items():
            number_tags[num].update(feature_set)
        
        # 应用生肖标签
        # Use fixed ZODIAC_MAPPING to ensure example output consistency
        for zodiac, numbers in ZODIAC_MAPPING.items():
            if num in numbers:
                number_tags[num].add(f"生肖-{zodiac}")
        
        # 应用五行标签
        for element, numbers in ELEMENTS_MAPPING.items():
            if num in numbers:
                number_tags[num].add(f"五行-{element}")
        
        # 应用波色标签
        for color, numbers in COLOR_MAPPING.items():
            if num in numbers:
                number_tags[num].add(color)

def format_tags_by_type(number: int) -> str:
    """按固定顺序格式化显示号码的所有标签"""
    if number not in number_tags:
        return f"号码 {number:02d} 无效"
    
    features = get_number_features(number)
    result = [f"例如：号码 {number:02d} 的特征:"]
    
    # 1. 基础特征
    # Custom sort: "单" or "双" first, then "大" or "小"
    basic_tags_list = list(features[TagTypes.BASIC])
    def sort_key_basic(tag):
        if tag in ["单", "双"]:
            return 0  # Odd/Even comes first
        if tag in ["大", "小"]:
            return 1  # Big/Small comes second
        return 2 # Other tags (if any)
    basic_tags_list.sort(key=sort_key_basic)
    if basic_tags_list:
        result.append(f"基础特征: {', '.join(basic_tags_list)}")
    
    # 2. 合数特征
    sum_tags = sorted(features[TagTypes.SUM])
    if sum_tags:
        result.append(f"合数特征: {sum_tags[0]}")
    
    # 3. 尾数特征
    tail_tags = sorted(features[TagTypes.TAIL])
    if tail_tags:
        result.append(f"尾数特征: {tail_tags[0]}")
    
    # 4. 生肖
    zodiac = next((tag.split('-')[1] for tag in number_tags[number] if tag.startswith("生肖-")), None)
    if zodiac:
        result.append(f"生肖: {zodiac}{ZODIAC_EMOJI[zodiac]}")
    
    # 5. 五行
    element = next((tag.split('-')[1] for tag in number_tags[number] if tag.startswith("五行-")), None)
    if element:
        result.append(f"五行: {element}{ELEMENTS_EMOJI[element]}")
    
    # 6. 波色
    color = next((tag for tag in number_tags[number] if "波" in tag), None)
    if color:
        result.append(f"波色: {color}{COLOR_EMOJI[color]}")
    
    return "\n".join(result)

def save_tags(filepath: str = None, auto_save: bool = True) -> bool:
    """保存标签数据
    
    Args:
        filepath: 保存路径，如果为None则使用默认路径
        auto_save: 是否同时保存到默认路径
    """
    try:
        # 确保目录存在
        target_file = filepath if filepath else DEFAULT_TAGS_FILE
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        # 如果文件存在，先创建备份
        if os.path.exists(target_file):
            backup_dir = os.path.join(os.path.dirname(target_file), "backup")
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = os.path.join(backup_dir, os.path.basename(target_file))
            shutil.copy2(target_file, backup_file)
        
        # 保存数据
        tags_dict = {str(k): list(v) for k, v in number_tags.items()}
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(tags_dict, f, ensure_ascii=False, indent=2)
            
        # 如果是保存到自定义路径且启用了自动保存，则同时保存到默认路径
        if filepath and auto_save and filepath != DEFAULT_TAGS_FILE:
            with open(DEFAULT_TAGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tags_dict, f, ensure_ascii=False, indent=2)
            print(f"Info: 标签数据已同时保存到系统默认路径: {DEFAULT_TAGS_FILE}")
            
        return True
    except Exception as e:
        print(f"Error: Failed to save tags: {e}")
        return False

def load_tags(filepath: str = None) -> bool:
    """从文件加载标签数据"""
    global number_tags
    try:
        if filepath is None:
            filepath = os.path.join("data", "tags.json")
            
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_tags = json.load(f)
                # 转换键为整数，值为集合
                number_tags = {int(k): set(v) for k, v in loaded_tags.items()}
            return True
    except Exception as e:
        print(f"Error: Failed to load tags: {e}")
        apply_default_tags()  # 加载失败时使用默认标签
        return False
    return False

def add_custom_tag(number: int, tag: str) -> None:
    """
    Adds a custom tag to a specific number.

    Args:
        number: The number (1-49) to tag.
        tag: The custom tag string to add.
    """
    global number_tags
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        print(f"Error: Number {number} is out of range ({MIN_NUMBER}-{MAX_NUMBER}). Cannot add tag '{tag}'.")
        return

    if not tag or not isinstance(tag, str) or tag.isspace():
        print(f"Error: Invalid tag '{tag}'. Tag cannot be empty or just whitespace.")
        return

    if number not in number_tags:
        # This case should ideally not happen if apply_default_tags is called first,
        # but as a safeguard, initialize it.
        number_tags[number] = set()

    number_tags[number].add(tag)
    save_tags()
    print(f"Info: Custom tag '{tag}' added to number {number}.")

def remove_tag(number: int, tag: str) -> None:
    """移除指定号码的标签
    
    Args:
        number: 号码(1-49)
        tag: 要移除的标签
    """
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        print(f"Error: 号码 {number} 超出范围 ({MIN_NUMBER}-{MAX_NUMBER})")
        return

    if number not in number_tags or tag not in number_tags[number]:
        print(f"Warning: 号码 {number} 没有标签 '{tag}'")
        return
        
    try:
        number_tags[number].remove(tag)
        save_tags()  # 自动保存更改
        print(f"Info: 已从号码 {number} 移除标签 '{tag}'")
    except Exception as e:
        print(f"Error: 移除标签失败: {str(e)}")

def remove_custom_tag(number: int, tag: str) -> None:
    """移除自定义标签"""
    if MIN_NUMBER <= number <= MAX_NUMBER and tag in number_tags.get(number, set()):
        number_tags[number].remove(tag)
        save_tags()

def get_tags_for_number(number: int) -> set[str]:
    """
    Retrieves all tags associated with a given number.

    Args:
        number: The number (1-49) to get tags for.

    Returns:
        A set of tags for the number. Returns an empty set if the number
        is invalid or has no tags.
    """
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        print(f"Warning: Number {number} is out of range ({MIN_NUMBER}-{MAX_NUMBER}). Returning empty set of tags.")
        return set()

    return number_tags.get(number, set())

def get_numbers_with_tag(tag: str) -> list[int]:
    """
    Finds all numbers that have a specific tag.

    Args:
        tag: The tag string to search for.

    Returns:
        A list of numbers that have the given tag. Returns an empty list
        if the tag is not found for any number or the tag is invalid.
    """
    if not tag or not isinstance(tag, str) or tag.isspace():
        print(f"Warning: Invalid tag '{tag}' provided for search. Returning empty list.")
        return []

    numbers_found = []
    for number, tags_set in number_tags.items():
        if tag in tags_set:
            numbers_found.append(number)

    if not numbers_found:
        print(f"Info: No numbers found with tag '{tag}'.")
    return sorted(numbers_found) # Return sorted list for consistency

def get_numbers_by_feature(feature: str) -> List[int]:
    """获取具有特定特征的所有号码"""
    return sorted([num for num, tags in number_tags.items() if feature in tags])

# Helper functions to get specific tag categories for a number

def get_dx_tag(number: int) -> str | None:
    """获取号码的单双标签 (e.g., '单', '双')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    return "单" if number % 2 == 1 else "双"

def get_ds_tag(number: int) -> str | None:
    """获取号码的大小标签 (e.g., '大', '小')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    # Boundary based on get_number_features (25 and up is '大')
    return "大" if number >= 25 else "小"

def get_sum_feature_tag(number: int) -> str | None:
    """获取号码的合数特征标签 (e.g., '合单', '合双')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    tens = number // 10
    ones = number % 10
    digit_sum = tens + ones
    return "合单" if digit_sum % 2 == 1 else "合双"

def get_tail_feature_tag(number: int) -> str | None:
    """获取号码的尾数特征标签 (e.g., '0尾', '5尾')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    ones = number % 10
    return f"{ones}尾"

def get_zodiac_tag(number: int) -> str | None:
    """获取号码的生肖标签 (e.g., '生肖-猪')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    for zodiac, numbers in ZODIAC_MAPPING.items():
        if number in numbers:
            return f"生肖-{zodiac}"
    return None # Should not be reached with current complete ZODIAC_MAPPING

def get_element_tag(number: int) -> str | None:
    """获取号码的五行标签 (e.g., '五行-木')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    for element, numbers in ELEMENTS_MAPPING.items():
        if number in numbers:
            return f"五行-{element}"
    return None # Should not be reached with current complete ELEMENTS_MAPPING

def get_color_tag(number: int) -> str | None:
    """获取号码的波色标签 (e.g., '红波', '蓝波', '绿波')."""
    if not (MIN_NUMBER <= number <= MAX_NUMBER):
        return None
    for color, numbers in COLOR_MAPPING.items():
        if number in numbers:
            return color
    return None # Should not be reached with current complete COLOR_MAPPING

def export_tags(filepath: str) -> bool:
    """导出标签数据"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(number_tags, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"导出标签失败: {str(e)}")
        return False

def import_tags(filepath: str) -> bool:
    """导入标签数据"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            number_tags.clear()
            number_tags.update(data)
            
            # 同时保存到系统文件
            if filepath != DEFAULT_TAGS_FILE:
                export_tags(DEFAULT_TAGS_FILE)
                
        return True
    except Exception as e:
        print(f"导入标签失败: {str(e)}")
        return False

# 初始化默认标签
apply_default_tags()


if __name__ == '__main__':
    print("\n--- Testing tagging system ---")

    # 1. Test apply_default_tags (already called on import)
    print("\n1. Default tags (first 5 numbers):")
    for i in range(1, 6):
        print(f"Number {i}: {get_tags_for_number(i)}")
    print(f"Number 24: {get_tags_for_number(24)}")
    print(f"Number 25: {get_tags_for_number(25)}")
    print(f"Number 49: {get_tags_for_number(49)}")

    # 2. Test add_custom_tag
    print("\n2. Adding custom tags:")
    add_custom_tag(7, "Lucky")
    add_custom_tag(42, "Universe")
    add_custom_tag(7, "Favorite") # Add another tag to 7
    add_custom_tag(100, "TooHigh") # Invalid number
    add_custom_tag(10, "") # Invalid tag
    add_custom_tag(10, "  ") # Invalid tag


    # 3. Test get_tags_for_number
    print("\n3. Getting tags for specific numbers:")
    print(f"Tags for 7: {get_tags_for_number(7)}")
    print(f"Tags for 42: {get_tags_for_number(42)}")
    print(f"Tags for 10: {get_tags_for_number(10)}") # No custom tag added here, should show defaults
    print(f"Tags for 50: {get_tags_for_number(50)}") # Invalid number

    # 4. Test get_numbers_with_tag
    print("\n4. Getting numbers with specific tags:")
    print(f"Numbers with 'Odd': {get_numbers_with_tag('Odd')[:5]}... (first 5)") # Show first 5 for brevity
    print(f"Numbers with 'Big': {get_numbers_with_tag('Big')[:5]}... (first 5)")
    print(f"Numbers with 'Lucky': {get_numbers_with_tag('Lucky')}")
    print(f"Numbers with 'Universe': {get_numbers_with_tag('Universe')}")
    print(f"Numbers with 'Favorite': {get_numbers_with_tag('Favorite')}")
    print(f"Numbers with 'DoesNotExist': {get_numbers_with_tag('DoesNotExist')}")
    print(f"Numbers with '': {get_numbers_with_tag('')}") # Invalid tag

    # Test re-applying default tags (should not duplicate or remove custom tags)
    print("\n5. Re-applying default tags (testing idempotency and preservation of custom tags):")
    apply_default_tags()
    print(f"Tags for 7 after re-applying defaults: {get_tags_for_number(7)}")
    print(f"Tags for 42 after re-applying defaults: {get_tags_for_number(42)}")

    # Test adding custom tag to a number that might not have been initialized by default (though current apply_default_tags covers all)
    # This scenario is less likely with current apply_default_tags, but tests robustness
    # For example, if apply_default_tags was conditional.
    # We'll simulate by clearing a number's tags first.
    print("\n6. Test adding custom tag to a number whose tags might have been cleared (simulated):")
    if 15 in number_tags: # number_tags is global
        number_tags[15].clear()
        print(f"Tags for 15 after clearing: {get_tags_for_number(15)}")
    add_custom_tag(15, "SpecialFifteen")
    print(f"Tags for 15 after adding 'SpecialFifteen': {get_tags_for_number(15)}")
    # Now re-apply defaults to see if it correctly adds default tags back without losing "SpecialFifteen"
    apply_default_tags() # This will re-add Odd/Small
    print(f"Tags for 15 after re-applying defaults again: {get_tags_for_number(15)}")

    print("\n--- Subtask specific output ---")
    print("\n--- Output for 07 ---")
    print(format_tags_by_type(7))
    print("\n--- Output for 49 ---")
    print(format_tags_by_type(49))

    print("\n--- End of tagging system tests ---")