"""
=============================================================================
F.R.I.D.A.Y LIVE COMPUTER USE // GEMINI FUNCTION CALLING SCHEMAS
=============================================================================
OpenAPI function declaration specifications for Gemini 2.5 Live Multimodal
WebSocket streaming.
=============================================================================
"""

COMPUTER_USE_SCHEMAS = [
    {
        "name": "computer_click",
        "description": (
            "Click on the screen at normalized coordinates (0 to 1000 grid based on what you see in the video stream). "
            "x=0 is leftmost, x=1000 is rightmost. y=0 is topmost, y=1000 is bottommost. "
            "Always provide 'element_hint' (e.g. 'search bar', 'close button', 'new tab', 'submit') "
            "to activate intelligent UI landmark snapping for 100% pixel-perfect accuracy."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "x": {
                    "type": "NUMBER",
                    "description": "Normalized X coordinate (0 to 1000) of the UI element center."
                },
                "y": {
                    "type": "NUMBER",
                    "description": "Normalized Y coordinate (0 to 1000) of the UI element center."
                },
                "button": {
                    "type": "STRING",
                    "description": "Mouse button: 'left' (default), 'right' (for context menu), or 'middle'."
                },
                "double_click": {
                    "type": "BOOLEAN",
                    "description": "Set to true to double-click (e.g. to open an icon, file, or select a word)."
                },
                "element_hint": {
                    "type": "STRING",
                    "description": "Visual label or type of element (e.g. 'search bar', 'close button', 'minimize', 'new tab', 'submit', 'start menu'). Highly recommended for sub-pixel auto-alignment!"
                }
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "computer_type",
        "description": (
            "Type text into an input field or editor. Optionally specify (x, y) coordinates "
            "and 'element_hint' to click and focus the target field before typing."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text": {
                    "type": "STRING",
                    "description": "Text to type or paste into the field."
                },
                "x": {
                    "type": "NUMBER",
                    "description": "Optional normalized X coordinate (0-1000) of the input field to click before typing."
                },
                "y": {
                    "type": "NUMBER",
                    "description": "Optional normalized Y coordinate (0-1000) of the input field to click before typing."
                },
                "element_hint": {
                    "type": "STRING",
                    "description": "Visual label of the input field (e.g. 'search bar', 'address bar', 'chat input')."
                },
                "press_enter": {
                    "type": "BOOLEAN",
                    "description": "Whether to press the Enter key after typing (e.g. to submit a search query)."
                },
                "clear_first": {
                    "type": "BOOLEAN",
                    "description": "Whether to select all (Ctrl+A) and clear the existing text before typing."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_press_key",
        "description": (
            "Press a keyboard key or hotkey combination on Windows. "
            "Examples: 'enter', 'esc', 'tab', 'space', 'backspace', 'ctrl+c', 'ctrl+v', 'ctrl+t', 'ctrl+w', 'win+r', 'alt+tab'."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "key_or_hotkey": {
                    "type": "STRING",
                    "description": "Key name or hotkey combination separated by '+' (e.g. 'enter', 'ctrl+c', 'alt+f4', 'win+r')."
                },
                "count": {
                    "type": "INTEGER",
                    "description": "Number of times to press the key (default 1)."
                }
            },
            "required": ["key_or_hotkey"]
        }
    },
    {
        "name": "computer_scroll",
        "description": (
            "Scroll the page or active window up or down. Optionally provide (x, y) coordinates "
            "to position the cursor over the specific scrollable area first."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "direction": {
                    "type": "STRING",
                    "description": "Scroll direction: 'down' (default) or 'up'."
                },
                "amount": {
                    "type": "INTEGER",
                    "description": "Scroll magnitude in mouse wheel clicks (default 5)."
                },
                "x": {
                    "type": "NUMBER",
                    "description": "Optional normalized X coordinate (0-1000) to place cursor before scrolling."
                },
                "y": {
                    "type": "NUMBER",
                    "description": "Optional normalized Y coordinate (0-1000) to place cursor before scrolling."
                }
            }
        }
    },
    {
        "name": "computer_drag",
        "description": (
            "Drag from starting coordinates to destination coordinates on the screen. "
            "Useful for moving windows, sliders, files, or canvas drawing."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "from_x": {"type": "NUMBER", "description": "Starting normalized X (0-1000)."},
                "from_y": {"type": "NUMBER", "description": "Starting normalized Y (0-1000)."},
                "to_x": {"type": "NUMBER", "description": "Destination normalized X (0-1000)."},
                "to_y": {"type": "NUMBER", "description": "Destination normalized Y (0-1000)."},
                "button": {"type": "STRING", "description": "Mouse button: 'left' (default) or 'right'."}
            },
            "required": ["from_x", "from_y", "to_x", "to_y"]
        }
    },
    {
        "name": "computer_inspect_screen",
        "description": "Inspect current display resolution, mouse cursor position, and title of active foreground window."
    }
]
