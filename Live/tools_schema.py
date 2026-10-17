"""
=============================================================================
F.R.I.D.A.Y LIVE MULTIMODAL // TOOLS SCHEMA REPOSITORY
=============================================================================
Declares all OpenAPI function calling schemas provided to Google Gemini Live
for bidirectional real-time multimodal tool execution.
=============================================================================
"""

LIVE_TOOLS = [
    {
        "function_declarations": [
            # ---- System & Hardware Controls ----
            {
                "name": "volume_up",
                "description": "Increase system audio volume by specified step percentage (default 10%).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "step": {"type": "INTEGER", "description": "Step percentage to increase (default 10)."}
                    }
                }
            },
            {
                "name": "volume_down",
                "description": "Decrease system audio volume by specified step percentage (default 10%).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "step": {"type": "INTEGER", "description": "Step percentage to decrease (default 10)."}
                    }
                }
            },
            {
                "name": "mute_volume",
                "description": "Mute system audio volume."
            },
            {
                "name": "unmute_volume",
                "description": "Unmute system audio volume."
            },
            {
                "name": "brightness_up",
                "description": "Increase screen brightness."
            },
            {
                "name": "brightness_down",
                "description": "Decrease screen brightness."
            },
            {
                "name": "check_battery",
                "description": "Check device battery percentage, charging status, and power health."
            },
            {
                "name": "check_cpu",
                "description": "Check device CPU usage percentage, cores, frequency, and RAM status."
            },
            {
                "name": "open_app",
                "description": "Open a desktop application on Windows (e.g. chrome, notepad, calculator, spotify, vscode).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app": {"type": "STRING", "description": "Name of the application to open."}
                    },
                    "required": ["app"]
                }
            },
            {
                "name": "close_app",
                "description": "Close an application or active window on Windows.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app": {"type": "STRING", "description": "Name of application to close (optional, leave blank for active window)."}
                    }
                }
            },
            {
                "name": "capture_screenshot",
                "description": "Take a screenshot of the current screen and save it to disk."
            },
            {
                "name": "open_website",
                "description": "Open a website URL or domain in the default web browser.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "Website URL or domain (e.g. youtube.com, github.com)."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "minimize_active_window",
                "description": "Minimize the current active window."
            },
            {
                "name": "maximize_active_window",
                "description": "Maximize the current active window."
            },
            {
                "name": "clear_recycle_bin",
                "description": "Empty the Windows recycle bin."
            },
            {
                "name": "find_my_ip",
                "description": "Find device public IP address."
            },
            {
                "name": "check_network_health",
                "description": "Run diagnostic check: ping latency (ms), internet download speed (Mbps), and connection health."
            },
            {
                "name": "focus_window",
                "description": "Bring an open application window (e.g. Chrome, VS Code, Spotify) to the foreground.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "app_name": {"type": "STRING", "description": "Name or title of application window to bring to front."}
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "list_running_apps",
                "description": "List currently running user desktop applications."
            },

            # ---- Date, Time, Weather, News & Search ----
            {
                "name": "get_weather",
                "description": "Get current weather conditions and temperature for a city.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "city": {"type": "STRING", "description": "City or location name."}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get current local time."
            },
            {
                "name": "get_date_with_day",
                "description": "Get today's date and day of week."
            },
            {
                "name": "get_News",
                "description": "Get latest news headlines."
            },
            {
                "name": "google_search",
                "description": "Search Google for current real-time information or questions.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Search query text."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_wikipedia",
                "description": "Search Wikipedia for a topic summary.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Topic or query to look up on Wikipedia."}
                    },
                    "required": ["query"]
                }
            },

            # ---- Media & YouTube Controls ----
            {
                "name": "youtube_automation",
                "description": "Search and play a video or music track on YouTube.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Name of song, artist, or video to play."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "yt_play_pause",
                "description": "Toggle play/pause on current YouTube video tab."
            },
            {
                "name": "yt_next",
                "description": "Skip to the next YouTube video."
            },
            {
                "name": "yt_previous",
                "description": "Go back to the previous YouTube video."
            },
            {
                "name": "yt_fullscreen",
                "description": "Toggle fullscreen on YouTube video."
            },
            {
                "name": "system_media_control",
                "description": "Controls Windows global media playback across Spotify, YouTube, VLC ('play_pause', 'next', 'previous', 'stop').",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {"type": "STRING", "description": "Media action: 'play_pause', 'next', 'previous', or 'stop'."}
                    },
                    "required": ["action"]
                }
            },

            # ---- Productivity, Timers & Clipboard ----
            {
                "name": "set_timer",
                "description": "Set a background countdown timer (e.g. '5 minutes', '30 seconds', '1 hour') with sound chime and alert.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "duration": {"type": "STRING", "description": "Timer duration (e.g. '5 minutes', '30 seconds')."},
                        "label": {"type": "STRING", "description": "Optional label for the timer."}
                    },
                    "required": ["duration"]
                }
            },
            {
                "name": "list_active_timers",
                "description": "List all currently active countdown timers."
            },
            {
                "name": "cancel_timer",
                "description": "Cancel a running countdown timer by label.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "label": {"type": "STRING", "description": "Label of the timer to cancel."}
                    },
                    "required": ["label"]
                }
            },
            {
                "name": "copy_to_clipboard",
                "description": "Copy text or code directly into Windows clipboard for Ctrl+V.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Text to copy to clipboard."}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "get_clipboard_content",
                "description": "Read current text from Windows clipboard."
            },
            {
                "name": "analyze_clipboard",
                "description": "Reads text or error code from clipboard and diagnoses it or provides a complete working fix.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "prompt": {"type": "STRING", "description": "Specific instruction or question regarding clipboard content."}
                    }
                }
            },

            # ---- Tasks (To-Do Management) ----
            {
                "name": "add_task",
                "description": "Add a new task to the user to-do list.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_text": {"type": "STRING", "description": "Description of task to add."}
                    },
                    "required": ["task_text"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List all active tasks in to-do list."
            },
            {
                "name": "delete_task",
                "description": "Delete a task from the to-do list.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_name": {"type": "STRING", "description": "Name or text of task to delete."}
                    },
                    "required": ["task_name"]
                }
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_name": {"type": "STRING", "description": "Name or text of task to mark complete."}
                    },
                    "required": ["task_name"]
                }
            },
            {
                "name": "reopen_task",
                "description": "Reopen a previously completed task.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_name": {"type": "STRING", "description": "Name or text of task to reopen."}
                    },
                    "required": ["task_name"]
                }
            },
            {
                "name": "update_task",
                "description": "Update task title or completion status.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_name": {"type": "STRING", "description": "Current task name."},
                        "new_name": {"type": "STRING", "description": "Optional new task name."},
                        "done": {"type": "BOOLEAN", "description": "Optional completion status."}
                    },
                    "required": ["task_name"]
                }
            },

            # ---- Reminders ----
            {
                "name": "add_reminder",
                "description": "Schedule a reminder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "reminder_text": {"type": "STRING", "description": "What to remind the user about."},
                        "remind_at": {"type": "STRING", "description": "Time to remind, e.g. '18:30', 'in 30 minutes', 'tomorrow at 9 AM'."}
                    },
                    "required": ["reminder_text", "remind_at"]
                }
            },
            {
                "name": "list_reminders",
                "description": "List all active and pending reminders."
            },
            {
                "name": "delete_reminder_by_name",
                "description": "Delete a reminder by its description text.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "reminder_text": {"type": "STRING", "description": "Text of reminder to delete."}
                    },
                    "required": ["reminder_text"]
                }
            },
            {
                "name": "update_reminder",
                "description": "Update reminder text or scheduled time.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "old_text": {"type": "STRING", "description": "Original reminder text."},
                        "new_text": {"type": "STRING", "description": "New reminder text."},
                        "new_remind_at": {"type": "STRING", "description": "New scheduled time."}
                    },
                    "required": ["old_text"]
                }
            },
            {
                "name": "toggle_reminder",
                "description": "Enable or disable a reminder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "reminder_text": {"type": "STRING", "description": "Text of reminder to toggle."},
                        "enabled": {"type": "BOOLEAN", "description": "Enable (true) or disable (false)."}
                    },
                    "required": ["reminder_text"]
                }
            },
            {
                "name": "get_due_reminders",
                "description": "Check and return all reminders that are currently due."
            },

            # ---- Emails ----
            {
                "name": "check_new_mail",
                "description": "Check for new incoming unread emails."
            },
            {
                "name": "read_latest_emails",
                "description": "Read latest incoming emails.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "n": {"type": "INTEGER", "description": "Number of emails to read (default 5)."}
                    }
                }
            },
            {
                "name": "readmail_Full_body",
                "description": "Read full body content of an email by index.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "index": {"type": "INTEGER", "description": "Index of email to read."}
                    },
                    "required": ["index"]
                }
            },
            {
                "name": "send_email",
                "description": "Send an email to a recipient.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "to": {"type": "STRING", "description": "Recipient email address."},
                        "subject": {"type": "STRING", "description": "Email subject."},
                        "body": {"type": "STRING", "description": "Email body content."}
                    },
                    "required": ["to", "subject", "body"]
                }
            },

            # ---- File Management ----
            {
                "name": "create_and_open_file",
                "description": "Create and open a file in user directory.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Name of file to create."},
                        "content": {"type": "STRING", "description": "Initial text content."}
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "read_file",
                "description": "Read contents of a file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Name of file to read."}
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "update_file",
                "description": "Append or update content in a file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Name of file to update."},
                        "new_content": {"type": "STRING", "description": "Content to append or write."}
                    },
                    "required": ["filename", "new_content"]
                }
            },
            {
                "name": "delete_file",
                "description": "Delete a file from user directory.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Name of file to delete."}
                    },
                    "required": ["filename"]
                }
            },
            {
                "name": "list_files",
                "description": "List all files in user workspace directory."
            },
            {
                "name": "rename_file",
                "description": "Rename a file in user directory.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "old_name": {"type": "STRING", "description": "Current file name."},
                        "new_name": {"type": "STRING", "description": "New file name."}
                    },
                    "required": ["old_name", "new_name"]
                }
            },
            {
                "name": "search_file_in_folder",
                "description": "Search if a file exists in folder.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Filename to search."}
                    },
                    "required": ["filename"]
                }
            },

            # ---- Web Scraping & Documents ----
            {
                "name": "summrize_url",
                "description": "Fetch and summarize content from a webpage URL.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL of webpage to summarize."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "extract_webpage_content",
                "description": "Extract full readable text content from any website URL.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "Website URL to scrape."}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "read_pdf_or_document",
                "description": "Read and extract text from PDF documents, text files, or markdown for question-answering.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filepath": {"type": "STRING", "description": "File path of PDF or document."}
                    },
                    "required": ["filepath"]
                }
            },

            # ---- Mobile Automation ----
            {
                "name": "connect_mobile_with_bat",
                "description": "Connect mobile device with Friday via ADB/network.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "ip_address": {"type": "STRING", "description": "Optional mobile device IP address."}
                    }
                }
            },
            {
                "name": "check_connection_json",
                "description": "Check if Android mobile is connected to Friday."
            },
            {
                "name": "unlock_device",
                "description": "Unlock mobile device with PIN code.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "pin_code": {"type": "STRING", "description": "Device unlock PIN."}
                    },
                    "required": ["pin_code"]
                }
            },
            {
                "name": "send_whatsapp_message",
                "description": "Send WhatsApp message via connected mobile device.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "phone_number": {"type": "STRING", "description": "Phone number with country code."},
                        "message": {"type": "STRING", "description": "Message text to send."}
                    },
                    "required": ["phone_number", "message"]
                }
            },
            {
                "name": "phone_call_with_mobile",
                "description": "Make a phone call using connected mobile device.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "phone_number": {"type": "STRING", "description": "Phone number to call."}
                    },
                    "required": ["phone_number"]
                }
            },

            # ---- Memory & Sandbox Agents ----
            {
                "name": "save_longterm_memory",
                "description": "Save critical user facts or context to long-term memory.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Fact or context to remember."},
                        "memory_type": {"type": "STRING", "description": "Type of memory (e.g. 'user_preference', 'project_fact')."}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "run_python_code",
                "description": "Execute Python code snippet in sandbox for calculation or analysis.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "code": {"type": "STRING", "description": "Python code to execute."}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "deep_research_agent",
                "description": "Launch deep research autonomous agent on a topic.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "topic": {"type": "STRING", "description": "Topic or research question."}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "code_reviewer_agent",
                "description": "Launch autonomous code review agent on code snippet or file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "code_or_filename": {"type": "STRING", "description": "Code string or filename to review."}
                    },
                    "required": ["code_or_filename"]
                }
            }
        ]
    }
]


def get_live_tools():
    """Return function calling declarations formatted for Gemini Live."""
    return LIVE_TOOLS
