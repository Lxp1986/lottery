from typing import Dict, List, Set, Tuple
import random
import collections
import numpy as np
from scipy.linalg import solve
from .tagging import get_tags_for_number # Assuming tagging.py is in the same package
from . import advanced_prediction
from . import analysis
from . import tagging

# Constants for prediction logic
MIN_NUMBER = 1
MAX_NUMBER = 49
DEFAULT_NUM_TO_PREDICT = 6

# Weighting factors for scoring (these can be tuned)
WEIGHT_FREQUENCY = 1.0
WEIGHT_RECENCY_HOT = 1.5
# WEIGHT_RECENCY_COLD = 0.5 # Optional: for numbers that haven't appeared in a while

# Configuration for tag prediction
TAG_PREDICTION_CONFIG = {
    "尾数特征": {"prefix": None, "suffix": "尾", "count": 3, "source": "tail"}, # Or identify by suffix
    "生肖": {"prefix": "生肖-", "count": 3, "source": "zodiac"},
    "五行": {"prefix": "五行-", "count": 2, "source": "elements"},
    "波色": {"prefix": None, "keywords": ["红波", "蓝波", "绿波"], "count": 2, "source": "color"} #波色 tags don't have a common prefix other than the word itself
}

def _get_recent_numbers(history_data: list[dict], count: int, number_type: str = 'regular') -> collections.Counter:
    """
    Helper function to get numbers that appeared in recent draws.

    Args:
        history_data: List of draw dictionaries.
        count: Number of recent draws to consider.
        number_type: 'regular' or 'special'.

    Returns:
        A Counter object with recent numbers and their counts in the recent period.
    """
    recent_numbers_list = []
    if not history_data or count <= 0:
        return collections.Counter()

    for draw in history_data[-count:]: # Get the last 'count' draws
        if number_type == 'regular':
            if 'numbers' in draw and isinstance(draw['numbers'], list):
                recent_numbers_list.extend(draw['numbers'])
        elif number_type == 'special':
            if 'special' in draw and isinstance(draw['special'], int):
                recent_numbers_list.append(draw['special'])
    return collections.Counter(recent_numbers_list)

