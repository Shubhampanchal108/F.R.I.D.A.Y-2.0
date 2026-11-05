"""
F.R.I.D.A.Y Core Package
========================
Contains the primary decision brain, multi-tier cognitive router, and security guardrails.
Uses module-level lazy attributes to ensure instant imports without loading heavyweight tools.
"""

def __getattr__(name):
    if name in ["Brain", "Brain_query"]:
        from core.brain import Brain
        return Brain
    if name in ["load_tools", "execute_tool", "TOOLS"]:
        import core.tool_guard as tg
        return getattr(tg, name)
    raise AttributeError(f"module 'core' has no attribute '{name}'")

__all__ = ["Brain", "Brain_query", "load_tools", "execute_tool", "TOOLS"]
