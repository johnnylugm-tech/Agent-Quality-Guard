# LLM Judge Prompts - 評分邏輯透明化

> 此文件記錄 LLM Judge 的評分提示詞，讓評分邏輯完全透明

---

## 評分維度

LLM Judge 使用以下維度進行評分：

| 維度 | 權重 | 說明 |
|------|------|------|
| 正確性 | 30% | 語法、邏輯、邊界條件 |
| 安全性 | 25% | 漏洞、認證、加密 |
| 可維護性 | 20% | 結構、命名、註解 |
| 效能 | 15% | 複雜度、資源使用 |
| 測試覆蓋 | 10% | 單元測試、整合測試 |

---

## 評分提示詞

### 系統提示詞

```
You are an expert code reviewer. Analyze the following code and provide detailed feedback.
```

### 用戶提示詞模板

```python
f"""You are an expert code reviewer. Analyze the following code and provide detailed feedback.

{context_str}

## Code to Review:
```{code[:3000]}```

Please provide your analysis in JSON format with these fields:
- "review_score" (0-100): Overall quality score
- "review_level" (A/B/C/D/F): Letter grade
- "strengths" (array): What's good about this code
- "improvements" (array): Specific improvement suggestions
- "security_concerns" (array): Security issues found
- "best_practices" (array): Best practices to follow
- "recommendations" (array): Overall recommendations

Respond ONLY with valid JSON."""
```

---

## 評分標準

### 分數範圍

| 分數 | 等級 | 說明 |
|------|------|------|
| 90-100 | A | 優秀，生產級品質 |
| 80-89 | B | 良好，只需小幅改善 |
| 70-79 | C | 可接受，需要改善 |
| 60-69 | D | 較差，需要大幅重構 |
| 0-59 | F | 不合格，需要重寫 |

---

## 評分維度說明

### 1. 正確性 (30%)

檢查項目：
- 語法正確性
- 邏輯正確性
- 邊界條件處理
- 異常處理

### 2. 安全性 (25%)

檢查項目：
- 敏感資訊處理
- 輸入驗證
- SQL Injection
- XSS
- Command Injection
- 認證/授權

### 3. 可維護性 (20%)

檢查項目：
- 程式碼結構
- 命名規範
- 函數/類別大小
- 重複代碼
- 註解質量

### 4. 效能 (15%)

檢查項目：
- 時間複雜度
- 空間複雜度
- 資料庫查詢優化
- 緩存使用

### 5. 測試覆蓋 (10%)

檢查項目：
- 單元測試存在
- 測試覆蓋率
- 測試質量

---

## JSON 輸出格式

```json
{
  "review_score": 85,
  "review_level": "B",
  "strengths": [
    "清晰的函數命名",
    "良好的錯誤處理"
  ],
  "improvements": [
    "考慮添加類型註釋",
    "可以拆分為更小的函數"
  ],
  "security_concerns": [],
  "best_practices": [
    "使用 logging 而非 print"
  ],
  "recommendations": [
    "建議添加單元測試"
  ]
}
```

---

## 自定義提示詞

你可以在 `config.yaml` 中自定義提示詞：

```yaml
llm_judge:
  custom_prompt: |
    You are a security-focused code reviewer...
    Focus on finding vulnerabilities...
```

---

## 常見問題

### Q: 為什麼分數主觀？

A: LLM 評分基於訓練數據中的最佳實踐，可能因模型而異。建議結合靜態分析的客觀分數使用。

### Q: 如何提高分數？

A:
1. 遵循 PEP 8 (Python)
2. 添加類型註釋
3. 撰寫 Docstring
4. 添加單元測試
5. 處理異常情況

---

## 版本

- v1.0.0 - 初始版本