def predict_numbers_basic(
    history_data: list[dict],
    regular_freq: dict[int, int],
    special_freq: dict[int, int],
    num_to_predict: int = DEFAULT_NUM_TO_PREDICT,
    recent_draws_count: int = 10,
    freq_weight: float = 0.2,      # 降低频率权重
    recent_weight: float = 0.7,    # 提高近期权重
    gap_weight: float = 0.1,       # 间隔权重
    **kwargs
) -> dict:
    """基础预测模型
    
    Args:
        history_data: 历史开奖数据
        regular_freq: 正码出现频率字典
        special_freq: 特码出现频率字典
        num_to_predict: 需要预测的正码数量
        recent_draws_count: 参考最近期数
        **kwargs: 额外参数(用于统一接口)
    """
    if not history_data or not regular_freq or not special_freq:
        print("警告: 历史数据或频率数据为空，将使用随机预测")
        # 随机预测兜底
        regular_numbers = sorted(random.sample(range(MIN_NUMBER, MAX_NUMBER + 1), num_to_predict))
        special_number = random.randint(MIN_NUMBER, MAX_NUMBER)
        while special_number in regular_numbers:
            special_number = random.randint(MIN_NUMBER, MAX_NUMBER)
        return {'regular': regular_numbers, 'special': special_number}

    # 修改分数计算方式
    regular_scores = collections.defaultdict(float)
    special_scores = collections.defaultdict(float)

    # 1. 频率权重
    total_regular_draws = sum(regular_freq.values())
    if total_regular_draws > 0:
        for num, freq in regular_freq.items():
            if MIN_NUMBER <= num <= MAX_NUMBER:
                normalized_freq = freq / total_regular_draws
                regular_scores[num] += normalized_freq * freq_weight

    # 2. 近期热门权重
    recent_regular_numbers = _get_recent_numbers(history_data, recent_draws_count, 'regular')
    for num, recency_count in recent_regular_numbers.items():
        if MIN_NUMBER <= num <= MAX_NUMBER:
            regular_scores[num] += (recency_count / max(1, recent_draws_count)) * recent_weight

    # 3. 间隔权重
    latest_appearances = {num: -1 for num in range(MIN_NUMBER, MAX_NUMBER + 1)}
    for i, draw in enumerate(history_data):
        for num in draw['numbers']:
            latest_appearances[num] = i
    
    current_index = len(history_data)
    for num in range(MIN_NUMBER, MAX_NUMBER + 1):
        if latest_appearances[num] != -1:
            gap = current_index - latest_appearances[num]
            gap_score = 1.0 / (gap + 1)  # 间隔越大，分数越小
            regular_scores[num] += gap_score * gap_weight

    # --- Score Special Numbers ---
    # 1. Frequency Weight
    total_special_draws = sum(special_freq.values()) # Could also be len(history_data)
    if total_special_draws > 0:
        for num, freq in special_freq.items():
             if MIN_NUMBER <= num <= MAX_NUMBER:
                normalized_freq = freq / total_special_draws
                special_scores[num] += normalized_freq * WEIGHT_FREQUENCY

    # 2. Recency Weight (Hot Numbers)
    recent_special_numbers = _get_recent_numbers(history_data, recent_draws_count, 'special')
    for num, recency_count in recent_special_numbers.items():
        if MIN_NUMBER <= num <= MAX_NUMBER:
            special_scores[num] += (recency_count / recent_draws_count) * WEIGHT_RECENCY_HOT

    # --- Prediction ---
    # Select top N regular numbers. Counter.most_common sorts by score, then by key (number) if scores are equal.
    # To ensure we get num_to_predict distinct numbers, especially if scores are low or many are 0.
    predicted_regular_numbers = []
    # Add all numbers from 1-49 to scores if not present, to ensure they can be picked if scores are sparse
    for i in range(MIN_NUMBER, MAX_NUMBER + 1):
        if i not in regular_scores:
            regular_scores[i] = 0.0
        if i not in special_scores:
            special_scores[i] = 0.0

    # Sort by score (desc) then number (asc for tie-breaking)
    # Using Counter.most_common might be cleaner if we ensure all numbers 1-49 are in the scores dict.
    # Let's use a list of tuples and sort it.
    sorted_regular_candidates = sorted(regular_scores.items(), key=lambda item: (item[1], -item[0]), reverse=True) # Score desc, num asc

    # We need to ensure we don't pick the same number multiple times if it's somehow duplicated in scoring (shouldn't happen with dict keys)
    # And that we pick num_to_predict numbers
    predicted_regular_numbers = [num for num, score in sorted_regular_candidates[:num_to_predict]]


    # Predict special number (top 1)
    special_counter = collections.Counter(special_scores)
    top_special = special_counter.most_common(1)
    predicted_special_number = top_special[0][0] if top_special else None
    # Fallback if no special number could be predicted (e.g., empty history)
    if predicted_special_number is None and len(special_scores) > 0:
        predicted_special_number = list(special_scores.keys())[0]
    elif predicted_special_number is None:
        predicted_special_number = random.randint(MIN_NUMBER, MAX_NUMBER)

    # --- 避免连续两期特别号码重复 ---
    if history_data and isinstance(history_data[-1], dict):
        last_special = history_data[-1].get('special')
        if last_special == predicted_special_number:
            # 排除上期特别号，选下一个分数最高的
            sorted_special_candidates = sorted(
                ((num, score) for num, score in special_scores.items() if num != last_special),
                key=lambda item: (item[1], -item[0]), reverse=True
            )
            if sorted_special_candidates:
                predicted_special_number = sorted_special_candidates[0][0]
            # 若所有分数都一样或只有一个可选，允许重复

    # Ensure the predicted regular numbers do not include the predicted special number.
    # If so, replace the conflicting regular number with the next best candidate.
    # This is a common lottery rule.
    if predicted_special_number in predicted_regular_numbers:
        print(f"Info: Predicted special number {predicted_special_number} was in regular numbers. Replacing.")
        # Remove it and find a new candidate
        predicted_regular_numbers = [n for n in predicted_regular_numbers if n != predicted_special_number]

        next_best_candidate_found = False
        for num, score in sorted_regular_candidates:
            if num not in predicted_regular_numbers and num != predicted_special_number:
                predicted_regular_numbers.append(num)
                next_best_candidate_found = True
                break

        if not next_best_candidate_found:
            # If we still don't have enough numbers (very unlikely), fill with random unpicked numbers
            # This is a fallback, should ideally not be hit with proper scoring of all 1-49 numbers.
            print("Warning: Could not find enough unique regular numbers after special number conflict resolution. Filling randomly.")
            current_selection = set(predicted_regular_numbers)
            current_selection.add(predicted_special_number)
            while len(predicted_regular_numbers) < num_to_predict:
                rand_num = random.randint(MIN_NUMBER, MAX_NUMBER)
                if rand_num not in current_selection:
                    predicted_regular_numbers.append(rand_num)
                    current_selection.add(rand_num)

    # Ensure correct number of predictions, sorted
    predicted_regular_numbers = sorted(predicted_regular_numbers[:num_to_predict])


    return {'regular': predicted_regular_numbers, 'special': predicted_special_number}


