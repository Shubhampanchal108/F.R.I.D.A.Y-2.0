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

from path import DOCS_PATH
from utiles import Default_Data, search

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
        console.print(f"\n[bold yellow]⚠️ Missing Configuration Key: [{parKey}][{childKey}][/bold yellow]")
        val = Prompt.ask(f"[bold cyan]Please provide value for {childKey}[/bold cyan]")
        if val:
            update_config(parKey, childKey, val.strip())
            return val.strip()

    return val


def is_agent_configured():
    data = load_data()
    llm_key = data.get("KEYS", {}).get("LLM_KEY", "")
    llm_url = data.get("LLM", {}).get("LLM_SERVICE_PROVIDER_URL", "")
    password = data.get("KEYS", {}).get("AGENT_PASSWORD", "")
    return bool(llm_key and llm_url and password)


def run_first_time_setup():
    console.clear()
    setup_panel = Panel(
        "[bold cyan]Welcome to F.R.I.D.A.Y 3.0 Setup Wizard![/bold cyan]\n\n"
        "[white]It looks like this is your first time running F.R.I.D.A.Y on this machine.\n"
        "Please provide the required configuration keys to activate your AI Agent.[/white]",
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

    # 2. LLM Provider Settings
    console.print("\n[bold yellow]2. LLM Provider Configuration[/bold yellow]")
    current_url = data.get("LLM", {}).get("LLM_SERVICE_PROVIDER_URL", "")
    new_url = Prompt.ask(
        "LLM Service Provider Base URL",
        default=current_url or "https://openrouter.ai/api/v1"
    )
    data["LLM"]["LLM_SERVICE_PROVIDER_URL"] = new_url.strip()

    current_key = data.get("KEYS", {}).get("LLM_KEY", "")
    new_key = Prompt.ask("Enter your LLM API Key (OpenAI / OpenRouter / Groq)", password=True, default=current_key)
    data["KEYS"]["LLM_KEY"] = new_key.strip()

    current_model = data.get("LLM", {}).get("MODEL", "")
    new_model = Prompt.ask(
        "Enter Model Name",
        default=current_model or "openai/gpt-4o-mini"
    )
    data["LLM"]["MODEL"] = new_model.strip()

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

        table = Table(title="⚙️ Current F.R.I.D.A.Y Configuration", box=ROUNDED)
        table.add_column("Category", style="bold cyan")
        table.add_column("Key", style="bold yellow")
        table.add_column("Value / Status", style="green")

        # Mask sensitive keys
        for category, keys in data.items():
            for k, v in keys.items():
                if k in ["LLM_KEY", "PASSWORD", "AGENT_PASSWORD", "WEATHER_KEY", "TAVILY_API_KEY", "NEWS_API_KEY"]:
                    display_val = "••••••••" if v else "[dim red]Not Set[/dim red]"
                else:
                    display_val = str(v) if v else "[dim red]Not Set[/dim red]"
                table.add_row(category, k, display_val)

        console.print(table)

        console.print("\n[bold yellow]Configuration Options:[/bold yellow]")
        console.print(" 1. Update LLM Provider & Key")
        console.print(" 2. Update Security Password")
        console.print(" 3. Update User Profile")
        console.print(" 4. Update External API Keys (Weather / Tavily / News)")
        console.print(" 5. Exit Config Editor")

        choice = Prompt.ask("[bold cyan]Select option (1-5)[/bold cyan]", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == "1":
            data["LLM"]["LLM_SERVICE_PROVIDER_URL"] = Prompt.ask("LLM Provider Base URL", default=data["LLM"].get("LLM_SERVICE_PROVIDER_URL", ""))
            data["KEYS"]["LLM_KEY"] = Prompt.ask("LLM API Key", password=True, default=data["KEYS"].get("LLM_KEY", ""))
            data["LLM"]["MODEL"] = Prompt.ask("Model Name", default=data["LLM"].get("MODEL", ""))
            save_data(data)

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