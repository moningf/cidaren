"""Solver 注册表 — 按 topic_mode 分发."""
from typing import Any, Dict, List, Optional

from config import DEEPSEEK_API_KEY
from utils.ai import AIService
from utils.vocab import VocabService
from solver.base import BaseSolver
from solver.mode_00 import Mode00Solver
from solver.mode_11 import Mode11Solver
from solver.mode_22 import Mode22Solver
from solver.mode_31 import Mode31Solver
from solver.mode_32 import Mode32Solver
from solver.mode_51 import Mode51Solver


def create_registry(
    course_id: str,
    word_list: List[Dict[str, Any]],
    ai: Optional[AIService] = None,
) -> Dict[int, BaseSolver]:
    vocab = VocabService(course_id, word_list)
    if ai is None:
        ai = AIService() if (DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.strip()) else None
    return {
        0: Mode00Solver(),
        11: Mode11Solver(),
        22: Mode22Solver(),
        31: Mode31Solver(),
        32: Mode32Solver(vocab, ai=ai),
        51: Mode51Solver(vocab, ai=ai),
    }