def predict_numbers_with_tags(
    history_data: list[dict],
    regular_freq: dict[int, int],
    special_freq: dict[int, int],
    number_tags: dict[int, set[str]], # Assuming this is the global dict from tagging.py
    num_to_predict: int = DEFAULT_NUM_TO_PREDICT,
    recent_draws_count: int = 10,
    tag_trend_draws: int = 5,          # 默认窗口缩小为5
    weight_tag_trend: float = 1.0,     # 标签趋势权重提高
    freq_weight: float = 0.2,          # 频率权重降低
    recent_weight: float = 0.7,        # 近期权重提高
) -> dict:
    """
    Predicts lottery numbers using basic scoring plus tag trend analysis.

    Args:
        history_data: List of draw dictionaries.
        regular_freq: Dictionary of regular number frequencies.
        special_freq: Dictionary of special number frequencies.
        number_tags: Dictionary mapping numbers to sets of tags.
        num_to_predict: How many regular numbers to predict.
        recent_draws_count: For hot number analysis in basic scoring.
        tag_trend_draws: How many recent draws to analyze for tag trends.
        weight_tag_trend: Weight factor for the influence of tag trends.

    Returns:
        A dictionary: {'regular': [predicted_regular_numbers], 'special': predicted_special_number}.
    """
    # 1. Get initial scores from the basic predictor
    # We can call predict_numbers_basic and then adjust scores, or re-implement scoring logic here
    # For clarity and to avoid issues with return format, let's re-implement and extend.

    regular_scores = collections.defaultdict(float)
    special_scores = collections.defaultdict(float)

    # --- Basic Scoring (Frequency and Recency) ---
    # (This section is similar to predict_numbers_basic)
    total_regular_draws = sum(regular_freq.values())
    if total_regular_draws > 0:
        for num, freq in regular_freq.items():
            if MIN_NUMBER <= num <= MAX_NUMBER:
                regular_scores[num] += (freq / total_regular_draws) * freq_weight

    recent_regular_numbers = _get_recent_numbers(history_data, recent_draws_count, 'regular')
    for num, recency_count in recent_regular_numbers.items():
        if MIN_NUMBER <= num <= MAX_NUMBER:
            regular_scores[num] += (recency_count / max(1, recent_draws_count)) * recent_weight

    total_special_draws = sum(special_freq.values())
    if total_special_draws > 0:
        for num, freq in special_freq.items():
            if MIN_NUMBER <= num <= MAX_NUMBER:
                special_scores[num] += (freq / total_special_draws) * WEIGHT_FREQUENCY

    recent_special_numbers = _get_recent_numbers(history_data, recent_draws_count, 'special')
    for num, recency_count in recent_special_numbers.items():
        if MIN_NUMBER <= num <= MAX_NUMBER:
            special_scores[num] += (recency_count / recent_draws_count) * WEIGHT_RECENCY_HOT

    # --- Tag Trend Analysis ---
    recent_tag_trends_regular = collections.Counter()
    recent_tag_trends_special = collections.Counter()

    if tag_trend_draws > 0 and history_data:
        for draw in history_data[-tag_trend_draws:]:
            # Regular numbers' tags
            if 'numbers' in draw and isinstance(draw['numbers'], list):
                for num in draw['numbers']:
                    if MIN_NUMBER <= num <= MAX_NUMBER:
                        # Use the get_tags_for_number function from the tagging module
                        tags = get_tags_for_number(num) # This uses the globally loaded number_tags
                        for tag in tags:
                            recent_tag_trends_regular[tag] += 1

            # Special number's tags
            if 'special' in draw and isinstance(draw['special'], int):
                num = draw['special']
                if MIN_NUMBER <= num <= MAX_NUMBER:
                    tags = get_tags_for_number(num)
                    for tag in tags:
                        recent_tag_trends_special[tag] += 1

    # --- Apply Tag Trend Scores ---
    # Normalize tag trend frequencies (e.g., by total tags counted in the trend period)
    total_tags_counted_regular = sum(recent_tag_trends_regular.values())
    total_tags_counted_special = sum(recent_tag_trends_special.values())

    for num in range(MIN_NUMBER, MAX_NUMBER + 1):
        num_actual_tags = get_tags_for_number(num) # Get tags for the current number being scored

        # Regular score adjustment
        if total_tags_counted_regular > 0:
            for tag in num_actual_tags:
                if tag in recent_tag_trends_regular:
                    normalized_tag_trend_freq = recent_tag_trends_regular[tag] / total_tags_counted_regular
                    regular_scores[num] += normalized_tag_trend_freq * weight_tag_trend

        # Special score adjustment
        if total_tags_counted_special > 0:
            for tag in num_actual_tags:
                if tag in recent_tag_trends_special:
                    normalized_tag_trend_freq = recent_tag_trends_special[tag] / total_tags_counted_special
                    special_scores[num] += normalized_tag_trend_freq * weight_tag_trend

    # --- Prediction (similar to basic, but with enhanced scores) ---
    # Ensure all numbers 1-49 are in scores for complete candidate list
    for i in range(MIN_NUMBER, MAX_NUMBER + 1):
        if i not in regular_scores: regular_scores[i] = 0.0
        if i not in special_scores: special_scores[i] = 0.0

    sorted_regular_candidates = sorted(regular_scores.items(), key=lambda item: (item[1], -item[0]), reverse=True)
    predicted_regular_numbers = [num for num, score in sorted_regular_candidates[:num_to_predict]]

    special_counter = collections.Counter(special_scores)
    top_special = special_counter.most_common(1)
    predicted_special_number = top_special[0][0] if top_special else random.randint(MIN_NUMBER, MAX_NUMBER)

    # --- 避免连续两期特别号码重复 ---
    if history_data and isinstance(history_data[-1], dict):
        last_special = history_data[-1].get('special')
        if last_special == predicted_special_number:
            sorted_special_candidates = sorted(
                ((num, score) for num, score in special_scores.items() if num != last_special),
                key=lambda item: (item[1], -item[0]), reverse=True
            )
            if sorted_special_candidates:
                predicted_special_number = sorted_special_candidates[0][0]

    # Conflict resolution: ensure special is not in regular
    if predicted_special_number in predicted_regular_numbers:
        print(f"Info (Tag Prediction): Predicted special number {predicted_special_number} was in regular numbers. Replacing.")
        predicted_regular_numbers = [n for n in predicted_regular_numbers if n != predicted_special_number]
        for num, score in sorted_regular_candidates:
            if num not in predicted_regular_numbers and num != predicted_special_number:
                predicted_regular_numbers.append(num)
                break
        # Fallback if still not enough (very unlikely)
        current_selection = set(predicted_regular_numbers)
        current_selection.add(predicted_special_number)
        while len(predicted_regular_numbers) < num_to_predict:
            rand_num = random.randint(MIN_NUMBER, MAX_NUMBER)
            if rand_num not in current_selection:
                predicted_regular_numbers.append(rand_num)
                current_selection.add(rand_num)


    predicted_regular_numbers = sorted(predicted_regular_numbers[:num_to_predict])

    return {'regular': predicted_regular_numbers, 'special': predicted_special_number}


