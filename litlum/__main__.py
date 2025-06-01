"""Main entry point for the LitLum application."""

import sys
from litlum.ui.cli import CLI


def main(args=None):
    """Run the LitLum application.
    
    Args:
        args: Command line arguments. If None, uses sys.argv[1:]
    """
    if args is None:
        args = sys.argv[1:]
    
    # If no arguments provided, show help
    if not args:
        args = ["--help"]
        
    cli = CLI()
    cli.run(args)


if __name__ == "__main__":
    main()
