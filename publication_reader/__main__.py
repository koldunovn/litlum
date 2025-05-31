"""Main entry point for the publication reader application."""

import sys
from publication_reader.ui.cli import CLI


def main():
    """Run the publication reader application."""
    cli = CLI()
    cli.run(sys.argv[1:])


if __name__ == "__main__":
    main()
