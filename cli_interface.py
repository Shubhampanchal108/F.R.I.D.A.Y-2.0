import os
import sys
import time
import platform
import multiprocessing
from datetime import datetime

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.spinner import Spinner
from rich import box

# Parent path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Tools.systems_tools import get_battery_status, get_cpu_status
from Tools.reminder import list_reminders
from path import CONTENT_PATH

console = Console()

ASCII_ART = """[bold cyan]
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗           ║
║   ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝           ║
║   █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝            ║
║   ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝             ║
║   ██║     ██║  ██║██║██████╔╝██║  ██║   ██║              ║
║   ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝              ║
║                                                          ║
║   ⚡ Friendly Reliable Intelligent Digital Assistant ⚡   ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]"""

class FridayCLI:
    def __init__(self, daemon=None):
        self.daemon = daemon
        self.vocal_protocol = False
        self.type_protocol = True
        self.audio_drive = True
        self.authenticated = False

    def print_banner(self):
        console.clear()
        
        mode_str = "[bold green]🎙️ VOICE[/bold green]" if self.vocal_protocol else "[bold yellow]⌨️ TYPING[/bold yellow]"
        audio_str = "[bold green]🔊 ON[/bold green]" if self.audio_drive else "[bold red]🔇 OFF[/bold red]"
        daemon_str = "[bold green]🟢 ACTIVE[/bold green]" if (self.daemon and self.daemon.is_running()) else "[bold red]🔴 OFF[/bold red]"

        # Subsystem Status Matrix
        hud_table = Table.grid(expand=True)
        hud_table.add_column(justify="center", ratio=1)
        hud_table.add_column(justify="center", ratio=1)
        hud_table.add_column(justify="center", ratio=1)
        hud_table.add_row(
            f"[bold cyan]Input Mode:[/bold cyan] {mode_str}",
            f"[bold cyan]Audio Drive:[/bold cyan] {audio_str}",
            f"[bold cyan]Daemon Watchdog:[/bold cyan] {daemon_str}"
        )

        # Specs grid
        specs_grid = Table.grid(expand=True)
        specs_grid.add_column(justify="left", style="dim white")
        specs_grid.add_column(justify="right", style="cyan")
        specs_grid.add_row(
            f"👤 Creator: [bold yellow]Shubham[/bold yellow]  │  OS: {platform.system()} {platform.release()}",
            f"🧠 Neural Path: [dim]{CONTENT_PATH}[/dim]"
        )

        content = Group(
            Align.center(Text.from_markup(ASCII_ART)),
            specs_grid,
            Text("─" * 60, style="dim cyan"),
            hud_table
        )

        main_panel = Panel(
            content,
            box=box.DOUBLE,
            border_style="cyan",
            title="[bold bright_blue]⚡ F.R.I.D.A.Y 4.0 — NEXT-GEN SUPER-AGENT HUD ⚡[/bold bright_blue]",
            subtitle="[dim]Type [bold yellow]/help[/bold yellow] for shortcuts │ [bold cyan]Version 4.0 Super-Agent[/bold cyan][/dim]"
        )
        console.print(main_panel)

    def print_help(self):
        help_table = Table(title="🤖 F.R.I.D.A.Y 4.0 CLI Command Palette", box=box.ROUNDED)
        help_table.add_column("Command", style="bold yellow")
        help_table.add_column("Description", style="white")

        help_table.add_row("/voice", "Switch to Voice Recognition Mode")
        help_table.add_row("/type", "Switch to Typing Mode")
        help_table.add_row("/audio", "Toggle Speech Audio Drive ON/OFF")
        help_table.add_row("/briefing", "Trigger Proactive Voice & Desktop Morning Briefing")
        help_table.add_row("/wakeword", "Toggle Hands-Free Background Wake-Word Detection")
        help_table.add_row("/status", "Display Full System Specs & Health Status HUD")
        help_table.add_row("/reminders", "Show Pending & Active Reminders")
        help_table.add_row("/config", "Open Dynamic Configuration Editor Wizard")
        help_table.add_row("/clear", "Clear Terminal Screen")
        help_table.add_row("/exit", "Shutdown F.R.I.D.A.Y CLI Agent")
        
        console.print(help_table)

    def show_status(self):
        batt = get_battery_status()
        batt_str = f"{batt.get('battery_percentage', 'N/A')}% ({batt.get('status', 'Unknown')})" if isinstance(batt, dict) else str(batt)
        
        cpu_info = get_cpu_status()
        cpu_usage = f"{cpu_info.get('cpu_usage_percent', 'N/A')}%" if isinstance(cpu_info, dict) else "N/A"
        cpu_cores = f"{cpu_info.get('logical_cores', multiprocessing.cpu_count())} Cores" if isinstance(cpu_info, dict) else f"{multiprocessing.cpu_count()} Cores"

        reminders_data = list_reminders()
        rem_count = len(reminders_data.get("reminders", [])) if isinstance(reminders_data, dict) else 0

        status_panel = Table(title="💻 F.R.I.D.A.Y Core System Health HUD", box=box.DOUBLE)
        status_panel.add_column("Subsystem Metric", style="bold cyan")
        status_panel.add_column("Status / Value", style="bold green")

        status_panel.add_row("Host OS", f"{platform.system()} {platform.release()} ({platform.machine()})")
        status_panel.add_row("CPU Core Threads", cpu_cores)
        status_panel.add_row("Current CPU Usage", cpu_usage)
        status_panel.add_row("Battery Level", batt_str)
        status_panel.add_row("Vector RAG Memory", "ChromaDB (Active) 🧠")
        status_panel.add_row("Permission Layer Guard", "Enforced (Server/Mobile/Web ACL) 🔐")
        status_panel.add_row("Active Reminders Count", f"{rem_count} Reminders")
        
        if self.daemon:
            status_panel.add_row("Background Daemon Watchdog", "Running 🟢" if self.daemon.is_running() else "Stopped 🔴")
            status_panel.add_row("Recent Daemon Event Logs", f"{len(self.daemon.notification_history)} Events Logged")

        console.print(status_panel)

        if self.daemon and self.daemon.notification_history:
            log_table = Table(title="🔔 Recent Daemon Alerts & Reminders", box=box.ROUNDED)
            log_table.add_column("Time", style="dim cyan")
            log_table.add_column("Title", style="bold yellow")
            log_table.add_column("Message", style="white")
            for item in self.daemon.notification_history[-5:]:
                log_table.add_row(item["timestamp"], item["title"], item["message"])
            console.print(log_table)

    def show_reminders(self):
        data = list_reminders()
        reminders = data.get("reminders", []) if isinstance(data, dict) else []

        if not reminders:
            console.print("[bold yellow]No active reminders found, Sir.[/bold yellow]")
            return

        table = Table(title="⏰ Active Reminders", box=box.ROUNDED)
        table.add_column("ID", style="dim", justify="right")
        table.add_column("Reminder", style="bold white")
        table.add_column("Remind At", style="cyan")
        table.add_column("Status", style="green")

        for r in reminders:
            status_str = "✅ Completed" if r.get("done") else "⏳ Pending"
            table.add_row(str(r.get("id")), r.get("reminder"), r.get("remind_at"), status_str)

        console.print(table)

    def print_agent_thought(self, message: str):
        console.print(f"[dim cyan]🔧 {message}[/dim cyan]")

    def render_agent_response(self, response_text: str):
        md = Markdown(response_text)
        panel = Panel(
            md,
            title="[bold cyan]🤖 F.R.I.D.A.Y[/bold cyan]",
            border_style="bold cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        console.print(panel)

    def render_user_prompt(self, prompt_text: str):
        console.print(f"\n[bold green]👤 You:[/bold green] {prompt_text}")

    def spinner_task(self, task_name="F.R.I.D.A.Y Processing & Executing Tools..."):
        return console.status(f"[bold cyan]{task_name}[/bold cyan]", spinner="dots")


if __name__ == "__main__":
    cli = FridayCLI()
    cli.print_banner()
    cli.render_agent_response("Good day, Sir! Cyberpunk HUD interface initialized.")
