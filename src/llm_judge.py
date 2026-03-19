"""
Agent Quality Guard - LLM Judge Module v3.0
Deep code review using LLM APIs (OpenAI, Anthropic, MiniMax, Gemini)
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MINIMAX = "minimax"
    GEMINI = "gemini"


@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 30


class LLMJudgeError(Exception):
    """Base exception for LLM Judge errors"""
    def __init__(self, message: str, recoverable: bool = True):
        super().__init__(message)
        self.recoverable = recoverable


class LLMConfigError(LLMJudgeError):
    """Configuration error (L1)"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=False)


class LLMAPIError(LLMJudgeError):
    """API error (L2)"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=True)


class LLMTimeoutError(LLMJudgeError):
    """Timeout error (L3)"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=True)


class LLMRateLimitError(LLMJudgeError):
    """Rate limit error (L4)"""
    def __init__(self, message: str):
        super().__init__(message, recoverable=True)


# =============================================================================
# LLM Judge v3.0 - Split into Prepare, Call, Parse
# =============================================================================

class LLMJudge:
    """
    LLM-powered code review judge.
    
    Uses GPT-4, Claude, or other LLMs for deep code analysis
    beyond static analysis.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_config()
        self._client = None
    
    def _load_config(self) -> LLMConfig:
        """Load config from environment or defaults."""
        # Check for API keys (priority order)
        api_key = None
        provider = None
        model = None
        
        # Check each provider in priority order
        if os.environ.get("MINIMAX_API_KEY"):
            provider = LLMProvider.MINIMAX.value
            api_key = os.environ.get("MINIMAX_API_KEY")
            model = os.environ.get("MINIMAX_MODEL", "abab6.5s")
        elif os.environ.get("GEMINI_API_KEY"):
            provider = LLMProvider.GEMINI.value
            api_key = os.environ.get("GEMINI_API_KEY")
            model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        elif os.environ.get("OPENAI_API_KEY"):
            provider = LLMProvider.OPENAI.value
            api_key = os.environ.get("OPENAI_API_KEY")
            model = os.environ.get("OPENAI_MODEL", "gpt-4")
        elif os.environ.get("ANTHROPIC_API_KEY"):
            provider = LLMProvider.ANTHROPIC.value
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        
        if not api_key:
            raise LLMConfigError(
                "No API key found. Set MINIMAX_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
            )
        
        return LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key
        )
    
    def _init_client(self):
        """Initialize the appropriate LLM client."""
        if self._client:
            return
        
        if self.config.provider == LLMProvider.OPENAI.value:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.config.api_key)
            except ImportError:
                raise LLMConfigError("openai package not installed. Run: pip install openai")
        
        elif self.config.provider == LLMProvider.ANTHROPIC.value:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise LLMConfigError("anthropic package not installed. Run: pip install anthropic")
        
        elif self.config.provider == LLMProvider.MINIMAX.value:
            # MiniMax uses requests directly (no separate package required)
            self._client = None  # Will use requests in _call_minimax
        
        elif self.config.provider == LLMProvider.GEMINI.value:
            try:
                import google.generativeai
                google.generativeai.configure(api_key=self.config.api_key)
                self._client = google.generativeai
            except ImportError:
                raise LLMConfigError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    # =========================================================================
    # Stage 1: Prepare (Build prompt)
    # =========================================================================
    
    def _prepare_prompt(self, code: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Stage 1: Prepare prompt for LLM analysis.
        
        Args:
            code: Source code to review
            context: Optional context (file_path, language, etc.)
            
        Returns:
            Formatted prompt string
        """
        context_str = ""
        if context:
            if "file_path" in context:
                context_str += f"\nFile: {context['file_path']}"
            if "language" in context:
                context_str += f"\nLanguage: {context['language']}"
            if "issues" in context:
                context_str += f"\nAlready detected issues: {len(context['issues'])}"
        
        return f"""You are an expert code reviewer. Analyze the following code and provide detailed feedback.

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
    
    # =========================================================================
    # Stage 2: Call (Make API request)
    # =========================================================================
    
    def _call_api(self, prompt: str) -> str:
        """
        Stage 2: Call LLM API and return raw response.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            Raw API response
        """
        self._init_client()
        
        if self.config.provider == LLMProvider.OPENAI.value:
            return self._call_openai(prompt)
        elif self.config.provider == LLMProvider.ANTHROPIC.value:
            return self._call_anthropic(prompt)
        elif self.config.provider == LLMProvider.MINIMAX.value:
            return self._call_minimax(prompt)
        elif self.config.provider == LLMProvider.GEMINI.value:
            return self._call_gemini(prompt)
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API."""
        try:
            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return self._parse_response(response.choices[0].message.content)
        
        except Exception as e:
            error_msg = str(e)
            
            if "rate limit" in error_msg.lower():
                raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"API timeout: {error_msg}")
            else:
                raise LLMAPIError(f"OpenAI API error: {error_msg}")
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API."""
        try:
            response = self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return self._parse_response(response.content[0].text)
        
        except Exception as e:
            error_msg = str(e)
            
            if "rate limit" in error_msg.lower():
                raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"API timeout: {error_msg}")
            else:
                raise LLMAPIError(f"Anthropic API error: {error_msg}")
    
    def _call_minimax(self, prompt: str) -> Dict[str, Any]:
        """Call MiniMax API."""
        import requests
        
        url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return self._parse_response(content)
            else:
                raise LLMAPIError(f"MiniMax API returned no choices: {data}")
        
        except requests.exceptions.Timeout:
            raise LLMTimeoutError("MiniMax API timeout")
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            if e.response is not None:
                error_msg = f"Status {e.response.status_code}: {e.response.text}"
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
            else:
                raise LLMAPIError(f"MiniMax API error: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise LLMAPIError(f"MiniMax API error: {str(e)}")
        except Exception as e:
            raise LLMAPIError(f"MiniMax API error: {str(e)}")
    
    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API."""
        try:
            model = self._client.GenerativeModel(self.config.model)
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                    "response_schema": {
                        "type": "object",
                        "properties": {
                            "review_score": {"type": "number"},
                            "review_level": {"type": "string"},
                            "strengths": {"type": "array"},
                            "improvements": {"type": "array"},
                            "security_concerns": {"type": "array"},
                            "best_practices": {"type": "array"},
                            "recommendations": {"type": "array"}
                        }
                    }
                }
            )
            
            return self._parse_response(response.text)
        
        except Exception as e:
            error_msg = str(e)
            
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise LLMTimeoutError(f"API timeout: {error_msg}")
            else:
                raise LLMAPIError(f"Gemini API error: {error_msg}")
    
    # =========================================================================
    # Stage 3: Parse (Parse response into structured format)
    # =========================================================================
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Stage 3: Parse LLM response into structured format.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed response as dict
        """
        # Try to extract JSON from response
        try:
            # Find JSON block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            # Return raw response as improvements if JSON parse fails
            return {
                "review_score": 50,
                "review_level": "C",
                "improvements": [response[:500]],
                "recommendations": ["Review response manually"]
            }
    
    # =========================================================================
    # Public API: Review (uses prepare → call → parse)
    # =========================================================================
    
    def review(
        self, 
        code: str, 
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Review code using LLM.
        Uses split stages: prepare → call → parse.
        
        Args:
            code: Source code to review
            context: Optional context (file_path, language, etc.)
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Dict with review results
        """
        # Validate input
        if not code or not code.strip():
            raise LLMConfigError("Code is empty")
        
        # Stage 1: Prepare
        prompt = self._prepare_prompt(code, context)
        
        # Stage 2: Call (with retries)
        last_error = None
        for attempt in range(max_retries):
            try:
                return self._call_api(prompt)
                    
            except LLMRateLimitError as e:
                # L4: Rate limit - wait and retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt * 5  # Exponential backoff
                    time.sleep(wait_time)
                    last_error = e
                    continue
                else:
                    return {
                        "error": str(e),
                        "error_level": "L4",
                        "review_score": None,
                        "review_level": "F",
                        "recommendations": ["Rate limit exceeded. Try again later."]
                    }
            
            except LLMTimeoutError as e:
                # L3: Timeout - can retry
                if attempt < max_retries - 1:
                    time.sleep(2)
                    last_error = e
                    continue
                else:
                    return {
                        "error": str(e),
                        "error_level": "L3",
                        "review_score": None,
                        "review_level": "F",
                        "recommendations": ["Request timed out. Try again."]
                    }
            
            except LLMAPIError as e:
                # L2: API error - can retry
                if attempt < max_retries - 1:
                    time.sleep(1)
                    last_error = e
                    continue
                else:
                    return {
                        "error": str(e),
                        "error_level": "L2",
                        "review_score": None,
                        "review_level": "F",
                        "recommendations": ["API error. Check your configuration."]
                    }
            
            except LLMConfigError as e:
                # L1: Config error - no retry
                return {
                    "error": str(e),
                    "error_level": "L1",
                    "review_score": None,
                    "review_level": "F",
                    "recommendations": ["Fix API key configuration."]
                }
        
        # All retries failed
        return {
            "error": str(last_error),
            "error_level": "L3",
            "review_score": None,
            "review_level": "F",
            "recommendations": ["All retry attempts failed."]
        }
    
    def is_available(self) -> bool:
        """Check if LLM judge is available (API key set)."""
        try:
            self._load_config()
            return True
        except LLMConfigError:
            return False


# =============================================================================
# Convenience Function
# =============================================================================

def llm_review(code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function for LLM review.
    
    Args:
        code: Source code to review
        context: Optional context information
        
    Returns:
        Review results as dict
    """
    try:
        judge = LLMJudge()
        return judge.review(code, context)
    except LLMConfigError as e:
        return {
            "error": str(e),
            "error_level": "L1",
            "review_score": None,
            "review_level": "F",
            "recommendations": ["Configure API key to enable LLM review."]
        }