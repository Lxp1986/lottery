import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import pandas as pd

def plot_number_frequencies(regular_freq: Dict[int, int], special_freq: Dict[int, int], 
                          save_path: str = None) -> None:
    """绘制号码频率分布图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 常规号码频率图
    numbers = list(range(1, 50))
    frequencies = [regular_freq.get(n, 0) for n in numbers]
    sns.barplot(x=numbers, y=frequencies, ax=ax1)
    ax1.set_title('常规号码频率分布')
    ax1.set_xlabel('号码')
    ax1.set_ylabel('出现次数')
    
    # 特殊号码频率图
    special_numbers = list(range(1, 50))
    special_frequencies = [special_freq.get(n, 0) for n in special_numbers]
    sns.barplot(x=special_numbers, y=special_frequencies, ax=ax2, color='orange')
    ax2.set_title('特殊号码频率分布')
    ax2.set_xlabel('号码')
    ax2.set_ylabel('出现次数')
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

def plot_trend_analysis(history: List[dict], save_path: str = None) -> None:
    """绘制近期趋势分析图"""
    # 转换数据为DataFrame
    dates = []
    numbers = []
    for draw in history[-10:]:  # 只看最近10期
        date = draw['date']
        for num in draw['numbers']:
            dates.append(date)
            numbers.append(num)
    
    df = pd.DataFrame({'date': dates, 'number': numbers})
    
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=df, x='date', y='number')
    plt.title('近期开奖号码分布趋势')
    plt.xticks(rotation=45)
    
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