def predict_tags(history_data: list[dict], recent_draws_count: int | None = None) -> dict:
    """
    Predicts trending tags for various categories based on **special numbers**
    from historical lottery data.

    The function analyzes the frequency and recency of tags associated with
    the special number in each draw within the specified history window.

    Args:
        history_data: List of draw dictionaries, where each draw should ideally
                      contain a 'special' key with the special number.
        recent_draws_count: Optional. The number of most recent draws to analyze.
                            If None or 0 or invalid, the full history_data is used.
                            The analysis focuses on special numbers within these draws.

    Returns:
        A dictionary where keys are tag category names (e.g., "单双", "生肖")
        and values are lists of predicted tag strings for that category.
        Example: {'单双': ['单'], '大小': ['小'], ...}
    """
    if recent_draws_count is not None and recent_draws_count > 0:
        start_index = max(0, len(history_data) - recent_draws_count)
        effective_history = history_data[start_index:]
    else:
        effective_history = history_data

    predicted_tags_output = {category_key: [] for category_key in TAG_PREDICTION_CONFIG.keys()}

    if not effective_history:
        # For empty effective_history (either original or after slicing),
        # return the initialized empty lists for each category.
        return predicted_tags_output

    tag_scores: dict[str, collections.defaultdict[str, float]] = {
        cat_key: collections.defaultdict(float) for cat_key in TAG_PREDICTION_CONFIG.keys()
    }

    tag_getter_mapping = {
        "单双": tagging.get_dx_tag,
        "大小": tagging.get_ds_tag,
        "合数特征": tagging.get_sum_feature_tag,
        "尾数特征": tagging.get_tail_feature_tag,
        "生肖": tagging.get_zodiac_tag,
        "五行": tagging.get_element_tag,
        "波色": tagging.get_color_tag,
    }

    # This constant defines the window for 'hot' tags *within* the effective_history
    recent_draws_for_hot_score_window = 10  # Defines how many of the *latest* draws in effective_history are considered "hot"

    for idx, draw_data_item in enumerate(effective_history):
        if not isinstance(draw_data_item, dict):
            continue

        special_num = draw_data_item.get('special')

        # Determine if this draw is "recent" for the purpose of applying WEIGHT_RECENCY_HOT.
        # This is based on its position within the (potentially sliced) effective_history.
        is_recent_for_hot_score = (len(effective_history) - 1 - idx) < recent_draws_for_hot_score_window

        if special_num is not None and isinstance(special_num, int) and \
           tagging.MIN_NUMBER <= special_num <= tagging.MAX_NUMBER:

            # Process only the special number for its tags
            num_to_process = special_num

            for category_key, config_details_loop in TAG_PREDICTION_CONFIG.items():
                getter_func = tag_getter_mapping.get(category_key)
                if not getter_func:
                    continue

                tag_value = getter_func(num_to_process)
                if tag_value is not None:
                    tag_scores[category_key][tag_value] += WEIGHT_FREQUENCY
                    if is_recent_for_hot_score:
                        tag_scores[category_key][tag_value] += WEIGHT_RECENCY_HOT
        # If special_num is not valid or not present, this draw contributes nothing to tag scores.

    for category_key, config_details in TAG_PREDICTION_CONFIG.items():
        num_to_predict_for_category = config_details['count']
        current_category_scores = tag_scores.get(category_key, collections.defaultdict(float))

        # Sort tags by score, then alphabetically for tie-breaking
        sorted_tags_by_score = sorted(current_category_scores.items(), key=lambda item: (item[1], item[0]), reverse=True)

        predictions_for_category = []
        for tag_data_tuple in sorted_tags_by_score[:num_to_predict_for_category]:
            tag_name = tag_data_tuple[0]

            prefix_to_strip = config_details.get('prefix')
            if prefix_to_strip and tag_name.startswith(prefix_to_strip):
                formatted_tag_name = tag_name[len(prefix_to_strip):]
            else:
                # Handle potential suffix stripping for "尾数特征" if needed, though not explicitly asked.
                # For now, direct tag name is fine as per getter functions.
                formatted_tag_name = tag_name

            predictions_for_category.append(formatted_tag_name)

        predicted_tags_output[category_key] = predictions_for_category

    return predicted_tags_output


