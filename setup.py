from setuptools import setup, find_packages

setup(
    name="lottery_analyzer",
    version="0.1",
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'PyQt6>=6.4.0',
        'PyQt6-Qt6>=6.4.0',  # Mac需要
        'PyQt6-sip>=13.4.0',  # Mac需要
        'matplotlib>=3.5.0',
        'seaborn>=0.11.0',
        'pandas>=1.3.0',
        'numpy>=1.20.0',
        'scipy>=1.7.0',  # 用于灰色模型的数学计算
    ],
    entry_points={
        'console_scripts': [
            'lottery-analyzer=lottery_analyzer.main:main',
        ],
    },
)
