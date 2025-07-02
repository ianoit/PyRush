# PyRush - Modern Stress Testing Application

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/pyrush.svg)](https://badge.fury.io/py/pyrush)

PyRush is a modern stress testing application for web applications and APIs built with Python. This application supports various advanced features such as async requests, multi-method support, custom headers, rate limiting, duration-based testing, and comprehensive reporting.

## 🚀 Key Features

- **Async HTTP Requests** - High performance using aiohttp
- **Multi-Method Support** - GET, POST, PUT, DELETE, HEAD, OPTIONS
- **Custom Headers & Authentication** - Support for custom headers and basic auth
- **Rate Limiting** - QPS control per worker
- **Duration-based Testing** - Testing based on time (10s, 3m, 1h)
- **Step Load Testing** - Gradual ramp-up concurrency
- **Multi-Core Support** - CPU usage optimization
- **HTTP/2 Support** - HTTP/2 protocol support
- **Proxy Support** - Testing through proxy servers
- **Custom Assertions** - Status code, response body, response time validation
- **Comprehensive Reporting** - PDF, CSV, JSON reports with charts
- **Interactive CLI** - Wizard mode for ease of use
- **Form Data Support** - File upload and form data

## 📋 Requirements

- Python 3.7+
- aiohttp >= 3.8.0
- tqdm >= 4.64.0
- reportlab >= 3.6.0
- matplotlib >= 3.5.0
- certifi >= 2022.0.0

## 🛠️ Installation

### Method 1: Install from Source Code

```bash
# Clone repository
git clone https://github.com/ianoit/pyrush.git
cd pyrush

# Install dependencies
pip install -r requirements.txt

# Install package (optional)
pip install -e .
```

### Method 2: Install via pip

```bash
pip install pyrush
```

### Method 3: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install aiohttp tqdm reportlab matplotlib certifi

# Run PyRush
python -m pyrush.cli --help
```

## 🏗️ Project Structure

```
pyrush/
├── __init__.py          # Package initialization & version info
├── models.py            # Data classes (RequestResult, TestConfig)
├── config.py            # Argument parsing & configuration management
├── core.py              # StressTester class & main testing logic
├── requestor.py         # HTTP request handling & worker functions
├── reporter.py          # Report generation (CSV, JSON, PDF)
└── cli.py               # Command Line Interface & interactive mode

setup.py                 # Package installation script
requirements.txt         # Python dependencies
README.md               # This file
.gitignore              # Git ignore rules
```

### Module Descriptions

- **`models.py`** - Contains data classes for storing request results and test configuration
- **`config.py`** - Handles command line argument parsing and configuration validation
- **`core.py`** - Main StressTester class that manages test execution and statistics
- **`requestor.py`** - Functions for making HTTP requests and worker management
- **`reporter.py`** - Generator for various report formats (PDF, CSV, JSON)
- **`cli.py`** - Command line interface and interactive wizard mode

## 🎯 Usage

### Basic Usage

```bash
# Simple test
python -m pyrush.cli http://example.com -n 100 -c 10

# Test with POST method and data
python -m pyrush.cli http://api.example.com -m POST -d '{"key":"value"}' -n 500 -c 25

# Test with duration
python -m pyrush.cli http://example.com -z 30s -c 100 -q 10

# Test with custom headers
python -m pyrush.cli http://example.com -H "Authorization: Bearer token" -o csv
```

### Interactive Mode

```bash
# Run wizard mode
python -m pyrush.cli -i
```

### Advanced Usage

```bash
# Step load testing (ramp-up concurrency)
python -m pyrush.cli http://example.com --step-load --step-initial 1 --step-max 50 --step-interval 10

# Test with assertions
python -m pyrush.cli http://example.com --assert-status 200 --assert-max-rt 1.0

# Test with form data
python -m pyrush.cli http://example.com --form "username=admin" --form "password=secret"

# Test with file upload
python -m pyrush.cli http://example.com --form-file "file=./test.txt"

# Test with proxy
python -m pyrush.cli http://example.com -x proxy.example.com:8080

# Test with HTTP/2
python -m pyrush.cli http://example.com -h2
```

## 📊 Output & Reports

### Terminal Output

PyRush displays comprehensive statistics in the terminal:

```
============================================================
PYRUSH STRESS TEST RESULTS
============================================================
Total Requests: 1000
Successful Requests: 998
Failed Requests: 2
Success Rate: 99.80%
Total Duration: 45.23s
Requests per Second: 22.11
Throughput (bytes/sec): 15678.45

Response Time Statistics:
  Mean: 0.234s
  Median: 0.198s
  Min: 0.045s
  Max: 2.156s
  P95: 0.567s
  P99: 1.234s
```

### Report Files

PyRush automatically generates reports in the `report_files/` folder:

- **PDF Report** - Comprehensive report with charts and detailed statistics
- **CSV Export** - Raw data for further analysis
- **JSON Export** - Structured data for processing

## 🔧 Development Guide

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/ianoit/pyrush.git
cd pyrush

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install additional dev tools
pip install pytest black flake8 mypy
```

### Project Structure for Development

```
pyrush/
├── __init__.py          # Package metadata & imports
├── models.py            # Data structures
├── config.py            # Configuration & argument parsing
├── core.py              # Main testing logic
├── requestor.py         # HTTP request handling
├── reporter.py          # Report generation
└── cli.py               # Command line interface

tests/                   # Unit tests
├── test_models.py
├── test_config.py
├── test_core.py
├── test_requestor.py
└── test_reporter.py

docs/                    # Documentation
├── api.md
├── examples.md
└── contributing.md

examples/                # Usage examples
├── basic_test.py
├── api_test.py
└── load_test.py
```

### Adding New Features

1. **Identify the appropriate module** for the new feature
2. **Create unit tests** for the feature
3. **Update documentation** in README and docstrings
4. **Test integration** with existing features

### Coding Standards

- **PEP 8** - Python style guide
- **Type hints** - Use type annotations
- **Docstrings** - Complete documentation for all functions
- **Error handling** - Proper exception handling
- **Logging** - Use logging for debugging

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core.py

# Run with coverage
pytest --cov=pyrush

# Run linting
flake8 pyrush/
black pyrush/
mypy pyrush/
```

## 📝 Command Line Options

### Basic Options


| Option               | Description                 | Default  |
| ---------------------- | ----------------------------- | ---------- |
| `urls`               | Target URL(s) to test       | Required |
| `-n, --num-requests` | Number of requests          | 200      |
| `-c, --concurrency`  | Number of workers           | 50       |
| `-q, --rate-limit`   | Rate limit per worker (QPS) | No limit |
| `-z, --duration`     | Test duration (10s, 3m, 1h) | None     |
| `-m, --method`       | HTTP method                 | GET      |

### HTTP Options


| Option            | Description              | Default |
| ------------------- | -------------------------- | --------- |
| `-H, --header`    | Custom HTTP header       | None    |
| `-d, --data`      | Request body             | None    |
| `-D, --data-file` | Request body from file   | None    |
| `-a, --auth`      | Basic auth (user:pass)   | None    |
| `-x, --proxy`     | Proxy server (host:port) | None    |
| `-h2, --http2`    | Enable HTTP/2            | False   |

### Advanced Options


| Option            | Description              | Default     |
| ------------------- | -------------------------- | ------------- |
| `--step-load`     | Enable step load testing | False       |
| `--step-initial`  | Initial concurrency      | 1           |
| `--step-max`      | Maximum concurrency      | concurrency |
| `--step-interval` | Step interval (seconds)  | 10          |
| `--assert-status` | Assert status code       | None        |
| `--assert-max-rt` | Assert max response time | None        |

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Checklist

- [ ] Code follows PEP 8 style guide
- [ ] Added type hints for all functions
- [ ] Added docstrings for all functions
- [ ] Added unit tests for new features
- [ ] Updated documentation
- [ ] All tests pass
- [ ] No linting errors

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP client/server
- [tqdm](https://github.com/tqdm/tqdm) - Progress bars
- [reportlab](https://www.reportlab.com/) - PDF generation
- [matplotlib](https://matplotlib.org/) - Plotting and visualization

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ianoit/pyrush/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ianoit/pyrush/discussions)
- **Documentation**: [Wiki](https://github.com/ianoit/pyrush/wiki)

---

**PyRush** - Modern stress testing for modern applications 🚀