def predict_using_grey_model(history_data: list[dict], num_to_predict: int = 6) -> dict:
    """使用灰色预测模型(GM(1,1))进行预测
    
    灰色模型原理：
    1. 对原始数据进行累加生成(AGO)以减少随机性
    2. 建立微分方程模型
    3. 求解微分方程得到预测值
    4. 通过累减还原预测数据
    """
    def gm11_predict(sequence: list[float], predict_length: int = 1) -> list[float]:
        """改进的GM(1,1)预测"""
        n = len(sequence)
        X0 = np.array(sequence)
        X1 = np.cumsum(X0)
        
        Z1 = (X1[:-1] + X1[1:]) / 2.0
        Z1 = Z1.reshape((n-1, 1))
        B = np.vstack([-Z1, np.ones((n-1, 1))])
        B = B.T
        Y = X0[1:].reshape((n-1, 1))
        
        try:
            [[a], [b]] = np.linalg.solve(B.T.dot(B), B.T.dot(Y))
            
            predictions = []
            for k in range(predict_length):
                next_val = (X0[0] - b/a) * np.exp(-a * (n+k)) + b/a
                predictions.append(next_val - (0 if k == 0 else predictions[-1]))
            return predictions
        except:
            return [sequence[-1]] * predict_length  # 如果计算失败，返回最后一个值
    
    # 使用最近20期数据构建预测序列
    recent_history = history_data[-20:]
    number_sequences = {i: [] for i in range(1, 50)}
    
    # 为每个号码构建出现频率序列
    for draw in recent_history:
        numbers_set = set(draw['numbers'])
        for num in range(1, 50):
            number_sequences[num].append(1 if num in numbers_set else 0)
    
    # 预测每个号码的出现概率
    probabilities = {}
    for num in range(1, 50):
        if not any(number_sequences[num]):  # 如果号码从未出现
            probabilities[num] = 0.1  # 给予小概率
        else:
            # 使用最近5期数据进行预测
            seq = number_sequences[num][-5:]
            pred = gm11_predict(seq)[0]
            probabilities[num] = max(0.1, min(1.0, pred))  # 限制概率范围
    
    # 根据预测概率选择号码
    numbers = list(range(1, 50))
    weights = [probabilities[n] for n in numbers]
    
    # 正规化权重
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w/total_weight for w in weights]
    
    # 选择号码
    regular_numbers = []
    while len(regular_numbers) < num_to_predict:
        chosen = np.random.choice(numbers, p=weights)
        if chosen not in regular_numbers:
            regular_numbers.append(chosen)
    
    # 特别号码使用不同的权重计算
    special_weights = [1-w for w in weights]
    total_special_weight = sum(special_weights)
    if total_special_weight > 0:
        special_weights = [w/total_special_weight for w in special_weights]
    
    special_number = np.random.choice(numbers, p=special_weights)
    while special_number in regular_numbers:
        special_number = np.random.choice(numbers, p=special_weights)
    
    return {
        'regular': sorted(regular_numbers),
        'special': special_number
    }


