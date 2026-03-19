# Agent Quality Guard - CLI Integration Examples

## 基本用法

### 1. 單文件掃描

```bash
python src/main.py --file your_code.py
```

### 2. 目錄掃描

```bash
python src/main.py --file ./src
```

### 3. JSON 輸出 (CI/CD)

```bash
python src/main.py --file your_code.py --json > results.json
```

### 4. LLM 審查

```bash
export OPENAI_API_KEY="sk-..."
python src/main.py --file your_code.py --llm
```

---

## CI/CD 整合

### GitHub Actions

```yaml
# .github/workflows/quality.yml
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
        run: python main.py --file . --json > results.json
      - name: Upload
        uses: actions/upload-artifact@v4
        with:
          name: results
          path: results.json
```

### GitLab CI

```yaml
# .gitlab-ci.yml
code-quality:
  image: python:3.11
  script:
    - pip install agent-quality-guard
    - python main.py --file . --json > results.json
  artifacts:
    paths:
      - results.json
```

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Quality Scan') {
            steps {
                sh 'pip install agent-quality-guard'
                sh 'python main.py --file . --json > results.json'
                archiveArtifacts artifacts: 'results.json', fingerprint: true
            }
        }
    }
}
```

---

## Git Hook 整合

### Pre-commit Hook

```bash
# 安裝
python src/main.py hook install

# 卸載
python src/main.py hook uninstall

# 手動執行
python src/main.py hook run
```

### 自定義 Hook Script

```bash
#!/bin/bash
# pre-commit-scan.sh

echo "Running Agent Quality Guard..."

python src/main.py --file . --json --output scan-results.json

# 檢查結果
if grep -q '"severity": "high"' scan-results.json; then
    echo "❌ High severity issues found!"
    exit 1
fi

echo "✅ Scan passed!"
```

---

## API Server

### 啟動服務器

```bash
python -c "from src.api_server import run_server; run_server(port=8080)"
```

### API 調用

```bash
# 掃描代碼
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "password = \"secret\"", "llm": true}'

# 批量掃描
curl -X POST http://localhost:8080/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{"files": ["app.py", "utils.py"]}'
```

### Python Client

```python
import requests

# 掃描
result = requests.post(
    "http://localhost:8080/analyze",
    json={"code": "password = 'secret'", "llm": True}
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
# 掃描本地代碼
docker run -v $(pwd):/app agent-quality-guard python src/main.py --file /app

# 啟動 API 服務器
docker run -p 8080:8080 -v $(pwd):/app agent-quality-guard python -c "from src.api_server import run_server; run_server()"
```

### Docker Compose

```bash
docker-compose up -d
```

---

## 常見用法

### 1. 只掃描變更的檔案

```bash
# Git diff 獲取變更的檔案
git diff --name-only | xargs python src/main.py --file
```

### 2. 排除特定目錄

```bash
python src/main.py --file . --exclude "tests,vendor,node_modules"
```

### 3. 嚴格模式 (分數低於 70 失敗)

```bash
python src/main.py --file . --strict --threshold 70
```

### 4. 只掃描特定問題類型

```bash
python src/main.py --file . --severity high
python src/main.py --file . --category security
```

---

## 環境變數

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# 自定義配置
export AQG_CONFIG_PATH="/path/to/config.yaml"
export AQG_DATA_DIR="/path/to/data"
```
