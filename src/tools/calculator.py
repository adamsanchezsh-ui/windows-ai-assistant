"""Safe calculator + simple data helpers. No artificial expression length limit."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_FUNCS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
}


def _eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _FUNCS.get(node.func.id)
        if fn and callable(fn):
            return fn(*[_eval(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _FUNCS:
        val = _FUNCS[node.id]
        if not callable(val):
            return val
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate(expression: str) -> dict[str, Any]:
    """Evaluate math expression safely (no eval of arbitrary code)."""
    expr = expression.strip().replace("^", "**")
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree)
        return {"ok": True, "expression": expression, "result": result}
    except Exception as e:
        return {"ok": False, "expression": expression, "error": str(e)}
