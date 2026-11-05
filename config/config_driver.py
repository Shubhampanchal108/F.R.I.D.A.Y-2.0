import json
import os
import sys
from datetime import datetime

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.box import ROUNDED, DOUBLE

from utils.paths import DOCS_PATH
from utils.helpers import Default_Data, search

CONFIG_FILE = os.path.join(DOCS_PATH, "config.json")
console = Console()


def load_data():
    if not os.path.exists(CONFIG_FILE):
        save_data(Default_Data)
        return Default_Data

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default top keys exist
            for category, keys in Default_Data.items():
                if category not in data:
                    data[category] = keys
                else:
                    if isinstance(keys, dict):
                        for k, v in keys.items():
                            if k not in data[category]:
                                data[category][k] = v
            return data
    except Exception as e:
        console.print(f"[bold red]❌ Config Load Error: {e}. Resetting to default config.[/bold red]")
        save_data(Default_Data)
        return Default_Data


def save_data(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Config Save Error: {e}[/bold red]")
        return False


def update_config(parKey, childKey, value):
    data = load_data()
    if parKey not in data:
        data[parKey] = {}

    data[parKey][childKey] = value

    if save_data(data):
        console.print(f"[bold green]✅ Config updated successfully: [{parKey}][{childKey}][/bold green]")
        return True

    console.print("[bold red]❌ Failed to update config.[/bold red]")
    return False


def Check_Keys(parKey, childKey):
    data = load_data()
    category = data.get(parKey, {})
    val = category.get(childKey, "")

    if not val:
        # Avoid hanging in non-interactive background tasks or subshells
        if not sys.stdin or not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            return ""
        try:
            console.print(f"\n[bold yellow]⚠️ Missing Configuration Key: [{parKey}][{childKey}][/bold yellow]")
            val = Prompt.ask(f"[bold cyan]Please provide value for {childKey}[/bold cyan]")
            if val:
                update_config(parKey, childKey, val.strip())
                return val.strip()
        except Exception:
            return ""

    return val


def get_neural_keys() -> dict:
    """
    Returns the dictionary of neural keys for all cascade providers:
    GEMINI, HUGGINGFACE, GROQ, OPENROUTER.
    Automatically imports legacy single keys for seamless backward compatibility.
    """
    data = load_data()
    neural_keys = data.setdefault("NEURAL_KEYS", {
        "GEMINI": [],
        "HUGGINGFACE": [],
        "GROQ": [],
        "OPENROUTER": []
    })

    for p in ["GEMINI", "HUGGINGFACE", "GROQ", "OPENROUTER"]:
        if p not in neural_keys or not isinstance(neural_keys[p], list):
            neural_keys[p] = []

    legacy_keys = data.get("KEYS", {})
    if not neural_keys["GEMINI"] and legacy_keys.get("GEMINI_KEY"):
        neural_keys["GEMINI"].append(legacy_keys["GEMINI_KEY"].strip())

    if not neural_keys["OPENROUTER"] and legacy_keys.get("OPENROUTER_API_KEY"):
        neural_keys["OPENROUTER"].append(legacy_keys["OPENROUTER_API_KEY"].strip())

    if not neural_keys["GROQ"] and legacy_keys.get("GROQ_API_KEY"):
        neural_keys["GROQ"].append(legacy_keys["GROQ_API_KEY"].strip())

    if not neural_keys["HUGGINGFACE"] and legacy_keys.get("HUGGINGFACE_API_KEY"):
        neural_keys["HUGGINGFACE"].append(legacy_keys["HUGGINGFACE_API_KEY"].strip())

    return neural_keys


def add_neural_key(provider: str, key: str) -> bool:
    """Adds a new API key to a specific cascade provider."""
    provider = provider.upper().strip()
    key = key.strip()
    if not key or provider not in ["GEMINI", "HUGGINGFACE", "GROQ", "OPENROUTER"]:
        return False

    data = load_data()
    neural_keys = data.setdefault("NEURAL_KEYS", {
        "GEMINI": [],
        "HUGGINGFACE": [],
        "GROQ": [],
        "OPENROUTER": []
    })

    if provider not in neural_keys or not isinstance(neural_keys[provider], list):
        neural_keys[provider] = []

    if key not in neural_keys[provider]:
        neural_keys[provider].append(key)
        # Sync legacy slot for fallback
        if provider == "GEMINI" and not data.get("KEYS", {}).get("GEMINI_KEY"):
            data.setdefault("KEYS", {})["GEMINI_KEY"] = key
        elif provider == "OPENROUTER" and not data.get("KEYS", {}).get("OPENROUTER_API_KEY"):
            data.setdefault("KEYS", {})["OPENROUTER_API_KEY"] = key
        elif provider == "GROQ" and not data.get("KEYS", {}).get("GROQ_API_KEY"):
            data.setdefault("KEYS", {})["GROQ_API_KEY"] = key
        elif provider == "HUGGINGFACE" and not data.get("KEYS", {}).get("HUGGINGFACE_API_KEY"):
            data.setdefault("KEYS", {})["HUGGINGFACE_API_KEY"] = key

        return save_data(data)
    return True


def delete_neural_key(provider: str, index: int) -> bool:
    """Deletes an API key by index from a specific cascade provider."""
    provider = provider.upper().strip()
    data = load_data()
    neural_keys = data.get("NEURAL_KEYS", {})
    if provider in neural_keys and isinstance(neural_keys[provider], list):
        if 0 <= index < len(neural_keys[provider]):
            removed = neural_keys[provider].pop(index)
            # If the legacy key matches this deleted key, update it
            legacy_map = {
                "GEMINI": "GEMINI_KEY",
                "OPENROUTER": "OPENROUTER_API_KEY",
                "GROQ": "GROQ_API_KEY",
                "HUGGINGFACE": "HUGGINGFACE_API_KEY"
            }
            slot = legacy_map.get(provider)
            if slot and data.get("KEYS", {}).get(slot) == removed:
                data["KEYS"][slot] = neural_keys[provider][0] if neural_keys[provider] else ""

            return save_data(data)
    return False


def is_agent_configured():
    data = load_data()
    password = data.get("KEYS", {}).get("AGENT_PASSWORD", "")
    neural = get_neural_keys()
    has_neural_key = any(len(keys) > 0 for keys in neural.values())
    legacy_key = bool(data.get("KEYS", {}).get("LLM_KEY", ""))
    return bool((has_neural_key or legacy_key) and password)


def run_first_time_setup():
    console.clear()
    setup_panel = Panel(
        "[bold cyan]Welcome to F.R.I.D.A.Y Setup Wizard![/bold cyan]\n\n"
        "[white]It looks like this is your first time running F.R.I.D.A.Y on this machine.\n"
        "Configure your security credentials and at least one Neural Key to activate.[/white]",
        title="[bold yellow]⚙️ FIRST-TIME AGENT CONFIGURATION[/bold yellow]",
        box=DOUBLE,
        border_style="yellow"
    )
    console.print(setup_panel)

    data = load_data()

    # 1. Security Password
    console.print("\n[bold yellow]1. Security Authentication[/bold yellow]")
    current_pass = data.get("KEYS", {}).get("AGENT_PASSWORD", "")
    new_pass = Prompt.ask("Set security access password for CLI Agent", default=current_pass or "Friday123")
    data["KEYS"]["AGENT_PASSWORD"] = new_pass.strip()

    # 2. Primary Neural Key (Gemini / OpenRouter / Groq)
    console.print("\n[bold yellow]2. Neural Core Key (Google Gemini / OpenRouter / Groq / HuggingFace)[/bold yellow]")
    gem_key = Prompt.ask("Enter Google Gemini API Key (Recommended Priority 1, leave blank to skip)", password=True, default="")
    if gem_key.strip():
        add_neural_key("GEMINI", gem_key.strip())

    or_key = Prompt.ask("Enter OpenRouter API Key (Quota Failover, leave blank to skip)", password=True, default="")
    if or_key.strip():
        add_neural_key("OPENROUTER", or_key.strip())

    # 3. User Profile
    console.print("\n[bold yellow]3. User Details[/bold yellow]")
    current_name = data.get("USER", {}).get("Name", "")
    new_name = Prompt.ask("Enter your name", default=current_name or "Shubham")
    data["USER"]["Name"] = new_name.strip()

    current_email = data.get("USER", {}).get("email", "")
    new_email = Prompt.ask("Enter your email (optional)", default=current_email)
    data["USER"]["email"] = new_email.strip()

    # Save
    if save_data(data):
        console.print("\n[bold green]✅ F.R.I.D.A.Y Configuration Completed Successfully![/bold green]\n")
    else:
        console.print("\n[bold red]❌ Setup save error. Please try again.[/bold red]\n")


def interactive_config_editor():
    while True:
        data = load_data()
        neural = get_neural_keys()

        table = Table(title="⚙️ Current F.R.I.D.A.Y Configuration", box=ROUNDED)
        table.add_column("Category", style="bold cyan")
        table.add_column("Key / Provider", style="bold yellow")
        table.add_column("Value / Status", style="green")

        # Show Neural Cascade Keys
        for prov, keys in neural.items():
            count = len(keys)
            status_str = f"[bold green]{count} Key(s) Registered[/bold green]" if count else "[dim red]No Keys[/dim red]"
            table.add_row("NEURAL_CASCADE", prov, status_str)

        # Other keys
        for k, v in data.get("KEYS", {}).items():
            if k in ["LLM_KEY", "OPENROUTER_API_KEY", "PASSWORD", "AGENT_PASSWORD", "WEATHER_KEY", "TAVILY_API_KEY", "NEWS_API_KEY", "GEMINI_KEY", "GROQ_API_KEY", "HUGGINGFACE_API_KEY"]:
                display_val = "••••••••" if v else "[dim red]Not Set[/dim red]"
            else:
                display_val = str(v) if v else "[dim red]Not Set[/dim red]"
            table.add_row("KEYS", k, display_val)

        console.print(table)

        console.print("\n[bold yellow]Configuration Options:[/bold yellow]")
        console.print(" 1. Add Neural Core Key (Gemini / HuggingFace / Groq / OpenRouter)")
        console.print(" 2. Update Security Password")
        console.print(" 3. Update User Profile")
        console.print(" 4. Update External API Keys (Weather / Tavily / News)")
        console.print(" 5. Exit Config Editor")

        choice = Prompt.ask("[bold cyan]Select option (1-5)[/bold cyan]", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == "1":
            p_choice = Prompt.ask("Select Provider", choices=["GEMINI", "HUGGINGFACE", "GROQ", "OPENROUTER"])
            new_k = Prompt.ask(f"Enter {p_choice} API Key", password=True)
            if new_k.strip():
                add_neural_key(p_choice, new_k.strip())
                console.print(f"[bold green]✅ Added key to {p_choice}[/bold green]")

        elif choice == "2":
            data["KEYS"]["AGENT_PASSWORD"] = Prompt.ask("New Security Password", password=True)
            save_data(data)

        elif choice == "3":
            data["USER"]["Name"] = Prompt.ask("User Name", default=data["USER"].get("Name", ""))
            data["USER"]["email"] = Prompt.ask("Email", default=data["USER"].get("email", ""))
            data["USER"]["phone_number"] = Prompt.ask("Phone Number", default=data["USER"].get("phone_number", ""))
            save_data(data)

        elif choice == "4":
            data["KEYS"]["WEATHER_KEY"] = Prompt.ask("Weather API Key", default=data["KEYS"].get("WEATHER_KEY", ""))
            data["KEYS"]["TAVILY_API_KEY"] = Prompt.ask("Tavily Search Key", default=data["KEYS"].get("TAVILY_API_KEY", ""))
            data["KEYS"]["NEWS_API_KEY"] = Prompt.ask("News API Key", default=data["KEYS"].get("NEWS_API_KEY", ""))
            save_data(data)

        elif choice == "5":
            break


if __name__ == "__main__":
    interactive_config_editor()
