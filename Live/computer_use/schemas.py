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
            "Click on any button, icon, tab, or element on the desktop screen. "
            "You receive real-time screen frames with the visible mouse cursor. "
            "First visually anchor the target element relative to surrounding landmarks, then provide normalized (x, y) coordinates on a 0-1000 grid. "
            "x=0 is leftmost edge, x=1000 is rightmost edge. y=0 is topmost edge, y=1000 is bottommost edge. "
            "CRITICAL: Observe the subsequent live stream frame to verify if the element opened. "
            "If cursor missed slightly, use 'computer_align_mouse' with (dx, dy) to shift onto the button."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "visual_anchor": {
                    "type": "STRING",
                    "description": "Visual anchor describing where the target element is located relative to screen edges or visible landmarks (e.g. 'top-right corner of the window below header', 'blue submit button in center modal'). MUST BE SPECIFIED FIRST to guarantee coordinate precision!"
                },
                "element_hint": {
                    "type": "STRING",
                    "description": "Name or label of the target element (e.g. 'search button', 'close button', 'settings icon', 'first video')."
                },
                "x": {
                    "type": "NUMBER",
                    "description": "Normalized horizontal X coordinate (0 to 1000) of the target element center."
                },
                "y": {
                    "type": "NUMBER",
                    "description": "Normalized vertical Y coordinate (0 to 1000) of the target element center."
                },
                "button": {
                    "type": "STRING",
                    "description": "Mouse button: 'left' (default), 'right' (for context menu), or 'middle'."
                },
                "double_click": {
                    "type": "BOOLEAN",
                    "description": "Set to true to double-click (e.g. to open an icon, file, or select a word)."
                }
            },
            "required": ["visual_anchor", "element_hint", "x", "y"]
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
    },
    {
        "name": "computer_restore_mouse",
        "description": (
            "Restores the mouse cursor back to its previous original position before the last Friday click or movement. "
            "Call this immediately when a click missed, landed in the wrong place, when Sir says you clicked wrong, "
            "or to undo an unwanted cursor movement."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "computer_align_mouse",
        "description": (
            "Micro-align or nudge the mouse cursor by relative pixel offsets (dx, dy) from its current position. "
            "Use this when you observe in the live video stream that your previous click or cursor landed slightly off-center "
            "or away from the target button/link. "
            "Set click_after=True (default) to immediately click the target button once aligned. "
            "dx: horizontal pixel offset (+ to nudge right, - to nudge left). "
            "dy: vertical pixel offset (+ to nudge down, - to nudge up). "
            "CRITICAL: After aligning and clicking, inspect the next incoming live screen frame to visually verify if the button responded!"
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "dx": {
                    "type": "NUMBER",
                    "description": "Horizontal pixel offset (+ to nudge right, - to nudge left) relative to current cursor position."
                },
                "dy": {
                    "type": "NUMBER",
                    "description": "Vertical pixel offset (+ to nudge down, - to nudge up) relative to current cursor position."
                },
                "click_after": {
                    "type": "BOOLEAN",
                    "description": "Whether to click the mouse immediately after aligning onto the target (default True)."
                },
                "button": {
                    "type": "STRING",
                    "description": "Mouse button to click: 'left' (default), 'right', or 'middle'."
                },
                "double_click": {
                    "type": "BOOLEAN",
                    "description": "Whether to double-click after aligning (default False)."
                },
                "element_hint": {
                    "type": "STRING",
                    "description": "Visual label of the button/element being aligned to (e.g. 'submit button', 'close button', 'tab')."
                },
                "reason": {
                    "type": "STRING",
                    "description": "Visual reason (e.g. 'cursor was 20px above the button, shifting down and clicking')."
                }
            },
            "required": ["dx", "dy"]
        }
    }
]
