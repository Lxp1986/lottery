from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QTabWidget, QCalendarWidget, QMessageBox, QSpinBox,
    QComboBox, QTableWidget, QTableWidgetItem, QGroupBox,
    QStatusBar, QHeaderView, QGridLayout, QMenu, QInputDialog,
    QFileDialog
)
from PyQt6.QtCore import Qt
import sys
import os
import requests # Added for API calls
from datetime import datetime, timedelta

from lottery_analyzer import data_input
from lottery_analyzer import analysis
from lottery_analyzer import prediction
from lottery_analyzer import tagging
from lottery_analyzer import visualization

class LotteryAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("六合彩分析系统")
        self.setMinimumSize(1024, 768)
        
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.create_menu_bar()
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        try:
            self.init_input_tab()
            self.init_analysis_tab()
            self.init_prediction_tab()
            self.init_tags_tab()
            self.init_label_prediction_tab() # New tab initialization
            self.load_system_data()
        except Exception as e:
            QMessageBox.critical(self, "初始化错误", f"系统初始化失败: {str(e)}")
            raise

    def format_number(self, num: int) -> str:
        """格式化号码，个位数前面添加0"""
        return f"{num:02d}"

    def update_history_table(self):
        """更新历史记录表格"""
        try:
            history = data_input.load_history()
            if not history:
                return
            
            self.history_table.setRowCount(0)
            history.sort(key=lambda x: x['date'], reverse=True)
            
            for draw in history:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                self.history_table.setItem(row, 0, QTableWidgetItem(draw['date']))
                
                for i, num in enumerate(draw['numbers'], 1):
                    self.history_table.setItem(row, i, QTableWidgetItem(self.format_number(num)))
                
                self.history_table.setItem(row, 7, QTableWidgetItem(self.format_number(draw['special'])))
            
            self.statusBar.showMessage("历史记录已更新")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"更新历史记录失败: {str(e)}")

    def create_menu_bar(self):
        """创建菜单栏"""
        try:
            menubar = self.menuBar()
            file_menu = menubar.addMenu("文件")
            
            # 在第一个位置添加初始化选项
            new_action = file_menu.addAction("新建")
            new_action.triggered.connect(self.handle_new)
            new_action.setShortcut("Ctrl+N")
            
            open_action = file_menu.addAction("打开历史数据")
            open_action.triggered.connect(self.handle_open_history)
            open_action.setShortcut("Ctrl+O")
            
            save_as_action = file_menu.addAction("历史数据另存为")
            save_as_action.triggered.connect(self.handle_save_history_as)
            save_as_action.setShortcut("Ctrl+S")
            
            file_menu.addSeparator()
            
            import_tags_action = file_menu.addAction("导入标签数据")
            import_tags_action.triggered.connect(self.handle_import_tags)
            
            export_tags_action = file_menu.addAction("导出标签数据")
            export_tags_action.triggered.connect(self.handle_export_tags)
            
            file_menu.addSeparator()
            
            exit_action = file_menu.addAction("退出")
            exit_action.triggered.connect(self.close)
            exit_action.setShortcut("Ctrl+Q")
        except Exception as e:
            QMessageBox.critical(self, "菜单创建错误", f"创建菜单失败: {str(e)}")
            raise

    def handle_new(self):
        """初始化数据"""
        reply = QMessageBox.question(
            self, 
            "确认初始化", 
            "这将清空所有历史数据！是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if data_input.initialize_data():
                    # 清空表格显示
                    self.history_table.setRowCount(0)
                    # 重新加载空表格
                    self.update_history_table()
                    self.statusBar.showMessage("数据已初始化，备份文件保存在data/backup目录")
                    # 清空输入框
                    if hasattr(self, 'draw_id_input'):
                        self.draw_id_input.clear()
                    if hasattr(self, 'numbers_input'):
                        self.numbers_input.clear()
                    if hasattr(self, 'special_input'):
                        self.special_input.clear()
                else:
                    QMessageBox.warning(self, "错误", "初始化失败，请检查日志")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"初始化过程出错: {str(e)}")

    def handle_open_history(self):
        """打开历史数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开历史数据",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        if file_path:
            try:
                data_input.load_history(file_path, merge=True)  # 合并到系统数据
                self.update_history_table()
                self.statusBar.showMessage(f"已导入: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")

    def handle_save_history_as(self):
        """历史数据另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "历史数据另存为",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        if file_path:
            try:
                data_input.export_history(file_path)
                self.statusBar.showMessage(f"已保存到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")

    def handle_import_tags(self):
        """导入标签数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入标签数据",
            "",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                if tagging.import_tags(file_path):
                    self.statusBar.showMessage(f"已导入标签数据: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")

    def handle_export_tags(self):
        """导出标签数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出标签数据",
            "",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                if tagging.export_tags(file_path):
                    self.statusBar.showMessage(f"已导出标签数据: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")

    def handle_prediction(self):
        """处理预测请求"""
        try:
            # 清空表格
            self.results_table.setRowCount(0)
            num_groups = self.num_predictions.value()
            
            history = data_input.load_history()
            if not history:
                QMessageBox.warning(self, "警告", "没有历史数据，预测将基于随机或有限数据")
            
            # 获取实际可用的历史数据长度
            max_history = len(history)
            recent_draws = min(self.recent_draws.value(), max_history)
            tag_trend_draws = min(self.tag_trend_draws.value(), max_history)
            
            # 如果请求的期数超过实际数据，显示提示
            if self.recent_draws.value() > max_history or self.tag_trend_draws.value() > max_history:
                QMessageBox.information(self, "提示", 
                    f"历史数据仅有 {max_history} 期，将使用全部可用数据进行预测。")
            
            method = self.pred_method.currentText()
            
            for group in range(num_groups):
                if method == "综合预测":
                    result = prediction.predict_all_methods(
                        history,
                        num_to_predict=6,
                        recent_draws_count=recent_draws,
                        tag_trend_draws=tag_trend_draws
                    )
                    self._add_prediction_results(f"第{group+1}组综合预测", result)
                    # 显示各方法的预测结果
                    for method_name, method_result in result['method_results'].items():
                        self._add_prediction_results(f"  {method_name}", method_result)

                    # Add label predictions to the same table for "综合预测"
                    label_predictions = result.get('label_predictions')
                    if label_predictions:
                        # Add a header row for label predictions
                        row = self.results_table.rowCount()
                        self.results_table.insertRow(row)
                        header_item = QTableWidgetItem("--- 标签预测 ---")
                        header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.results_table.setItem(row, 0, header_item)
                        if self.results_table.columnCount() > 0: # Ensure there are columns
                             self.results_table.setSpan(row, 0, 1, self.results_table.columnCount())

                        for category, tags_list in label_predictions.items():
                            row = self.results_table.rowCount()
                            self.results_table.insertRow(row)

                            self.results_table.setItem(row, 0, QTableWidgetItem(category))
                            tags_str = ", ".join(tags_list) if tags_list else "无"
                            self.results_table.setItem(row, 1, QTableWidgetItem(tags_str))
                            self.results_table.setItem(row, 2, QTableWidgetItem("")) # Empty for the third column
                else:
                    # 单一方法预测
                    prediction_method_func = self._get_prediction_method(method)
                    num_predict_val = 6 # Placeholder, ideally from a UI element if it exists for this granularity
                                        # For now, using 6 as it was in the original code.

                    if method == "基础预测":
                        reg_freq, spec_freq = analysis.calculate_frequencies(history)
                        result = prediction_method_func(
                            history_data=history,
                            regular_freq=reg_freq,
                            special_freq=spec_freq,
                            num_to_predict=num_predict_val,
                            recent_draws_count=recent_draws # recent_draws is from self.recent_draws.value()
                        )
                    elif method == "标签预测":
                        reg_freq, spec_freq = analysis.calculate_frequencies(history)
                        result = prediction_method_func(
                            history_data=history,
                            regular_freq=reg_freq,
                            special_freq=spec_freq,
                            number_tags=tagging.number_tags, # tagging is imported in gui.py
                            num_to_predict=num_predict_val,
                            recent_draws_count=recent_draws, # recent_draws is from self.recent_draws.value()
                            tag_trend_draws=tag_trend_draws # tag_trend_draws is from self.tag_trend_draws.value()
                        )
                    elif method in ["马尔可夫预测", "贝叶斯预测", "时间序列预测"]: # These use predict_numbers_advanced
                        result = prediction_method_func(
                            history, # This will be args[0] in the lambda
                            num_to_predict=num_predict_val
                        )
                    elif method == "灰度预测": # This uses predict_using_grey_model
                        result = prediction_method_func(
                            history_data=history,
                            num_to_predict=num_predict_val
                        )
                    else:
                        # Fallback or error for unknown method if any, though ComboBox should prevent this.
                        QMessageBox.warning(self, "错误", f"未知的预测方法: {method}")
                        continue # Skip this group

                    self._add_prediction_results(f"第{group+1}组 ({method})", result) # Added method name for clarity
            
            self.statusBar.showMessage("预测完成")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("预测失败")

    def _add_prediction_results(self, method_name: str, result: dict):
        """向结果表格添加一行预测结果"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        reg_nums = [self.format_number(n) for n in result['regular']]
        spec_num = self.format_number(result['special'])
        
        self.results_table.setItem(row, 0, QTableWidgetItem(method_name))
        self.results_table.setItem(row, 1, QTableWidgetItem(', '.join(reg_nums)))
        self.results_table.setItem(row, 2, QTableWidgetItem(spec_num))

    def _get_prediction_method(self, method_name: str):
        """获取对应的预测方法"""
        method_map = {
            "基础预测": prediction.predict_numbers_basic,
            "标签预测": prediction.predict_numbers_with_tags,
            "马尔可夫预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="markov", **kwargs),
            "贝叶斯预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="bayes", **kwargs),
            "时间序列预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="timeseries", **kwargs),
            "灰度预测": prediction.predict_using_grey_model
        }
        return method_map.get(method_name)

    def handle_fetch_from_api(self):
        # Placeholder for now, will be implemented in the next step
        api_url = self.api_url_input.text()
        if not api_url:
            QMessageBox.warning(self, "提示", "请输入API URL")
            return
        self.statusBar.showMessage(f"准备从API获取数据: {api_url}")
        # Actual fetching logic will be added later
        api_url = self.api_url_input.text().strip()
        if not api_url:
            QMessageBox.warning(self, "提示", "请输入API URL")
            return

        self.statusBar.showMessage(f"正在从API获取数据: {api_url}...")
        QApplication.processEvents() # Update UI to show status message

        try:
            # Fetch data from API
            response = requests.get(api_url, timeout=10) # Added timeout
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            raw_api_data = response.json()

            # Validate API response structure
            if raw_api_data.get("code") != 0:
                message = raw_api_data.get("message", "API返回错误状态")
                QMessageBox.warning(self, "API错误", f"API请求失败: {message}")
                self.statusBar.showMessage("API请求失败")
                return

            api_draw_data = raw_api_data.get("data")
            if not isinstance(api_draw_data, list):
                QMessageBox.warning(self, "API数据格式错误", "API返回的数据格式不正确 (data字段不是列表).")
                self.statusBar.showMessage("API数据格式错误")
                return

            if not api_draw_data:
                QMessageBox.information(self, "提示", "API未返回任何开奖数据。")
                self.statusBar.showMessage("API未返回数据")
                return

            # Load existing history
            try:
                history = data_input.load_history()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载本地历史数据失败: {str(e)}")
                self.statusBar.showMessage("加载本地历史数据失败")
                return

            existing_draw_ids = {draw['date'] for draw in history}
            new_draws_added_count = 0

            # Process API data
            new_records_to_add = []
            for api_draw in api_draw_data:
                draw_id = api_draw.get("issue")
                open_code_str = api_draw.get("openCode")
                # open_time = api_draw.get("openTime") # Not directly used in save_history

                if not draw_id or not open_code_str:
                    print(f"警告: API数据条目缺少期号或开奖号码: {api_draw}")
                    continue

                if not (draw_id.isdigit() and len(draw_id) == 7):
                    print(f"警告: 跳过无效API期号格式: {draw_id} (应为7位数字)")
                    continue

                if draw_id in existing_draw_ids:
                    # This message can be noisy if API often returns old data,
                    # so consider removing it or making it less prominent if that's the case.
                    # print(f"信息: 期号 {draw_id} 已存在于历史记录中，跳过。")
                    continue

                try:
                    # Parse openCode: "n1,n2,n3,n4,n5,n6,special"
                    numbers_str_list = open_code_str.split(',')
                    if len(numbers_str_list) != 7:
                        print(f"警告: 开奖号码格式不正确 (数量应为7个，逗号分隔): {open_code_str} for issue {draw_id}")
                        continue

                    # Convert to integers
                    numbers_int_list = [int(n.strip()) for n in numbers_str_list]

                    numbers = numbers_int_list[:-1]
                    special_num = numbers_int_list[-1]

                    # Validate numbers
                    if not all(1 <= n <= 49 for n in numbers):
                         print(f"警告: 正码中有号码超出1-49范围 for issue {draw_id}: {numbers}")
                         continue
                    if not (1 <= special_num <= 49):
                         print(f"警告: 特码超出1-49范围 for issue {draw_id}: {special_num}")
                         continue
                    if len(set(numbers)) != 6:
                        print(f"警告: 正码中有重复号码 for issue {draw_id}: {numbers}")
                        continue
                    if special_num in numbers:
                        print(f"警告: 特码与正码中某个号码重复 for issue {draw_id}: special {special_num}, regular {numbers}")
                        continue

                    transformed_draw = {
                        'date': draw_id,
                        'numbers': numbers, # List of 6 integers
                        'special': special_num # Single integer
                    }
                    new_records_to_add.append(transformed_draw)
                    existing_draw_ids.add(draw_id) # Add to set to prevent duplicates from API itself if API has internal dupes
                    new_draws_added_count += 1

                except ValueError as ve: # Catches errors from int() conversion if numbers are not valid integers
                    print(f"警告: 解析号码时数值转换出错 for issue {draw_id}: {open_code_str}. Error: {ve}")
                    continue

            if not new_records_to_add:
                QMessageBox.information(self, "提示", "没有新的开奖数据需要添加 (可能所有数据都已存在或API数据格式不符合要求)。")
                self.statusBar.showMessage("没有新的开奖数据")
                return

            # Append new records to history and save
            # The history object is modified in place by extend
            history.extend(new_records_to_add)
            try:
                # save_history should take the entire dataset and overwrite the file
                data_input.save_history(history)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存合并后的历史数据失败: {str(e)}")
                self.statusBar.showMessage("保存历史数据失败")
                return

            self.update_history_table() # Refresh the UI table
            QMessageBox.information(self, "成功", f"成功从API获取并添加了 {new_draws_added_count} 条新记录。")
            self.statusBar.showMessage(f"成功添加 {new_draws_added_count} 条新记录")

        except requests.exceptions.Timeout:
            QMessageBox.warning(self, "网络错误", "请求API超时。请检查网络连接或API地址。")
            self.statusBar.showMessage("API请求超时")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "网络错误", f"请求API时发生网络错误: {str(e)}")
            self.statusBar.showMessage("API请求网络错误")
        except ValueError as e: # Handles JSON decoding errors or other value errors during processing
            QMessageBox.warning(self, "数据错误", f"处理API数据时出错 (例如JSON解码失败或数值转换问题): {str(e)}")
            self.statusBar.showMessage("API数据处理错误")
        except Exception as e: # Catch any other unexpected errors
            QMessageBox.critical(self, "未知错误", f"发生未知错误: {str(e)}")
            self.statusBar.showMessage(f"发生未知错误: {e}")
        finally:
            QApplication.processEvents() # Ensure UI updates after all operations

    def init_input_tab(self):
        """输入页面"""
        input_tab = QWidget()
        layout = QVBoxLayout()

        # API 输入区域
        api_group = QGroupBox("从API获取数据")
        api_layout = QVBoxLayout()

        api_url_layout = QHBoxLayout()
        api_url_layout.addWidget(QLabel("API URL:"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("输入API URL")
        api_url_layout.addWidget(self.api_url_input)
        api_layout.addLayout(api_url_layout)

        self.fetch_api_button = QPushButton("获取数据")
        self.fetch_api_button.clicked.connect(self.handle_fetch_from_api)
        api_layout.addWidget(self.fetch_api_button)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 期号输入区域
        draw_id_layout = QHBoxLayout()
        draw_id_layout.addWidget(QLabel("期号:"))
        self.draw_id_input = QLineEdit()
        self.draw_id_input.setPlaceholderText("格式: YYYYNNN 例如: 2025001")
        
        # 自动设置初始期号
        self._set_initial_draw_id()
        draw_id_layout.addWidget(self.draw_id_input)
        layout.addLayout(draw_id_layout)
        
        # 号码输入区域
        numbers_group = QGroupBox("号码输入")
        numbers_layout = QVBoxLayout()
        
        regular_layout = QHBoxLayout()
        regular_layout.addWidget(QLabel("六个正码(用点号分隔):"))
        self.numbers_input = QLineEdit()
        self.numbers_input.setPlaceholderText("例如: 01.02.03.04.05.06")
        
        # 添加回车键支持
        self.numbers_input.returnPressed.connect(self.handle_submit)
        regular_layout.addWidget(self.numbers_input)
        numbers_layout.addLayout(regular_layout)
        
        special_layout = QHBoxLayout()
        special_layout.addWidget(QLabel("特别号码:"))
        self.special_input = QLineEdit()
        self.special_input.setPlaceholderText("例如: 07")
        # 添加回车键支持
        self.special_input.returnPressed.connect(self.handle_submit)
        special_layout.addWidget(self.special_input)
        numbers_layout.addLayout(special_layout)
        
        numbers_group.setLayout(numbers_layout)
        layout.addWidget(numbers_group)
        
        # 添加按钮
        submit_btn = QPushButton("添加开奖记录")
        submit_btn.clicked.connect(self.handle_submit)
        layout.addWidget(submit_btn)
        
        # 历史记录表格
        history_group = QGroupBox("历史记录")
        history_layout = QVBoxLayout()
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels(["期号", "号码1", "号码2", "号码3", "号码4", "号码5", "号码6", "特别号"])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        input_tab.setLayout(layout)
        self.tabs.addTab(input_tab, "数据输入")

        # 设置表格右键菜单
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 使表格可选择
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def init_analysis_tab(self):
        """分析页面"""
        analysis_tab = QWidget()
        layout = QVBoxLayout()
        
        # 分析控制面板
        control_group = QGroupBox("分析控制")
        control_layout = QHBoxLayout()
        
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["全部", "正码", "特码"])
        control_layout.addWidget(QLabel("分析类型:"))
        control_layout.addWidget(self.analysis_type)
        
        self.top_n = QSpinBox()
        self.top_n.setValue(5)
        self.top_n.setRange(1, 20)
        control_layout.addWidget(QLabel("显示前N个:"))
        control_layout.addWidget(self.top_n)
        
        self.periods_spin = QSpinBox()
        self.periods_spin.setRange(1, 1000)
        self.periods_spin.setValue(100)
        control_layout.addWidget(QLabel("分析期数:"))
        control_layout.addWidget(self.periods_spin)
        
        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self.handle_analysis)
        control_layout.addWidget(analyze_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 分析结果表格
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["号码", "出现次数", "出现频率", "最近出现"])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.result_table)
        
        # 可视化按钮
        viz_btn = QPushButton("生成图表")
        viz_btn.clicked.connect(self.handle_visualization)
        results_layout.addWidget(viz_btn)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        analysis_tab.setLayout(layout)
        self.tabs.addTab(analysis_tab, "数据分析")
    
    def init_prediction_tab(self):
        """预测页面"""
        prediction_tab = QWidget()
        layout = QVBoxLayout()
        
        # 预测控制组
        control_group = QGroupBox("预测控制")
        control_layout = QGridLayout()
        
        # 预测方法选择
        self.pred_method = QComboBox()
        self.pred_method.addItems([
            "综合预测",
            "基础预测",
            "标签预测",
            "马尔可夫预测",
            "贝叶斯预测",
            "时间序列预测",
            "灰度预测"
        ])
        control_layout.addWidget(QLabel("预测方法:"), 0, 0)
        control_layout.addWidget(self.pred_method, 0, 1)
        
        # 预测组数
        self.num_predictions = QSpinBox()
        self.num_predictions.setRange(1, 10)
        self.num_predictions.setValue(5)
        control_layout.addWidget(QLabel("预测组数:"), 0, 2)
        control_layout.addWidget(self.num_predictions, 0, 3)
        
        # 参数设置
        self.recent_draws = QSpinBox()
        self.recent_draws.setRange(5, 1000)  # 修改最大值为1000
        self.recent_draws.setValue(10)
        control_layout.addWidget(QLabel("参考期数:"), 1, 0)
        control_layout.addWidget(self.recent_draws, 1, 1)
        
        self.tag_trend_draws = QSpinBox()
        self.tag_trend_draws.setRange(10, 1000)  # 修改最大值为1000
        self.tag_trend_draws.setValue(20)
        control_layout.addWidget(QLabel("标签趋势期数:"), 1, 2)
        control_layout.addWidget(self.tag_trend_draws, 1, 3)
        
        # 预测按钮
        predict_btn = QPushButton("开始预测")
        predict_btn.clicked.connect(self.handle_prediction)
        control_layout.addWidget(predict_btn, 2, 0, 1, 4)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 预测结果显示区域
        results_group = QGroupBox("预测结果")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["预测方法", "预测正码", "预测特码"])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)
        
        self.confidence_label = QLabel("置信度分析:")
        results_layout.addWidget(self.confidence_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        prediction_tab.setLayout(layout)
        self.tabs.addTab(prediction_tab, "号码预测")

    def handle_prediction(self):
        """处理预测请求"""
        try:
            # 清空表格
            self.results_table.setRowCount(0)
            num_groups = self.num_predictions.value()
            
            history = data_input.load_history()
            if not history:
                QMessageBox.warning(self, "警告", "没有历史数据，预测将基于随机或有限数据")
            
            # 获取实际可用的历史数据长度
            max_history = len(history)
            recent_draws = min(self.recent_draws.value(), max_history)
            tag_trend_draws = min(self.tag_trend_draws.value(), max_history)
            
            # 如果请求的期数超过实际数据，显示提示
            if self.recent_draws.value() > max_history or self.tag_trend_draws.value() > max_history:
                QMessageBox.information(self, "提示", 
                    f"历史数据仅有 {max_history} 期，将使用全部可用数据进行预测。")
            
            method = self.pred_method.currentText()
            
            for group in range(num_groups):
                if method == "综合预测":
                    result = prediction.predict_all_methods(
                        history,
                        num_to_predict=6,
                        recent_draws_count=recent_draws,
                        tag_trend_draws=tag_trend_draws
                    )
                    self._add_prediction_results(f"第{group+1}组综合预测", result)
                    # 显示各方法的预测结果
                    for method_name, method_result in result['method_results'].items():
                        self._add_prediction_results(f"  {method_name}", method_result)
                else:
                    # 单一方法预测
                    prediction_method = self._get_prediction_method(method)
                    if method in ["基础预测", "标签预测"]:
                        # 这些方法需要频率数据
                        reg_freq, spec_freq = analysis.calculate_frequencies(history)
                        result = prediction_method(
                            history,
                            reg_freq,
                            spec_freq,
                            number_tags=tagging.number_tags if method == "标签预测" else None,
                            num_to_predict=6,
                            recent_draws_count=recent_draws,
                            tag_trend_draws=tag_trend_draws
                        )
                    else:
                        # 高级预测方法不需要频率数据
                        result = prediction_method(
                            history,
                            num_to_predict=6
                        )
                    self._add_prediction_results(f"第{group+1}组", result)
            
            self.statusBar.showMessage("预测完成")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("预测失败")

    def _add_prediction_results(self, method_name: str, result: dict):
        """向结果表格添加一行预测结果"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        reg_nums = [self.format_number(n) for n in result['regular']]
        spec_num = self.format_number(result['special'])
        
        self.results_table.setItem(row, 0, QTableWidgetItem(method_name))
        self.results_table.setItem(row, 1, QTableWidgetItem(', '.join(reg_nums)))
        self.results_table.setItem(row, 2, QTableWidgetItem(spec_num))

    def _get_prediction_method(self, method_name: str):
        """获取对应的预测方法"""
        method_map = {
            "基础预测": prediction.predict_numbers_basic,
            "标签预测": prediction.predict_numbers_with_tags,
            "马尔可夫预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="markov", **kwargs),
            "贝叶斯预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="bayes", **kwargs),
            "时间序列预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="timeseries", **kwargs),
            "灰度预测": prediction.predict_using_grey_model
        }
        return method_map.get(method_name)

    def init_input_tab(self):
        """输入页面"""
        input_tab = QWidget()
        layout = QVBoxLayout()
        
        # 期号输入区域
        draw_id_layout = QHBoxLayout()
        draw_id_layout.addWidget(QLabel("期号:"))
        self.draw_id_input = QLineEdit()
        self.draw_id_input.setPlaceholderText("格式: YYYYNNN 例如: 2025001")
        
        # 自动设置初始期号
        self._set_initial_draw_id()
        draw_id_layout.addWidget(self.draw_id_input)
        layout.addLayout(draw_id_layout)
        
        # 号码输入区域
        numbers_group = QGroupBox("号码输入")
        numbers_layout = QVBoxLayout()
        
        regular_layout = QHBoxLayout()
        regular_layout.addWidget(QLabel("六个正码(用点号分隔):"))
        self.numbers_input = QLineEdit()
        self.numbers_input.setPlaceholderText("例如: 01.02.03.04.05.06")
        
        # 添加回车键支持
        self.numbers_input.returnPressed.connect(self.handle_submit)
        regular_layout.addWidget(self.numbers_input)
        numbers_layout.addLayout(regular_layout)
        
        special_layout = QHBoxLayout()
        special_layout.addWidget(QLabel("特别号码:"))
        self.special_input = QLineEdit()
        self.special_input.setPlaceholderText("例如: 07")
        # 添加回车键支持
        self.special_input.returnPressed.connect(self.handle_submit)
        special_layout.addWidget(self.special_input)
        numbers_layout.addLayout(special_layout)
        
        numbers_group.setLayout(numbers_layout)
        layout.addWidget(numbers_group)
        
        # 添加按钮
        submit_btn = QPushButton("添加开奖记录")
        submit_btn.clicked.connect(self.handle_submit)
        layout.addWidget(submit_btn)
        
        # 历史记录表格
        history_group = QGroupBox("历史记录")
        history_layout = QVBoxLayout()
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels(["期号", "号码1", "号码2", "号码3", "号码4", "号码5", "号码6", "特别号"])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        input_tab.setLayout(layout)
        self.tabs.addTab(input_tab, "数据输入")

        # 设置表格右键菜单
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 使表格可选择
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

    def init_analysis_tab(self):
        """分析页面"""
        analysis_tab = QWidget()
        layout = QVBoxLayout()
        
        # 分析控制面板
        control_group = QGroupBox("分析控制")
        control_layout = QHBoxLayout()
        
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["全部", "正码", "特码"])
        control_layout.addWidget(QLabel("分析类型:"))
        control_layout.addWidget(self.analysis_type)
        
        self.top_n = QSpinBox()
        self.top_n.setValue(5)
        self.top_n.setRange(1, 20)
        control_layout.addWidget(QLabel("显示前N个:"))
        control_layout.addWidget(self.top_n)
        
        self.periods_spin = QSpinBox()
        self.periods_spin.setRange(1, 1000)
        self.periods_spin.setValue(100)
        control_layout.addWidget(QLabel("分析期数:"))
        control_layout.addWidget(self.periods_spin)
        
        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self.handle_analysis)
        control_layout.addWidget(analyze_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 分析结果表格
        results_group = QGroupBox("分析结果")
        results_layout = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["号码", "出现次数", "出现频率", "最近出现"])
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.result_table)
        
        # 可视化按钮
        viz_btn = QPushButton("生成图表")
        viz_btn.clicked.connect(self.handle_visualization)
        results_layout.addWidget(viz_btn)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        analysis_tab.setLayout(layout)
        self.tabs.addTab(analysis_tab, "数据分析")
    
    def init_prediction_tab(self):
        """预测页面"""
        prediction_tab = QWidget()
        layout = QVBoxLayout()
        
        # 预测控制组
        control_group = QGroupBox("预测控制")
        control_layout = QGridLayout()
        
        # 预测方法选择
        self.pred_method = QComboBox()
        self.pred_method.addItems([
            "综合预测",
            "基础预测",
            "标签预测",
            "马尔可夫预测",
            "贝叶斯预测",
            "时间序列预测",
            "灰度预测"
        ])
        control_layout.addWidget(QLabel("预测方法:"), 0, 0)
        control_layout.addWidget(self.pred_method, 0, 1)
        
        # 预测组数
        self.num_predictions = QSpinBox()
        self.num_predictions.setRange(1, 10)
        self.num_predictions.setValue(5)
        control_layout.addWidget(QLabel("预测组数:"), 0, 2)
        control_layout.addWidget(self.num_predictions, 0, 3)
        
        # 参数设置
        self.recent_draws = QSpinBox()
        self.recent_draws.setRange(5, 1000)  # 修改最大值为1000
        self.recent_draws.setValue(10)
        control_layout.addWidget(QLabel("参考期数:"), 1, 0)
        control_layout.addWidget(self.recent_draws, 1, 1)
        
        self.tag_trend_draws = QSpinBox()
        self.tag_trend_draws.setRange(10, 1000)  # 修改最大值为1000
        self.tag_trend_draws.setValue(20)
        control_layout.addWidget(QLabel("标签趋势期数:"), 1, 2)
        control_layout.addWidget(self.tag_trend_draws, 1, 3)
        
        # 预测按钮
        predict_btn = QPushButton("开始预测")
        predict_btn.clicked.connect(self.handle_prediction)
        control_layout.addWidget(predict_btn, 2, 0, 1, 4)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 预测结果显示区域
        results_group = QGroupBox("预测结果")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["预测方法", "预测正码", "预测特码"])
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)
        
        self.confidence_label = QLabel("置信度分析:")
        results_layout.addWidget(self.confidence_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        prediction_tab.setLayout(layout)
        self.tabs.addTab(prediction_tab, "号码预测")

    def handle_prediction(self):
        """处理预测请求"""
        try:
            # 清空表格
            self.results_table.setRowCount(0)
            num_groups = self.num_predictions.value()
            
            history = data_input.load_history()
            if not history:
                QMessageBox.warning(self, "警告", "没有历史数据，预测将基于随机或有限数据")
            
            # 获取实际可用的历史数据长度
            max_history = len(history)
            recent_draws = min(self.recent_draws.value(), max_history)
            tag_trend_draws = min(self.tag_trend_draws.value(), max_history)
            
            # 如果请求的期数超过实际数据，显示提示
            if self.recent_draws.value() > max_history or self.tag_trend_draws.value() > max_history:
                QMessageBox.information(self, "提示", 
                    f"历史数据仅有 {max_history} 期，将使用全部可用数据进行预测。")
            
            method = self.pred_method.currentText()
            
            for group in range(num_groups):
                if method == "综合预测":
                    result = prediction.predict_all_methods(
                        history,
                        num_to_predict=6,
                        recent_draws_count=recent_draws,
                        tag_trend_draws=tag_trend_draws
                    )
                    self._add_prediction_results(f"第{group+1}组综合预测", result)
                    # 显示各方法的预测结果
                    for method_name, method_result in result['method_results'].items():
                        self._add_prediction_results(f"  {method_name}", method_result)
                else:
                    # 单一方法预测
                    prediction_method = self._get_prediction_method(method)
                    if method in ["基础预测", "标签预测"]:
                        # 这些方法需要频率数据
                        reg_freq, spec_freq = analysis.calculate_frequencies(history)
                        result = prediction_method(
                            history,
                            reg_freq,
                            spec_freq,
                            number_tags=tagging.number_tags if method == "标签预测" else None,
                            num_to_predict=6,
                            recent_draws_count=recent_draws,
                            tag_trend_draws=tag_trend_draws
                        )
                    else:
                        # 高级预测方法不需要频率数据
                        result = prediction_method(
                            history,
                            num_to_predict=6
                        )
                    self._add_prediction_results(f"第{group+1}组", result)
            
            self.statusBar.showMessage("预测完成")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("预测失败")

    def _add_prediction_results(self, method_name: str, result: dict):
        """向结果表格添加一行预测结果"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        reg_nums = [self.format_number(n) for n in result['regular']]
        spec_num = self.format_number(result['special'])
        
        self.results_table.setItem(row, 0, QTableWidgetItem(method_name))
        self.results_table.setItem(row, 1, QTableWidgetItem(', '.join(reg_nums)))
        self.results_table.setItem(row, 2, QTableWidgetItem(spec_num))

    def _get_prediction_method(self, method_name: str):
        """获取对应的预测方法"""
        method_map = {
            "基础预测": prediction.predict_numbers_basic,
            "标签预测": prediction.predict_numbers_with_tags,
            "马尔可夫预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="markov", **kwargs),
            "贝叶斯预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="bayes", **kwargs),
            "时间序列预测": lambda *args, **kwargs: prediction.predict_numbers_advanced(history_data=args[0], method="timeseries", **kwargs),
            "灰度预测": prediction.predict_using_grey_model
        }
        return method_map.get(method_name)

    def init_tags_tab(self):
        """标签管理页面"""
        try:
            tags_tab = QWidget()
            layout = QVBoxLayout()
            
            # 号码网格
            numbers_group = QGroupBox("号码标签管理")
            numbers_layout = QGridLayout()
            
            # 创建49个号码按钮
            self.number_buttons = {}
            for num in range(1, 50):
                btn = QPushButton(self.format_number(num))
                btn.setFixedSize(50, 50)
                btn.clicked.connect(lambda checked, n=num: self.show_number_tags(n))
                row = (num - 1) // 7
                col = (num - 1) % 7
                numbers_layout.addWidget(btn, row, col)
                self.number_buttons[num] = btn
                
            numbers_group.setLayout(numbers_layout)
            layout.addWidget(numbers_group)

            # 标签操作区域
            control_group = QGroupBox("标签操作")
            control_layout = QVBoxLayout()
            
            # 添加标签
            add_layout = QHBoxLayout()
            self.tag_input = QLineEdit()
            self.tag_input.setPlaceholderText("输入新标签")
            # 添加回车键支持
            self.tag_input.returnPressed.connect(self.add_tag_to_selected)
            add_layout.addWidget(self.tag_input)
            
            add_btn = QPushButton("添加")
            add_btn.clicked.connect(self.add_tag_to_selected)
            add_layout.addWidget(add_btn)
            
            control_layout.addLayout(add_layout)
            
            # 当前标签列表
            self.tag_list = QTableWidget()
            self.tag_list.setColumnCount(2)
            self.tag_list.setHorizontalHeaderLabels(["标签", "操作"])
            self.tag_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            control_layout.addWidget(self.tag_list)
            
            control_group.setLayout(control_layout)
            layout.addWidget(control_group)
            
            tags_tab.setLayout(layout)
            self.tabs.addTab(tags_tab, "标签管理")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化标签页失败: {str(e)}")

    def init_label_prediction_tab(self):
        """标签预测页面 Tab for Label Prediction."""
        label_prediction_tab = QWidget()
        layout = QVBoxLayout(label_prediction_tab) # Set layout for the tab

        # Placeholder content
        placeholder_label = QLabel("标签预测功能将在这里实现。")
        layout.addWidget(placeholder_label)

        # Add more UI elements for label prediction here later
        # For example:
        # - A button to trigger label prediction
        # - A display area (e.g., QTableWidget or QTextEdit) for results

        # Remove placeholder
        # if placeholder_label.layout() is not None: # Check if it's in a layout
        #     layout.removeWidget(placeholder_label)
        #     placeholder_label.deleteLater()
        # Or, more simply, just don't add it if we are re-writing the method content.
        # The previous step added the tab with the placeholder.
        # This step will define the method with new content.
        # So, we clear the existing layout first if we are truly "modifying" the content of an existing tab widget.
        # However, init_label_prediction_tab is called once at startup.
        # The task is to *modify the method's definition*, not to dynamically change UI after it's shown.

        # Clear previous content by taking the widget and setting a new layout (or clearing children)
        # This is simpler: the method will now define the final content directly.
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # --- 预测控制区域 ---
        control_group = QGroupBox("预测控制")
        control_layout = QGridLayout(control_group) # Changed to QGridLayout and set parent

        # QLabel for the spinbox
        draws_label = QLabel("分析期数:")
        control_layout.addWidget(draws_label, 0, 0) # Row 0, Col 0

        # QSpinBox for draw count
        self.label_pred_draws_spinbox = QSpinBox()
        self.label_pred_draws_spinbox.setRange(10, 1000)
        self.label_pred_draws_spinbox.setValue(100)
        self.label_pred_draws_spinbox.setSuffix(" 期")
        control_layout.addWidget(self.label_pred_draws_spinbox, 0, 1) # Row 0, Col 1

        # QPushButton for starting prediction
        self.predict_labels_button = QPushButton("开始标签预测")
        self.predict_labels_button.clicked.connect(self.handle_label_prediction)
        control_layout.addWidget(self.predict_labels_button, 0, 2) # Row 0, Col 2

        # Optional: Add some stretch to make the button not take the whole remaining width
        control_layout.setColumnStretch(3, 1) # Add a stretchable column after the button

        # control_group.setLayout(control_layout) # Already set by passing control_group to QGridLayout constructor
        layout.addWidget(control_group)

        # --- 标签预测结果区域 ---
        results_group = QGroupBox("标签预测结果")
        results_layout = QVBoxLayout()

        self.label_results_table = QTableWidget()
        self.label_results_table.setColumnCount(2)
        self.label_results_table.setHorizontalHeaderLabels(["标签类别", "预测标签"])

        header = self.label_results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # First column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Second column

        results_layout.addWidget(self.label_results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        self.tabs.addTab(label_prediction_tab, "标签预测")

    def handle_label_prediction(self):
        """Handles the '开始标签预测' button click."""
        try:
            self.label_results_table.setRowCount(0)
            self.statusBar.showMessage("正在进行标签预测...")

            history = data_input.load_history()
            if not history:
                QMessageBox.warning(self, "数据不足", "没有历史数据可用于预测标签。")
                self.statusBar.showMessage("标签预测失败：数据不足")
                return

            # Get user-selected draw count for label prediction analysis window
            user_selected_draws = self.label_pred_draws_spinbox.value()

            # Default for num_to_predict (for number predictions part of predict_all_methods)
            num_to_predict_default = 6
            # Default for tag_trend_draws (for predict_numbers_with_tags part of predict_all_methods)
            # This is not controlled by the label prediction tab UI.
            tag_trend_draws_for_number_prediction_with_tags = 20

            all_preds_result = prediction.predict_all_methods(
                history_data=history,
                num_to_predict=num_to_predict_default,
                recent_draws_count=user_selected_draws, # Pass the user-selected value for label prediction context
                tag_trend_draws=tag_trend_draws_for_number_prediction_with_tags
            )

            label_predictions = all_preds_result.get('label_predictions')

            if not label_predictions: # Also handles if label_predictions is an empty dict
                QMessageBox.warning(self, "预测无结果", "未能生成标签预测。可能是因为历史数据不足或特定标签组合未出现。")
                self.statusBar.showMessage("未能生成标签预测")
                return

            for category_name, predicted_tags_list in label_predictions.items():
                row_position = self.label_results_table.rowCount()
                self.label_results_table.insertRow(row_position)
                self.label_results_table.setItem(row_position, 0, QTableWidgetItem(category_name))
                tags_str = ", ".join(predicted_tags_list) if predicted_tags_list else "无"
                self.label_results_table.setItem(row_position, 1, QTableWidgetItem(tags_str))

            self.label_results_table.resizeColumnsToContents()
            self.statusBar.showMessage("标签预测完成")

        except Exception as e:
            QMessageBox.critical(self, "预测错误", f"进行标签预测时发生错误: {str(e)}")
            self.statusBar.showMessage(f"标签预测失败: {str(e)}")

    def load_system_data(self):
        """加载系统数据"""
        try:
            self.update_history_table()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载系统数据失败: {str(e)}")

    def show_number_tags(self, number: int):
        """显示号码的标签"""
        self.selected_number = number
        tags = tagging.get_tags_for_number(number)
        
        self.tag_list.setRowCount(0)
        for tag in sorted(tags):
            row = self.tag_list.rowCount()
            self.tag_list.insertRow(row)
            self.tag_list.setItem(row, 0, QTableWidgetItem(tag))
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, t=tag: self.remove_tag_from_selected(t))
            self.tag_list.setCellWidget(row, 1, delete_btn)
            
        self.statusBar.showMessage(f"已选择号码: {number}")

    def add_tag_to_selected(self):
        """为选中的号码添加标签"""
        if not hasattr(self, 'selected_number'):
            QMessageBox.warning(self, "警告", "请先选择一个号码")
            return
            
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "警告", "请输入标签")
            return
            
        try:
            tagging.add_custom_tag(self.selected_number, tag)
            self.show_number_tags(self.selected_number)  # 刷新标签列表
            self.tag_input.clear()
            self.statusBar.showMessage(f"已添加标签 '{tag}' 到号码 {self.selected_number}")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def remove_tag_from_selected(self, tag: str):
        """从选中号码移除标签"""
        if not hasattr(self, 'selected_number'):
            return
            
        try:
            tagging.remove_tag(self.selected_number, tag)
            self.show_number_tags(self.selected_number)  # 刷新标签列表
            self.statusBar.showMessage(f"已从号码 {self.selected_number} 移除标签 '{tag}'")
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    def handle_analysis(self):
        """处理数据分析请求"""
        try:
            history = data_input.load_history()
            if not history:
                raise ValueError("没有历史数据")
            
            periods = self.periods_spin.value()
            history = history[-periods:] if len(history) > periods else history
            
            reg_freq, spec_freq = analysis.calculate_frequencies(history)
            
            self.result_table.setRowCount(0)
            analysis_type = self.analysis_type.currentText()
            top_n = self.top_n.value()
            
            if analysis_type in ["全部", "正码"]:
                most_freq = analysis.get_most_frequent(reg_freq, top_n)
                for num, freq in most_freq:
                    row = self.result_table.rowCount()
                    self.result_table.insertRow(row)
                    self.result_table.setItem(row, 0, QTableWidgetItem(f"{num:02d}"))
                    self.result_table.setItem(row, 1, QTableWidgetItem(str(freq)))
                    percent = (freq / sum(reg_freq.values())) * 100
                    self.result_table.setItem(row, 2, QTableWidgetItem(f"{percent:.2f}%"))
            
            if analysis_type in ["全部", "特码"]:
                most_freq = analysis.get_most_frequent(spec_freq, top_n)
                for num, freq in most_freq:
                    row = self.result_table.rowCount()
                    self.result_table.insertRow(row)
                    self.result_table.setItem(row, 0, QTableWidgetItem(f"{num:02d}"))
                    self.result_table.setItem(row, 1, QTableWidgetItem(str(freq)))
                    percent = (freq / sum(spec_freq.values())) * 100
                    self.result_table.setItem(row, 2, QTableWidgetItem(f"{percent:.2f}%"))
            
            self.statusBar.showMessage("分析完成")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("分析失败")

    def handle_visualization(self):
        """处理可视化请求"""
        try:
            history = data_input.load_history()
            if not history:
                raise ValueError("没有历史数据")
            
            reg_freq, spec_freq = analysis.calculate_frequencies(history)
            
            # 创建图表保存目录
            plot_path = os.path.join("data", "analysis_plots")
            os.makedirs(plot_path, exist_ok=True)
            
            # 生成并保存图表
            freq_plot_path = os.path.join(plot_path, "frequency_distribution.png")
            trend_plot_path = os.path.join(plot_path, "trend_analysis.png")
            
            visualization.plot_number_frequencies(reg_freq, spec_freq, freq_plot_path)
            visualization.plot_trend_analysis(history, trend_plot_path)
            
            self.statusBar.showMessage(f"图表已保存到: {plot_path}")
            QMessageBox.information(self, "成功", f"图表已保存到:\n{plot_path}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("生成图表失败")

    def handle_submit(self):
        """处理提交新开奖记录"""
        try:
            # 获取期号
            draw_id = self.draw_id_input.text().strip()
            if not draw_id:
                raise ValueError("请输入期号")
            if not (draw_id.isdigit() and len(draw_id) == 7):
                raise ValueError("期号必须为7位数字，格式为: YYYYNNN")
                
            # 获取正码号码，使用点号分隔
            numbers_text = self.numbers_input.text().strip()
            if not numbers_text:
                raise ValueError("请输入正码号码")
                
            try:
                numbers = [int(n.strip()) for n in numbers_text.split('.')]
                if len(numbers) != 6:
                    raise ValueError("必须输入6个正码号码")
                if len(set(numbers)) != 6:
                    raise ValueError("正码号码不能重复")
                if not all(1 <= n <= 49 for n in numbers):
                    raise ValueError("号码必须在1-49之间")
            except ValueError as e:
                if str(e) == "invalid literal for int() with base 10":
                    raise ValueError("号码必须为数字")
                raise e
                
            # 获取特别号码
            special_text = self.special_input.text().strip()
            if not special_text:
                raise ValueError("请输入特别号码")
                
            try:
                special = int(special_text)
                if not (1 <= special <= 49):
                    raise ValueError("特别号码必须在1-49之间")
                if special in numbers:
                    raise ValueError("特别号码不能与正码重复")
            except ValueError as e:
                if str(e).startswith("invalid literal"):
                    raise ValueError("特别号码必须为数字")
                raise e
            
            # 构建数据并保存，保持原始顺序
            new_draw = {
                'date': draw_id,
                'numbers': numbers,  # 不再排序
                'special': special
            }
            
            # 加载现有数据
            history = data_input.load_history()
            
            # 检查期号是否已存在
            if any(draw['date'] == draw_id for draw in history):
                raise ValueError(f"期号 {draw_id} 已存在")
                
            # 添加新记录
            history.append(new_draw)
            data_input.save_history(history)
            
            # 更新界面显示
            self.update_history_table()
            
            # 提交成功后自动递增期号
            self.increment_draw_id()
            
            # 清空输入框并设置焦点到号码输入框
            self.numbers_input.clear()
            self.special_input.clear()
            self.numbers_input.setFocus()
            
            self.statusBar.showMessage(f"成功添加期号 {draw_id} 的开奖记录")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            self.statusBar.showMessage("添加记录失败")

    def _set_initial_draw_id(self):
        """设置初始期号"""
        try:
            history = data_input.load_history()
            if history:
                # 获取最新的期号
                latest_id = max(int(draw['date']) for draw in history)
                # 设置下一期的期号
                next_id = str(latest_id + 1)
            else:
                # 如果没有历史记录，使用当前年份作为起始
                current_year = datetime.now().year
                next_id = f"{current_year}001"
            
            self.draw_id_input.setText(next_id)
        except Exception as e:
            print(f"设置初始期号失败: {str(e)}")

    def increment_draw_id(self):
        """递增期号"""
        try:
            current_id = self.draw_id_input.text()
            if current_id and len(current_id) == 7 and current_id.isdigit():
                next_id = str(int(current_id) + 1)
                self.draw_id_input.setText(next_id)
        except Exception as e:
            print(f"递增期号失败: {str(e)}")

    def show_context_menu(self, position):
        """显示右键菜单"""
        try:
            menu = QMenu()
            delete_action = menu.addAction("删除")
            action = menu.exec(self.history_table.viewport().mapToGlobal(position))
            
            if action == delete_action:
                self.delete_selected_row()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"菜单操作失败: {str(e)}")

    def delete_selected_row(self):
        """删除选中的记录"""
        try:
            current_row = self.history_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "警告", "请先选择要删除的记录")
                return
                
            # 获取期号
            draw_id = self.history_table.item(current_row, 0).text()
            
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除期号 {draw_id} 的记录吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 从数据文件中删除
                history = data_input.load_history()
                history = [draw for draw in history if draw['date'] != draw_id]
                data_input.save_history(history)
                
                # 从表格中删除
                self.history_table.removeRow(current_row)
                self.statusBar.showMessage(f"已删除期号 {draw_id} 的记录")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"删除记录失败: {str(e)}")

def launch_gui():
    """启动GUI应用"""
    try:
        app = QApplication(sys.argv)
        window = LotteryAnalyzerGUI()
        window.show()
        return app.exec()
    except Exception as e:
        print(f"GUI启动失败: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(launch_gui())
if __name__ == '__main__':
    sys.exit(launch_gui())
