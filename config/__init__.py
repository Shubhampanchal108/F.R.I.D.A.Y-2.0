"""
F.R.I.D.A.Y Configuration Package
=================================
Application settings, system instructions, creator details, and config.json key driver.
"""

from config.config_driver import (
    Check_Keys,
    update_config,
    load_data,
    save_data,
)

__all__ = [
    "Check_Keys",
    "update_config",
    "load_data",
    "save_data",
]


def __getattr__(name):
    if name in ("Friday_Instruction", "creator_details", "user_Details", "Name", "email", "phone_number"):
        import config.settings as _settings
        return getattr(_settings, name)
    raise AttributeError(f"module 'config' has no attribute '{name}'")
