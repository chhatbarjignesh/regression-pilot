"""
CLI — run the server or trigger a manual heal from the command line.
"""
from __future__ import annotations
import json
import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from agent.models import Framework, TestFailure

app = typer.Typer(help="RegressionPilot — AI self-healing test agent")
console = Console()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, help="Hot reload for development"),
):
    """Start the RegressionPilot webhook server."""
    console.print("[bold green]Starting RegressionPilot server...[/bold green]")
    uvicorn.run("agent.server:app", host=host, port=port, reload=reload)


@app.command()
def heal(
    test_name: str = typer.Option(..., help="Name of the failing test"),
    test_file: str = typer.Option(..., help="Relative path to test file"),
    framework: str = typer.Option("playwright", help="playwright or selenium"),
    error: str = typer.Option(..., help="Error message from the failure"),
    stack: str = typer.Option("", help="Stack trace"),
    repo: str = typer.Option(".", help="Local repo path"),
    branch: str = typer.Option("main", help="Current branch"),
    commit: str = typer.Option("HEAD", help="Commit SHA"),
    page_url: str = typer.Option("", help="URL of the page under test"),
):
    """Manually trigger a heal cycle for a specific test failure."""
    from agent.orchestrator import Orchestrator

    failure = TestFailure(
        test_name=test_name,
        test_file=test_file,
        framework=Framework(framework),
        error_message=error,
        stack_trace=stack,
        repo_path=repo,
        branch=branch,
        commit_sha=commit,
        run_id="cli",
    )

    console.print(f"[bold]Healing:[/bold] {test_name}")
    orchestrator = Orchestrator()
    result = orchestrator.heal(failure, page_url)

    table = Table(title="Heal Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Status", result.status.value)
    table.add_row("Failure type", result.failure_type.value)
    table.add_row("Jira ticket", result.jira_ticket_key or "—")
    table.add_row("PR URL", result.pr_url or "—")
    table.add_row("Commit", result.commit_sha or "—")
    table.add_row("Confidence", f"{result.fix.confidence:.0%}" if result.fix else "—")
    table.add_row("Time saved", f"{result.time_saved_minutes:.0f} min")
    console.print(table)


if __name__ == "__main__":
    app()
