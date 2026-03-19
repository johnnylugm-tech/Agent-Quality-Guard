# Agent Quality Guard - Documentation

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Supported Languages](#supported-languages)
5. [Security Rules](#security-rules)
6. [CLI Usage](#cli-usage)
7. [API Server](#api-server)
8. [Docker](#docker)
9. [CI/CD Integration](#cicd-integration)
10. [Configuration](#configuration)

---

## Installation

```bash
# Clone
git clone https://github.com/johnnylugm-tech/Agent-Quality-Guard.git
cd Agent-Quality-Guard
pip install -r requirements.txt

# Docker
docker build -t agent-quality-guard .
```

---

## Quick Start

```bash
# Python scan
python src/main.py --file your_code.py

# JavaScript/TypeScript scan
python src/multi_lang_analyzer.py --file app.js

# Go scan
python src/multi_lang_analyzer.py --file main.go

# With LLM Judge
python src/main.py --file your_code.py --llm
```

---

## Features

| Feature | Description |
|---------|-------------|
| Static Analysis | AST-based code analysis |
| Quality Scoring | 0-100 score + Grade (A-F) |
| Security Scanning | OWASP Top 10 2023 |
| LLM Judge | OpenAI/Claude integration |
| Git Hook | pre-commit integration |
| Report Generation | Markdown/HTML formats |
| Trend Tracking | Historical score analysis |
| API Server | REST API service |
| Docker | Container support |
| CI/CD | GitHub Actions, GitLab, Jenkins |

---

## Supported Languages

| Language | Status | Analyzer |
|----------|--------|----------|
| Python | ✅ Full | AST + patterns |
| JavaScript | ✅ | Pattern-based |
| TypeScript | ✅ | Pattern-based |
| Go | ✅ | Pattern-based |
| Java | 🔄 | Coming soon |
| Rust | 🔄 | Coming soon |

---

## Security Rules

### OWASP Top 10 2023

| Code | Category | Rules |
|------|----------|-------|
| A01 | Broken Access Control | 2 |
| A02 | Cryptographic Failures | 5 |
| A03 | Injection | 7 |
| A04 | Insecure Design | 2 |
| A05 | Security Misconfiguration | 3 |
| A06 | Vulnerable Components | 1 |
| A07 | Auth Failures | 2 |
| A08 | Software Integrity | 1 |
| A09 | Logging Failures | 1 |
| A10 | SSRF | 2 |

### Total: 80+ Rules

---

## CLI Usage

### Basic Commands

```bash
# Scan file
python src/main.py --file code.py

# Scan directory
python src/main.py --file ./src

# JSON output
python src/main.py --file code.py --json

# LLM Judge
python src/main.py --file code.py --llm

# Report
python src/main.py --file code.py --report --report-format html

# Git Hook
python src/main.py hook install
```

### Options

| Option | Description |
|--------|-------------|
| `--file, -f` | File or directory to scan |
| `--code, -c` | Code string to scan |
| `--stdin, -s` | Read from stdin |
| `--json, -j` | JSON output |
| `--llm, -l` | Enable LLM Judge |
| `--report` | Generate report |
| `--report-format` | Format: markdown, html |
| `--verbose, -v` | Verbose output |

---

## API Server

### Start Server

```bash
python -c "from src.api_server import run_server; run_server(port=8080)"
```

### Endpoints

```
GET  /health          - Health check
POST /analyze         - Analyze code
POST /analyze/batch   - Batch analyze
```

### Request Example

```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "password = \"secret\"", "llm": true}'
```

### Python Client

```python
import requests

result = requests.post(
    "http://localhost:8080/analyze",
    json={"code": "your_code_here"}
).json()

print(f"Score: {result['score']}")
print(f"Grade: {result['grade']}")
```

---

## Docker

### Build

```bash
docker build -t agent-quality-guard .
```

### Run

```bash
# Scan file
docker run -v $(pwd):/app agent-quality-guard python src/main.py --file /app

# API Server
docker run -p 8080:8080 agent-quality-guard python -c "from src.api_server import run_server; run_server()"
```

### Docker Compose

```bash
docker-compose up -d
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install
        run: pip install agent-quality-guard
      - name: Scan
        run: python -m src.main --file . --json > results.json
```

### GitLab CI

```yaml
code-quality:
  image: python:3.11
  script:
    - pip install agent-quality-guard
    - python -m src.main --file . --json > results.json
  artifacts:
    paths:
      - results.json
```

---

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## License

MIT
