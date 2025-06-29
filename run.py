import sys
import argparse
import os

# Mac特定配置
os.environ['QT_MAC_WANTS_LAYER'] = '1'
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false;*.info=false;qt.qpa.xcb.*=false'
os.environ['QT_ENABLE_GLYPH_CACHE_WORKAROUND'] = '1'
os.environ['QT_MAC_DISABLE_FOREGROUND_APPLICATION_TRANSFORM'] = '1'
os.environ['QT_QPA_PLATFORM'] = 'cocoa'

def main():
    parser = argparse.ArgumentParser(description="Lottery Analyzer")
    parser.add_argument("--gui", action="store_true", help="启动图形界面")
    args, remaining = parser.parse_known_args()

    if args.gui:
        from lottery_analyzer.gui import launch_gui
        launch_gui()
    else:
        from lottery_analyzer.main import main as cli_main
        # 正确传递剩余参数给 CLI
        sys.argv = [sys.argv[0]] + remaining
        cli_main()

if __name__ == "__main__":
    main()
