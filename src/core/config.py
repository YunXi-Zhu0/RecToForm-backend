import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 测试文件目录
TESTS_DIR = ROOT_DIR / "tests"