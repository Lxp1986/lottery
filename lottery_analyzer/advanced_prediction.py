import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import random

def calculate_transition_matrix(history_data: List[dict], order: int = 1) -> Dict[tuple, Dict[int, float]]:
    """计算马尔可夫转移概率矩阵"""
    transitions = defaultdict(lambda: defaultdict(int))
    total_counts = defaultdict(int)
    
    for i in range(len(history_data) - order):
        # 获取当前状态和下一个状态
        current_state = tuple(sorted(history_data[i]['numbers']))
        next_numbers = history_data[i + order]['numbers']
        
        # 计算转移次数
        for next_num in next_numbers:
            transitions[current_state][next_num] += 1
            total_counts[current_state] += 1
    
    # 计算概率
    probability_matrix = defaultdict(dict)
    for state in transitions:
        for next_num in transitions[state]:
            probability_matrix[state][next_num] = transitions[state][next_num] / total_counts[state]
            
    return probability_matrix

def markov_chain_prediction(history_data: List[dict], order: int = 1, num_to_predict: int = 6) -> List[int]:
    """基于马尔可夫链的预测"""
    if len(history_data) < order + 1:
        return random.sample(range(1, 50), num_to_predict)
        
    transition_matrix = calculate_transition_matrix(history_data, order)
    
    # 获取最近一期作为当前状态
    current_state = tuple(sorted(history_data[-1]['numbers']))
    
    # 根据转移概率选择下一期号码
    predicted = set()
    if current_state in transition_matrix:
        while len(predicted) < num_to_predict:
            probs = transition_matrix[current_state]
            if not probs:  # 如果没有转移概率数据
                remaining = random.choice([n for n in range(1, 50) if n not in predicted])
            else:
                # 根据概率选择号码
                numbers = list(probs.keys())
                probabilities = list(probs.values())
                chosen = np.random.choice(numbers, p=probabilities)
                if chosen not in predicted:
                    predicted.add(chosen)
    
    # 如果预测数量不足，随机补充
    while len(predicted) < num_to_predict:
        num = random.randint(1, 49)
        if num not in predicted:
            predicted.add(num)
            
    return sorted(list(predicted))

def calculate_conditional_probabilities(history_data: List[dict]) -> Dict[int, float]:
    """计算条件概率"""
    counts = defaultdict(int)
    total_draws = len(history_data)
    
    for draw in history_data:
        for num in draw['numbers']:
            counts[num] += 1
            
    # 计算条件概率
    cond_probs = {}
    for num in range(1, 50):
        # 使用拉普拉斯平滑
        cond_probs[num] = (counts[num] + 1) / (total_draws + 49)
        
    return cond_probs

def bayesian_prediction(history_data: List[dict], num_to_predict: int = 6) -> List[int]:
    """贝叶斯预测"""
    # 计算条件概率
    cond_probs = calculate_conditional_probabilities(history_data)
    
    # 根据概率选择号码
    numbers = list(range(1, 50))
    probabilities = [cond_probs[n] for n in numbers]
    
    # 标准化概率
    probabilities = np.array(probabilities) / sum(probabilities)
    
    # 预测号码
    predicted = set()
    while len(predicted) < num_to_predict:
        chosen = np.random.choice(numbers, p=probabilities)
        if chosen not in predicted:
            predicted.add(chosen)
            
    return sorted(list(predicted))

def time_series_prediction(history_data: List[dict], num_to_predict: int = 6) -> List[int]:
    """时间序列预测"""
    if not history_data:
        return random.sample(range(1, 50), num_to_predict)
        
    # 提取最近的趋势
    recent_draws = history_data[-10:]  # 考虑最近10期
    frequency = defaultdict(int)
    
    # 计算近期频率
    for draw in recent_draws:
        for num in draw['numbers']:
            frequency[num] += 1
            
    # 计算趋势得分
    trend_scores = defaultdict(float)
    for i, draw in enumerate(recent_draws):
        weight = (i + 1) / len(recent_draws)  # 更近的数据权重更大
        for num in draw['numbers']:
            trend_scores[num] += weight
            
    # 结合频率和趋势
    final_scores = {}
    for num in range(1, 50):
        final_scores[num] = frequency[num] * 0.7 + trend_scores[num] * 0.3
        
    # 选择得分最高的号码
    sorted_numbers = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    predicted = [num for num, _ in sorted_numbers[:num_to_predict]]
    
    return sorted(predicted)

def hybrid_prediction(history_data: List[dict], num_to_predict: int = 6) -> List[int]:
    """混合预测模型"""
    # 获取各个模型的预测
    markov_nums = set(markov_chain_prediction(history_data, num_to_predict=num_to_predict))
    bayes_nums = set(bayesian_prediction(history_data, num_to_predict=num_to_predict))
    ts_nums = set(time_series_prediction(history_data, num_to_predict=num_to_predict))
    
    # 找出在多个模型中都出现的号码
    common_nums = markov_nums.intersection(bayes_nums).intersection(ts_nums)
    
    # 选择预测号码
    predicted = set(common_nums)
    candidates = markov_nums.union(bayes_nums).union(ts_nums)
    
    # 如果公共号码不足，从候选号码中随机选择
    while len(predicted) < num_to_predict:
        if candidates:
            num = random.choice(list(candidates))
            predicted.add(num)
            candidates.remove(num)
        else:
            # 如果候选号码用完，随机选择
            num = random.randint(1, 49)
            if num not in predicted:
                predicted.add(num)
                
    return sorted(list(predicted))
