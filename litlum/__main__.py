"""Main entry point for the LitLum application."""

import sys
from litlum.ui.cli import CLI


def main():
    """Run the LitLum application."""
    cli = CLI()
    cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()