def predict_numbers_advanced(
    history_data: list[dict],
    method: str = "hybrid",
    num_to_predict: int = 6
) -> dict:
    """
    使用高级预测模型进行预测
    
    Args:
        history_data: 历史数据
        method: 预测方法 ("markov", "bayes", "timeseries", "hybrid", "grey")
        num_to_predict: 预测号码数量
    """
    prediction_funcs = {
        "markov": advanced_prediction.markov_chain_prediction,
        "bayes": advanced_prediction.bayesian_prediction,
        "timeseries": advanced_prediction.time_series_prediction,
        "hybrid": advanced_prediction.hybrid_prediction
    }
    
    if method == "grey":
        return predict_using_grey_model(history_data, num_to_predict)
    
    if method not in prediction_funcs:
        raise ValueError(f"Unknown prediction method: {method}")
        
    # 预测正码
    regular_numbers = prediction_funcs[method](history_data, num_to_predict)
    
    # 预测特码 (使用混合模型)
    special_number = prediction_funcs["hybrid"](history_data, 1)[0]
    # --- 避免连续两期特别号码重复 ---
    if history_data and isinstance(history_data[-1], dict):
        last_special = history_data[-1].get('special')
        if last_special == special_number:
            # 重新选一个不等于上期的
            alt_special = None
            alt_candidates = [n for n in range(1, 50) if n != last_special and n not in regular_numbers]
            if alt_candidates:
                alt_special = random.choice(alt_candidates)
            if alt_special:
                special_number = alt_special
    while special_number in regular_numbers:
        special_number = prediction_funcs["hybrid"](history_data, 1)[0]

    return {
        'regular': regular_numbers,
        'special': special_number
    }


