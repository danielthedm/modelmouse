"""
Progress Display - CLI progress bars and status display for benchmark runs.

Uses the rich library for beautiful terminal output.
"""
from typing import Optional, Dict, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from ..core.schemas import TestResult


class BenchmarkProgress:
    """Progress tracker for benchmark execution."""

    def __init__(self, total_tests: int, models: List[str], console: Optional[Console] = None):
        """Initialize progress tracker.

        Args:
            total_tests: Total number of test executions expected
            models: List of model IDs being tested
            console: Optional Rich console instance
        """
        self.total_tests = total_tests
        self.models = models
        self.console = console or Console()
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.current_model = None
        self.current_test = None
        self.results_by_model: Dict[str, List[TestResult]] = {model: [] for model in models}

        # Progress bar
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.task_id = None

    def start(self):
        """Start the progress display."""
        self.progress.start()
        self.task_id = self.progress.add_task(
            "[cyan]Running benchmark...",
            total=self.total_tests
        )

    def update(self, result: TestResult):
        """Update progress with a completed test result.

        Args:
            result: TestResult from a completed test
        """
        self.completed += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

        self.current_model = result.model
        self.current_test = result.test_name

        # Store result
        if result.model in self.results_by_model:
            self.results_by_model[result.model].append(result)

        # Update progress bar
        if self.task_id is not None:
            desc = f"[cyan]Testing {result.model} - {result.test_name}"
            self.progress.update(self.task_id, advance=1, description=desc)

    def stop(self):
        """Stop the progress display."""
        self.progress.stop()

    def print_summary(self):
        """Print a summary table of results."""
        table = Table(title="Benchmark Results Summary")

        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Tests", justify="right")
        table.add_column("Success", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")
        table.add_column("Avg Score", justify="right")
        table.add_column("Avg Latency", justify="right")

        for model in self.models:
            results = self.results_by_model.get(model, [])
            if not results:
                continue

            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful

            # Calculate average score
            scores = [r.overall_score for r in results if r.success and r.overall_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            # Calculate average latency
            latencies = [r.latency_ms for r in results if r.success and r.latency_ms is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            table.add_row(
                model,
                str(total),
                str(successful),
                str(failed),
                f"{avg_score:.2f}" if avg_score > 0 else "-",
                f"{avg_latency:.0f} ms" if avg_latency > 0 else "-",
            )

        self.console.print("\n")
        self.console.print(table)


class LiveBenchmarkDisplay:
    """Live updating display for benchmark execution.

    Shows real-time progress with current status and a results summary table.
    """

    def __init__(self, total_tests: int, models: List[str], console: Optional[Console] = None):
        """Initialize live display.

        Args:
            total_tests: Total number of test executions expected
            models: List of model IDs being tested
            console: Optional Rich console instance
        """
        self.total_tests = total_tests
        self.models = models
        self.console = console or Console()
        self.completed = 0
        self.successful = 0
        self.failed = 0
        self.current_model = None
        self.current_test = None
        self.results_by_model: Dict[str, List[TestResult]] = {model: [] for model in models}
        self.live = None
        self.layout = None

    def _generate_layout(self) -> Layout:
        """Generate the layout for display."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )

        # Header with overall progress
        progress_pct = (self.completed / self.total_tests * 100) if self.total_tests > 0 else 0
        header_text = Text()
        header_text.append(f"Progress: {self.completed}/{self.total_tests} ", style="bold cyan")
        header_text.append(f"({progress_pct:.1f}%) ", style="cyan")
        header_text.append(f"✓ {self.successful} ", style="green")
        header_text.append(f"✗ {self.failed}", style="red")

        if self.current_model and self.current_test:
            header_text.append(f"\nTesting: ", style="bold")
            header_text.append(f"{self.current_model}", style="yellow")
            header_text.append(f" - {self.current_test}", style="dim")

        layout["header"].update(Panel(header_text, border_style="blue"))

        # Body with results table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan")
        table.add_column("Tests", justify="right")
        table.add_column("✓", justify="right", style="green")
        table.add_column("✗", justify="right", style="red")
        table.add_column("Avg Score", justify="right")
        table.add_column("Avg Latency", justify="right")

        for model in self.models:
            results = self.results_by_model.get(model, [])
            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful

            if total == 0:
                table.add_row(model, "-", "-", "-", "-", "-")
                continue

            # Calculate average score
            scores = [r.overall_score for r in results if r.success and r.overall_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            # Calculate average latency
            latencies = [r.latency_ms for r in results if r.success and r.latency_ms is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Style based on completion
            style = "dim" if total < (self.total_tests / len(self.models)) else "bold"

            table.add_row(
                model,
                str(total),
                str(successful),
                str(failed),
                f"{avg_score:.2f}" if avg_score > 0 else "-",
                f"{avg_latency:.0f} ms" if avg_latency > 0 else "-",
                style=style,
            )

        layout["body"].update(table)
        return layout

    def start(self):
        """Start the live display."""
        self.layout = self._generate_layout()
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.live.start()

    def update(self, result: TestResult):
        """Update display with a completed test result.

        Args:
            result: TestResult from a completed test
        """
        self.completed += 1
        if result.success:
            self.successful += 1
        else:
            self.failed += 1

        self.current_model = result.model
        self.current_test = result.test_name

        # Store result
        if result.model in self.results_by_model:
            self.results_by_model[result.model].append(result)

        # Update layout
        if self.live:
            self.layout = self._generate_layout()
            self.live.update(self.layout)

    def stop(self):
        """Stop the live display."""
        if self.live:
            self.live.stop()

    def print_final_summary(self):
        """Print final summary with rankings."""
        self.console.print("\n")
        self.console.print("[bold green]✓ Benchmark Complete![/bold green]\n")

        # Overall stats
        self.console.print(f"[bold]Total Tests:[/bold] {self.completed}")
        self.console.print(f"[green]Successful:[/green] {self.successful}")
        self.console.print(f"[red]Failed:[/red] {self.failed}")
        self.console.print()

        # Rankings by score
        model_scores = {}
        for model, results in self.results_by_model.items():
            successful_results = [r for r in results if r.success]
            if successful_results:
                scores = [r.overall_score for r in successful_results if r.overall_score is not None]
                if scores:
                    model_scores[model] = sum(scores) / len(scores)

        if model_scores:
            sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)

            rank_table = Table(title="Model Rankings by Score", show_header=True)
            rank_table.add_column("Rank", justify="right", style="cyan")
            rank_table.add_column("Model", style="yellow")
            rank_table.add_column("Avg Score", justify="right", style="green")

            for i, (model, score) in enumerate(sorted_models, 1):
                rank_style = "bold" if i == 1 else ""
                rank_table.add_row(str(i), model, f"{score:.2f}", style=rank_style)

            self.console.print(rank_table)


def create_progress_callback(display: BenchmarkProgress) -> callable:
    """Create a callback function for progress updates.

    Args:
        display: BenchmarkProgress or LiveBenchmarkDisplay instance

    Returns:
        Callback function that can be passed to executor
    """
    def callback(result: TestResult):
        display.update(result)

    return callback
