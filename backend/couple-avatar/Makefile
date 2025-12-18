.PHONY: install setup run clean test help activate

# Python 版本
PYTHON_VERSION := 3.12
PYTHON := python3

# 项目目录
PROJECT_DIR := $(shell pwd)
VENV_DIR := $(PROJECT_DIR)/venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
VENV_ACTIVATE := $(VENV_DIR)/bin/activate

help:
	@echo "可用目标:"
	@echo "  make install  - 创建 Python 虚拟环境（如果不存在）"
	@echo "  make setup    - 安装项目依赖"
	@echo "  make run      - 执行拼图脚本"
	@echo "  make clean    - 清理临时文件和虚拟环境"
	@echo "  make test     - 运行测试（如果实现）"
	@echo "  make activate - 显示激活虚拟环境的命令"

install:
	@echo "检查 virtualenv 是否已安装..."
	@VIRTUALENV_CMD=""; \
	if command -v virtualenv > /dev/null 2>&1; then \
		VIRTUALENV_CMD="virtualenv"; \
	elif $(PYTHON) -m virtualenv --help > /dev/null 2>&1; then \
		VIRTUALENV_CMD="$(PYTHON) -m virtualenv"; \
	else \
		echo "virtualenv 未安装，正在安装..."; \
		$(PYTHON) -m pip install --user virtualenv 2>/dev/null || $(PYTHON) -m pip install virtualenv; \
		if command -v virtualenv > /dev/null 2>&1; then \
			VIRTUALENV_CMD="virtualenv"; \
		elif $(PYTHON) -m virtualenv --help > /dev/null 2>&1; then \
			VIRTUALENV_CMD="$(PYTHON) -m virtualenv"; \
		fi; \
	fi; \
	if [ -z "$$VIRTUALENV_CMD" ]; then \
		echo "错误: 无法找到 virtualenv 命令"; \
		exit 1; \
	fi; \
	echo "检查虚拟环境是否存在..."; \
	if [ ! -d "$(VENV_DIR)" ]; then \
		echo "创建虚拟环境（使用 virtualenv）..."; \
		$$VIRTUALENV_CMD $(VENV_DIR); \
		echo "虚拟环境创建完成: $(VENV_DIR)"; \
	else \
		echo "虚拟环境目录已存在: $(VENV_DIR)"; \
		echo "检查虚拟环境完整性..."; \
		if [ ! -f "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_PIP)" ]; then \
			echo "警告: 虚拟环境不完整，正在重新创建..."; \
			rm -rf $(VENV_DIR); \
			$$VIRTUALENV_CMD $(VENV_DIR); \
			echo "虚拟环境重新创建完成"; \
		else \
			echo "虚拟环境完整"; \
		fi \
	fi
	@if [ ! -f "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_PIP)" ]; then \
		echo ""; \
		echo "错误: 虚拟环境创建失败！"; \
		echo ""; \
		echo "可能的原因："; \
		echo "  1. virtualenv 安装失败"; \
		echo "  2. Python 环境配置不正确"; \
		echo ""; \
		echo "解决方案："; \
		echo "  手动安装 virtualenv: pip install virtualenv"; \
		echo "  或使用系统包管理器: sudo apt install python3-virtualenv"; \
		echo ""; \
		echo "安装完成后，运行: make clean && make install"; \
		echo ""; \
		exit 1; \
	fi
	@echo "虚拟环境检查完成"

setup: install
	@echo "检查虚拟环境完整性..."
	@if [ ! -d "$(VENV_DIR)" ] || [ ! -f "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_PIP)" ]; then \
		echo "错误: 虚拟环境不完整，请先运行 make install"; \
		exit 1; \
	fi
	@echo "安装/更新依赖..."
	@$(VENV_PIP) install --upgrade pip --quiet
	@$(VENV_PIP) install Pillow numpy scikit-learn
	@echo "依赖安装完成"

run: setup
	@echo "执行拼图脚本..."
	@if [ ! -f "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_PIP)" ]; then \
		echo "错误: 虚拟环境不完整，请先运行 make install"; \
		exit 1; \
	fi
	@$(VENV_PYTHON) puzzle.py $(ARGS)

clean:
	@echo "清理临时文件..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "删除虚拟环境..."; \
		rm -rf $(VENV_DIR); \
		echo "虚拟环境已删除"; \
	fi
	@echo "清理完成"

test: setup
	@echo "运行测试..."
	@if [ ! -f "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_PIP)" ]; then \
		echo "错误: 虚拟环境不完整，请先运行 make install"; \
		exit 1; \
	fi
	@if [ -f "test_puzzle.py" ]; then \
		$(VENV_PYTHON) -m pytest test_puzzle.py -v; \
	else \
		echo "未找到测试文件 test_puzzle.py"; \
	fi

activate:
	@echo "要激活虚拟环境，请运行以下命令:"
	@echo "  source $(VENV_ACTIVATE)"
	@echo ""
	@echo "或者使用:"
	@echo "  . $(VENV_ACTIVATE)"
