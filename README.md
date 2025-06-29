# 六合彩分析预测系统（Lottery Analysis and Prediction Tool）

## 项目简介

本项目是基于 Python 的六合彩数据分析与预测工具，支持历史数据管理、频率分析、标签系统、号码预测、自动API同步、可视化等功能。支持 6+1 格式（6个正码+1个特别号），号码范围 1-49。

---

## 主要功能

- **自动API同步**：每次启动自动从API获取最新开奖记录并更新本地数据。
- **历史数据管理**：支持CSV导入导出，自动备份。
- **频率分析**：统计正码/特别号出现频率，冷热分析。
- **标签系统**：自动标签（奇偶/大小），支持自定义标签。
- **数据预测**：
  - 基础预测（频率+近期热门）
  - 标签预测（结合标签趋势）
  - 马尔可夫预测
  - 贝叶斯预测
  - 时间序列预测
  - 灰度预测
  - 综合预测（多模型融合）
- **标签趋势期数**：最大支持1000期分析。
- **可视化**：自动生成频率分布图、趋势图。
- **图形界面（GUI）与命令行（CLI）**：均支持。

---

## 项目结构

- `lottery_analyzer/`
  - `data_input.py`：数据加载与保存
  - `tagging.py`：标签系统
  - `analysis.py`：频率与统计分析
  - `prediction.py`：预测算法
  - `advanced_prediction.py`：高级预测（马尔可夫、贝叶斯等）
  - `visualization.py`：可视化
  - `gui.py`：图形界面主程序
  - `main.py`：命令行入口
- `data/`：历史数据与分析结果
- `requirements.txt`：依赖库

---

## 数据文件格式（data/history.csv）

- **表头**：`date,n1,n2,n3,n4,n5,n6,special_number`
- **date** 字段支持“期号”（如2025001）或“日期”（如2023-01-01）
- **n1-n6**：6个正码，1-49且唯一
- **special_number**：特别号，1-49且不与正码重复

示例：

```csv
date,n1,n2,n3,n4,n5,n6,special_number
2025001,5,12,23,34,40,45,7
```

---

## 安装与运行

1. **环境要求**：Python 3.9+，PyQt6，pandas，numpy，matplotlib，seaborn
2. **安装依赖**：

   ```bash
   pip install -r requirements.txt
   ```

3. **启动GUI**：

   ```bash
   python -m lottery_analyzer.main --gui
   ```
   - 启动后会自动从API同步最新数据

4. **命令行用法**：

   ```bash
   python -m lottery_analyzer.main <命令> [参数]
   ```
   - 具体命令见 `python -m lottery_analyzer.main -h`

---

## 其他说明

- **自定义标签**：当前仅内存保存，重启后会丢失。
- **数据目录**：首次运行自动创建 `data/` 目录。
- **可视化结果**：保存在 `data/analysis_plots/` 目录。

---

## 未来规划

- 持久化自定义标签
- 更多高级预测模型
- 多种彩票格式支持
- Web界面

---

如需英文文档或详细开发接口说明，请联系维护者。