def predict_all_methods(history_data: List[Dict], 
                       num_to_predict: int = 6,
                       recent_draws_count: int = 10,
                       tag_trend_draws: int = 20) -> Dict:
    """综合所有预测方法的结果"""
    predictions = []
    
    # 计算频率
    reg_freq, spec_freq = analysis.calculate_frequencies(history_data)
    
    # 1. 基础预测
    basic_pred = predict_numbers_basic(
        history_data, 
        reg_freq, 
        spec_freq,
        num_to_predict=num_to_predict,
        recent_draws_count=recent_draws_count
    )
    
    # 2. 标签预测
    tag_pred = predict_numbers_with_tags(
        history_data,
        reg_freq,
        spec_freq,
        tagging.number_tags,
        num_to_predict=num_to_predict,
        recent_draws_count=recent_draws_count,
        tag_trend_draws=tag_trend_draws
    )
    
    # 3. 马尔可夫预测
    markov_pred = predict_numbers_advanced(
        history_data, 
        method="markov",
        num_to_predict=num_to_predict
    )
    
    # 4. 贝叶斯预测
    bayes_pred = predict_numbers_advanced(
        history_data, 
        method="bayes", 
        num_to_predict=num_to_predict
    )
    
    # 5. 时间序列预测
    time_pred = predict_numbers_advanced(
        history_data, 
        method="timeseries", 
        num_to_predict=num_to_predict
    )
    
    # 6. 灰度预测
    grey_pred = predict_using_grey_model(
        history_data, 
        num_to_predict=num_to_predict
    )

    # 7. 标签预测 (by category)
    # Pass the recent_draws_count from predict_all_methods to predict_tags
    label_predictions = predict_tags(history_data, recent_draws_count=recent_draws_count)
    
    # 返回综合结果
    return {
        'regular': sorted(basic_pred['regular']),  # 使用基础预测作为主要结果
        'special': basic_pred['special'],
        'method_results': {
            'basic': basic_pred,
            'tags': tag_pred, # This is for number prediction using tags
            'markov': markov_pred,
            'bayes': bayes_pred,
            'timeseries': time_pred,
            'grey': grey_pred
        },
        'label_predictions': label_predictions # New: predictions for each tag category
    }


