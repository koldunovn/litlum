"""Command line interface for the LitLum application."""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

from litlum.config import Config
from litlum.db.database import Database
from litlum.feeds.parser import FeedParser
from litlum.llm.analyzer import OllamaAnalyzer
from litlum.reports.generator import ReportGenerator
from litlum.web.static_site_generator import StaticSiteGenerator


class CLI:
    """Command line interface for the LitLum application."""
    
    def __init__(self):
        """Initialize the CLI interface."""
        self.console = Console()
        self.config = Config()
        self.db = Database(self.config.get_database_path())
        self.feed_parser = FeedParser()
        self.ollama_analyzer = OllamaAnalyzer(self.config.get_ollama_config())
        self.report_generator = ReportGenerator(
            reports_path=self.config.get_reports_path(),
            min_relevance=self.config.get_min_relevance()
        )
        # Initialize the static site generator
        self.site_generator = StaticSiteGenerator(
            reports_path=self.config.get_reports_path(),
            output_path=self.config.get_web_path()
        )
    
    def run(self, args: Optional[List[str]] = None) -> None:
        """Run the CLI application.
        
        Args:
            args: Command line arguments
        """
        parser = self._create_argument_parser()
        parsed_args = parser.parse_args(args)
        
        # Process command
        command = parsed_args.command
        
        if command == 'fetch':
            self._handle_fetch(parsed_args)
        elif command == 'analyze':
            self._handle_analyze(parsed_args)
        elif command == 'report':
            self._handle_report(parsed_args)
        elif command == 'list':
            self._handle_list(parsed_args)
        elif command == 'show':
            self._handle_show(parsed_args)
        elif command == 'run':
            self._handle_run(parsed_args)
        elif command == 'reset':
            self._handle_reset(parsed_args)
        elif command == 'web':
            self._handle_web(parsed_args)
        else:
            # Default to showing help
            parser.print_help()
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for CLI commands.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description='LitLum - Monitor and analyze scientific publications'
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command')
        
        # Fetch command
        fetch_parser = subparsers.add_parser('fetch', help='Fetch publications from RSS feeds')
        
        # Analyze command
        analyze_parser = subparsers.add_parser('analyze', help='Analyze unprocessed publications')
        analyze_parser.add_argument('--reanalyze', action='store_true', help='Reanalyze already processed publications')
        analyze_parser.add_argument('--date', help='Analyze publications from a specific date (YYYY-MM-DD)')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Generate or display reports')
        report_parser.add_argument('--date', help='Report date (YYYY-MM-DD, defaults to today)')
        report_parser.add_argument('--generate', action='store_true', help='Generate a new report')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List reports or publications')
        list_parser.add_argument('--reports', action='store_true', help='List available reports')
        list_parser.add_argument('--publications', action='store_true', help='List recent publications')
        list_parser.add_argument('--days', type=int, default=7, help='Number of days to look back (default: 7)')
        list_parser.add_argument('--min-relevance', type=int, default=0, help='Minimum relevance score (0-10)')
        
        # Show command
        show_parser = subparsers.add_parser('show', help='Show publication details')
        show_parser.add_argument('id', type=int, help='Publication ID')
        
        # Run command - performs fetch, analyze, report in sequence
        run_parser = subparsers.add_parser('run', help='Run the full workflow: fetch, analyze, and report')
        run_parser.add_argument('--serve', action='store_true', help='Start a local web server after generating the site')
        run_parser.add_argument('--reanalyze', action='store_true', help='Reanalyze already processed publications')
        
        # Reset command
        reset_parser = subparsers.add_parser('reset', help='Reset the LitLum application')
        reset_parser.add_argument('--force', action='store_true', help='Force reset without confirmation')
        reset_parser.add_argument('--keep-config', action='store_true', help='Keep configuration files')
        
        # Web command
        web_parser = subparsers.add_parser('web', help='Generate static website from reports')
        web_parser.add_argument('--serve', action='store_true', help='Start a local web server to preview the site')
        
        return parser
    
    def _handle_fetch(self, args: argparse.Namespace) -> None:
        """Handle the fetch command.
        
        Args:
            args: Parsed arguments
        """
        feeds = self.config.get_feeds()
        
        if not feeds:
            self.console.print("[bold red]No feeds configured.[/bold red]")
            return
        
        self.console.print(f"[bold]Fetching publications from all feeds[/bold]")
        
        import time
        from datetime import timedelta
        
        total_new = 0
        
        # Track time for estimation
        start_time = time.time()
        processed_count = 0
        total_count = len(feeds)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[cyan]({task.completed}/{task.total})"),
            TextColumn("[yellow]Remaining: {task.remaining}"),
            TextColumn("[green]Est: {task.fields[est_time]}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Fetching publications from {total_count} feeds...", 
                total=total_count,
                est_time="calculating..."
            )
            
            for feed_config in feeds:
                feed_name = feed_config.get('name', 'Unknown')
                progress.update(task, description=f"Fetching from {feed_name}...")
                
                # Measure time for this feed
                feed_start_time = time.time()
                
                # Parse feed
                publications = self.feed_parser.parse_feed(feed_config)
                
                # Add to database
                new_count = 0
                for pub in publications:
                    if self.db.add_publication(pub):
                        new_count += 1
                
                total_new += new_count
                
                # Update time metrics
                feed_elapsed = time.time() - feed_start_time
                processed_count += 1
                
                # Calculate average time per feed and estimate remaining time
                if processed_count > 0:
                    avg_time_per_feed = (time.time() - start_time) / processed_count
                    remaining_feeds = total_count - processed_count
                    est_remaining_seconds = avg_time_per_feed * remaining_feeds
                    
                    # Format as hours:minutes:seconds
                    est_remaining = str(timedelta(seconds=int(est_remaining_seconds)))
                    
                    # Update progress with estimated time
                    progress.update(task, est_time=est_remaining)
                
                progress.advance(task)
        
        self.console.print(f"[bold green]Fetch complete. {total_new} new publications added.[/bold green]")
    
    def _handle_analyze(self, args: argparse.Namespace) -> None:
        """Handle the analyze command.
        
        Args:
            args: Parsed arguments
        """
        # Get publications to analyze
        if args.date:
            try:
                date_obj = datetime.strptime(args.date, '%Y-%m-%d')
                date_str = date_obj.strftime('%Y-%m-%d')
                
                if args.reanalyze:
                    # Get all publications from date for reanalysis
                    publications = self.db.get_publications_by_date(date_str)
                    self.console.print(f"[bold]Reanalyzing {len(publications)} publications from {date_str}...[/bold]")
                else:
                    # Filter to only unprocessed publications
                    publications = self.db.get_publications_by_date(date_str)
                    publications = [p for p in publications if p.get('relevance_score') is None]
                    self.console.print(f"[bold]Analyzing {len(publications)} unprocessed publications from {date_str}...[/bold]")
            except ValueError:
                self.console.print("[bold red]Invalid date format. Use YYYY-MM-DD.[/bold red]")
                return
        else:
            if args.reanalyze:
                # Get all publications for reanalysis
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id, journal, title, abstract, url, pub_date, guid FROM publications')
                publications = [dict(row) for row in cursor.fetchall()]
                self.console.print(f"[bold]Reanalyzing {len(publications)} publications...[/bold]")
            else:
                # Only get unprocessed publications
                publications = self.db.get_unprocessed_publications()
                self.console.print(f"[bold]Analyzing {len(publications)} unprocessed publications...[/bold]")
        
        if not publications:
            self.console.print("[bold yellow]No publications to analyze.[/bold yellow]")
            return
        
        # Analyze publications
        import time
        from datetime import timedelta
        
        # Track time for estimation
        start_time = time.time()
        processed_count = 0
        total_count = len(publications)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[cyan]({task.completed}/{task.total})"),
            TextColumn("[yellow]Remaining: {task.remaining}"),
            TextColumn("[green]Est: {task.fields[est_time]}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"Analyzing publications...", 
                total=total_count,
                est_time="calculating..."
            )
            
            for i, pub in enumerate(publications):
                pub_title = pub.get('title', '')[:40]
                progress.update(
                    task, 
                    description=f"Analyzing: {pub_title}..."
                )
                
                # Measure time for this publication
                pub_start_time = time.time()
                
                # Process the publication
                relevance_score, summary = self.ollama_analyzer.analyze_publication(pub)
                self.db.update_publication_analysis(pub['id'], relevance_score, summary)
                
                # Update time metrics
                pub_elapsed = time.time() - pub_start_time
                processed_count += 1
                
                # Calculate average time per publication and estimate remaining time
                if processed_count > 0:
                    avg_time_per_pub = (time.time() - start_time) / processed_count
                    remaining_pubs = total_count - processed_count
                    est_remaining_seconds = avg_time_per_pub * remaining_pubs
                    
                    # Format as hours:minutes:seconds
                    est_remaining = str(timedelta(seconds=int(est_remaining_seconds)))
                    
                    # Update progress with estimated time
                    progress.update(task, est_time=est_remaining)
                
                progress.advance(task)
        
        self.console.print(f"[bold green]Analysis complete. {len(publications)} publications analyzed.[/bold green]")
    
    def _handle_report(self, args: argparse.Namespace) -> None:
        """Handle the report command.
        
        Args:
            args: Parsed arguments
        """
        date_str = args.date or datetime.now().strftime('%Y-%m-%d')
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            self.console.print("[bold red]Invalid date format. Use YYYY-MM-DD.[/bold red]")
            return
        
        # Generate new report if requested
        if args.generate:
            # Get the min_relevance from the report generator
            min_relevance = self.report_generator.min_relevance
            
            # Get publications with minimum relevance score
            publications = self.db.get_publications_by_date(date_str, min_relevance)
            
            if not publications:
                self.console.print(
                    f"[bold yellow]No publications found for {date_str} "
                    f"with relevance >= {min_relevance}.[/bold yellow]"
                )
                return
            
            self.console.print(
                f"[bold]Generating report for {date_str} with "
                f"min_relevance={min_relevance}...[/bold]"
            )
            report_data = self.report_generator.generate_daily_report(publications, date_str)
            
            # Extract the summary text from the report dictionary
            summary_text = report_data.get('summary', '')
            self.db.save_daily_summary(date_str, summary_text)
            
            self.console.print(f"[bold green]Report generated for {date_str}.[/bold green]")
        
        # Display the report (whether newly generated or existing)
        report = self.report_generator.get_report(date_str)
        
        if not report:
            self.console.print(f"[bold yellow]No report found for {date_str}. Run with --generate to create one.[/bold yellow]")
            return
        
        self.report_generator.display_report(date_str)
    
    def _handle_list(self, args: argparse.Namespace) -> None:
        """Handle the list command.
        
        Args:
            args: Parsed arguments
        """
        if args.reports:
            # List reports
            reports = self.report_generator.list_reports()
            
            if not reports:
                self.console.print("[bold yellow]No reports found.[/bold yellow]")
                return
            
            table = Table(title="Available Reports")
            table.add_column("Date", style="cyan")
            
            for report_date in reports:
                table.add_row(report_date)
            
            self.console.print(table)
        
        elif args.publications:
            # List publications
            days = args.days or 7
            min_relevance = args.min_relevance or 0
            
            publications = self.db.get_recent_publications(days, min_relevance)
            
            if not publications:
                self.console.print(f"[bold yellow]No publications found in the last {days} days with minimum relevance {min_relevance}.[/bold yellow]")
                return
            
            table = Table(title=f"Recent Publications (Last {days} days, Min Relevance: {min_relevance})")
            table.add_column("ID", style="dim")
            table.add_column("Date", style="cyan")
            table.add_column("Journal", style="blue")
            table.add_column("Title", style="green")
            table.add_column("Relevance", justify="center", style="magenta")
            
            for pub in publications:
                table.add_row(
                    str(pub.get('id', '')),
                    pub.get('pub_date', '')[:10] if pub.get('pub_date') else '',
                    pub.get('journal', ''),
                    pub.get('title', ''),
                    f"{pub.get('relevance_score', 0)}/10"
                )
            
            self.console.print(table)
        
        else:
            self.console.print("[bold yellow]Please specify what to list (--reports or --publications)[/bold yellow]")
    
    def _handle_show(self, args: argparse.Namespace) -> None:
        """Handle the show command.
        
        Args:
            args: Parsed arguments
        """
        pub_id = args.id
        
        # Get publication from database
        cursor = self.db.conn.cursor()
        cursor.execute('''
        SELECT id, journal, title, abstract, url, pub_date, guid, relevance_score, llm_summary
        FROM publications
        WHERE id = ?
        ''', (pub_id,))
        row = cursor.fetchone()
        
        if not row:
            self.console.print(f"[bold red]Publication with ID {pub_id} not found.[/bold red]")
            return
        
        publication = dict(row)
        self.report_generator.display_publication_details(publication)
    
    def _handle_reset(self, args: argparse.Namespace) -> None:
        """Handle the reset command.
        
        Args:
            args: Parsed arguments
        """
        if not args.force:
            confirm = Confirm.ask("\n[bold red]WARNING: This will delete all publications and reports. Continue?[/bold red]")
            if not confirm:
                self.console.print("Reset cancelled.")
                return
        
        # Close the current connection
        self.db.close()
        
        # Get db path
        db_path = self.config.get_database_path()
        
        # Delete the database file
        if os.path.exists(db_path):
            os.remove(db_path)
            self.console.print(f"[bold green]Database deleted: {db_path}[/bold green]")
        
        # Delete report files if they exist
        if not args.keep_config:
            reports_path = self.config.get_reports_path()
            if os.path.exists(reports_path):
                for file in os.listdir(reports_path):
                    if file.startswith("report_") and file.endswith(".json"):
                        os.remove(os.path.join(reports_path, file))
                self.console.print(f"[bold green]Report files deleted from: {reports_path}[/bold green]")
        
        # Reconnect to create a fresh database
        self.db = Database(self.config.get_database_path())
        self.console.print("[bold green]Database reset complete. Fresh database created.[/bold green]")
    
    def _handle_run(self, args: argparse.Namespace) -> None:
        """Handle the run command.
        
        Args:
            args: Parsed arguments
        """
        # Fetch publications
        self.console.print("[bold]Step 1: Fetching publications...[/bold]")
        self._handle_fetch(args)
        
        # Analyze publications
        self.console.print("\n[bold]Step 2: Analyzing publications...[/bold]")
        analyze_args = argparse.Namespace(date=None, reanalyze=False)
        self._handle_analyze(analyze_args)
        
        # Generate report
        self.console.print("\n[bold]Step 3: Generating report...[/bold]")
        report_args = argparse.Namespace(date=None, generate=True)
        self._handle_report(report_args)
        
        # Generate static website
        self.console.print("\n[bold]Step 4: Generating static website...[/bold]")
        web_args = argparse.Namespace(serve=getattr(args, 'serve', False))
        self._handle_web(web_args)
        
    def _handle_web(self, args: argparse.Namespace) -> None:
        """Handle the web command.
        
        Args:
            args: Parsed arguments
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Generating static website..."),
            transient=True,
        ) as progress:
            progress.add_task("Generating", total=None)
            self.site_generator.generate_site()
        
        self.console.print(f"[bold green]Static website generated at: {self.config.get_web_path()}[/bold green]")
        
        # Start a local web server if requested
        if args.serve:
            import http.server
            import socketserver
            import threading
            import webbrowser
            
            web_path = self.config.get_web_path()
            port = 8000
            
            self.console.print(f"\n[bold]Starting local web server on port {port}...[/bold]")
            self.console.print(f"[bold blue]Open your browser at: http://localhost:{port}[/bold blue]")
            self.console.print("Press Ctrl+C to stop the server.\n")
            
            # Change to the web directory
            os.chdir(web_path)
            
            # Open browser after a short delay
            threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
            
            # Start the server
            Handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("localhost", port), Handler)
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                self.console.print("\n[bold]Web server stopped.[/bold]")
            finally:
                httpd.server_close()
