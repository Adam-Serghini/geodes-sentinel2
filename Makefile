.PHONY: help install install-dev test format lint type-check clean docs

help:
	@echo "Available commands:"
	@echo "  make install      Install package with core dependencies"
	@echo "  make install-dev  Install package with all development dependencies"
	@echo "  make test         Run tests with pytest"
	@echo "  make format       Format code with black"
	@echo "  make lint         Lint code with ruff"
	@echo "  make type-check   Type check with mypy"
	@echo "  make clean        Remove build artifacts and cache files"
	@echo "  make docs         Build documentation"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev,viz,docs]"

test:
	pytest tests/ -v --cov=geodes_sentinel2 --cov-report=term-missing

format:
	black geodes_sentinel2/ tests/
	ruff check --fix geodes_sentinel2/ tests/

lint:
	ruff check geodes_sentinel2/ tests/
	black --check geodes_sentinel2/ tests/

type-check:
	mypy geodes_sentinel2/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

docs:
	cd docs && make html

# Windows-specific commands (if on Windows, use these instead)
clean-windows:
	if exist build rmdir /s /q build
	if exist dist rmdir /s /q dist
	if exist *.egg-info rmdir /s /q *.egg-info
	if exist .coverage del .coverage
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	del /s /q *.pyc 2>nul
	del /s /q *.pyo 2>nul