if __name__ == '__main__':
    print("--- Testing prediction functions ---")

    # Mock history data (simplified)
    # In a real scenario, this would come from data_input.load_history
    sample_history = [
        {'date': 'd1', 'numbers': [1, 2, 3, 10, 11, 12], 'special': 5},
        {'date': 'd2', 'numbers': [1, 2, 4, 13, 14, 15], 'special': 6},
        {'date': 'd3', 'numbers': [1, 3, 4, 16, 17, 18], 'special': 5},
        {'date': 'd4', 'numbers': [2, 3, 4, 19, 20, 21], 'special': 7}, # Recent for hot
        {'date': 'd5', 'numbers': [10, 11, 12, 22, 23, 24], 'special': 8},# Recent for hot
    ] * 4 # Multiply to make history longer for frequency and trends

    # Mock frequency data
    mock_reg_freq = collections.defaultdict(int)
    mock_spec_freq = collections.defaultdict(int)
    for draw in sample_history:
        for num in draw['numbers']: mock_reg_freq[num] +=1
        mock_spec_freq[draw['special']] +=1

    # Add more frequency to specific numbers
    mock_reg_freq[1] += 10
    mock_reg_freq[25] += 8
    mock_spec_freq[5] += 5

    # Test basic prediction
    print("\n1. Testing predict_numbers_basic:")
    basic_prediction = predict_numbers_basic(sample_history, mock_reg_freq, mock_spec_freq, recent_draws_count=2)
    print(f"Basic prediction: {basic_prediction}")
    
    basic_prediction_7 = predict_numbers_basic(sample_history, mock_reg_freq, mock_spec_freq, num_to_predict=7, recent_draws_count=2)
    print(f"Basic prediction (7 numbers): {basic_prediction_7}")

    # Test tag prediction
    print("\n2. Testing predict_numbers_with_tags:")
    from .tagging import add_custom_tag, number_tags
    add_custom_tag(10, "Decade1")
    add_custom_tag(20, "Decade2")

    print(f"Tags for 10: {get_tags_for_number(10)}")
    print(f"Tags for 20: {get_tags_for_number(20)}")

    tag_prediction = predict_numbers_with_tags(
        sample_history,
        mock_reg_freq,
        mock_spec_freq,
        number_tags,
        recent_draws_count=2,
        tag_trend_draws=3
    )
    print(f"Tag-based prediction: {tag_prediction}")

    tag_prediction_7 = predict_numbers_with_tags(
        sample_history,
        mock_reg_freq,
        mock_spec_freq,
        number_tags,
        num_to_predict=7,
        recent_draws_count=2,
        tag_trend_draws=3
    )
    print(f"Tag-based prediction (7 numbers): {tag_prediction_7}")

    # Test with empty history
    print("\n3. Testing with empty history data:")
    empty_freq = collections.defaultdict(int)
    basic_empty = predict_numbers_basic([], empty_freq, empty_freq)
    print(f"Basic prediction (empty history): {basic_empty}")
    tag_empty = predict_numbers_with_tags([], empty_freq, empty_freq, number_tags)
    print(f"Tag-based prediction (empty history): {tag_empty}")

    print("\n--- End of prediction function tests ---")