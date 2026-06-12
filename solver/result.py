"""答题结果."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SolveResult:
    topic: Optional[Dict[str, Any]] = None  # 下一题，None 表示全部完成
    answer: str = ""      # 展示文本
    source: str = ""      # 答案来源: pass_through / brute_force / vocab_match / word_list
