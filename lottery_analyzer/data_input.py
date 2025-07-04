import csv
import os
import shutil
from typing import List, Dict
from datetime import datetime

# 系统数据目录设置
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backup")
SYSTEM_FILE = os.path.join(DATA_DIR, "history.csv")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# 修改CSV文件头
CSV_HEADER = ['date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'special_number']

def _validate_draw_data(draw: dict, previous_draws: list) -> bool:
    """验证开奖数据的有效性，包括重复性检查
    
    Args:
        draw: 当前开奖记录
        previous_draws: 之前的开奖记录列表
    
    Returns:
        bool: 数据是否有效
    """
    if not draw or 'date' not in draw or 'numbers' not in draw or 'special' not in draw:
        print(f"警告: 数据格式不完整: {draw}")
        return False
        
    # 检查与最近10期的重复性
    recent_draws = previous_draws[-10:] if previous_draws else []
    for prev_draw in recent_draws:
        if (draw['numbers'] == prev_draw['numbers'] and 
            draw['special'] == prev_draw['special'] and
            draw['date'] != prev_draw['date']):
            print(f"警告: 检测到重复数据 - 期号:{draw['date']}, 与期号:{prev_draw['date']}重复")
            return False
            
    return True

def save_history(draw_data: List[Dict], custom_path: str = None) -> None:
    """保存历史数据，带重复性检查和期号去重"""
    try:
        # 验证每条数据
        validated_data = []
        seen_dates = set()
        for i, draw in enumerate(draw_data):
            date = draw.get('date')
            if date in seen_dates:
                continue  # 跳过重复期号
            if _validate_draw_data(draw, validated_data):
                validated_data.append(draw)
                seen_dates.add(date)
            else:
                print(f"跳过无效数据: {draw}")
        
        # 保存验证后的数据
        _save_to_file(validated_data, SYSTEM_FILE)
        
        if custom_path and custom_path != SYSTEM_FILE:
            _save_to_file(validated_data, custom_path)
            
    except Exception as e:
        raise IOError(f"保存失败: {str(e)}")

def _save_to_file(data: List[Dict], filepath: str) -> None:
    """保存数据到指定文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    mode = 'w'  # 总是重写文件
    with open(filepath, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        for draw in data:
            # 确保期号格式正确
            draw_id = draw['date']
            if not (draw_id.isdigit() and len(draw_id) == 7):
                print(f"警告: 跳过无效期号格式: {draw_id}")
                continue
                
            row = {
                'date': draw_id,
                'special_number': draw['special']
            }
            # 保持原始输入顺序，不排序
            for i, num in enumerate(draw['numbers'], 1):
                row[f'n{i}'] = f"{num:02d}"
            writer.writerow(row)

def load_history(filepath: str = None, merge: bool = False) -> List[Dict]:
    """加载历史数据
    
    Args:
        filepath: 数据文件路径，如果为None则使用系统文件
        merge: 是否将加载的数据合并到系统数据
    """
    try:
        file_to_load = filepath if filepath else SYSTEM_FILE
        if not os.path.exists(file_to_load):
            # 如果文件不存在，返回空列表
            return []
            
        history = []
        with open(file_to_load, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # 检查文件是否为空
            if not reader.fieldnames:
                return []
                
            if not all(field in reader.fieldnames for field in CSV_HEADER):
                raise ValueError(f"文件格式错误: 需要的列名 {CSV_HEADER}")
                
            for row in reader:
                try:
                    numbers = []
                    for i in range(1, 7):
                        num = int(row[f'n{i}'])
                        numbers.append(num)
                        
                    history.append({
                        'date': row['date'],
                        'numbers': numbers,
                        'special': int(row['special_number'])
                    })
                except (ValueError, KeyError) as e:
                    print(f"警告: 跳过无效行: {row}. 原因: {str(e)}")
                    continue
                    
        if merge and filepath and filepath != SYSTEM_FILE:
            # 合并到系统数据
            _save_to_file(history, SYSTEM_FILE)
            
        return history
        
    except Exception as e:
        print(f"警告: 读取文件失败: {str(e)}")
        return []  # 出错时返回空列表而不是抛出异常

def export_history(filepath: str) -> bool:
    """导出历史数据到指定文件"""
    try:
        history = load_history()  # 加载系统数据
        _save_to_file(history, filepath)
        return True
    except Exception as e:
        print(f"导出失败: {str(e)}")
        return False

def initialize_data():
    """初始化所有数据，清空历史记录"""
    try:
        # 确保目录存在
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # 备份现有数据
        if os.path.exists(SYSTEM_FILE):
            backup_name = f"history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            shutil.copy2(SYSTEM_FILE, backup_path)
            
            # 删除现有文件
            os.remove(SYSTEM_FILE)
        
        # 创建新的空文件，只写入表头
        with open(SYSTEM_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
            writer.writeheader()
        
        # 确保文件被正确创建和清空
        if not os.path.exists(SYSTEM_FILE):
            raise IOError("Failed to create new system file")
            
        return True
    except Exception as e:
        print(f"初始化数据失败: {str(e)}")
        return False

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    import os
    if not os.path.exists('data'):
        os.makedirs('data')

    dummy_filepath = 'data/history_example.csv'

    # Test save_history (creating a new file)
    draws_to_save = [
        {'date': '2023-10-01', 'numbers': [1, 2, 3, 4, 5, 6], 'special': 7},
        {'date': '2023-10-08', 'numbers': [8, 9, 10, 11, 12, 13], 'special': 14},
    ]
    
    print(f"\n--- Testing save_history (new file) with: {dummy_filepath} ---")
    save_history(draws_to_save, dummy_filepath)

    # Test load_history
    print(f"\n--- Testing load_history from: {dummy_filepath} ---")
    loaded_data = load_history(dummy_filepath)
    print("Loaded data:")
    for entry in loaded_data:
        print(entry)

    # Clean up test files
    # os.remove(dummy_filepath)
    print("\nTest completed")
