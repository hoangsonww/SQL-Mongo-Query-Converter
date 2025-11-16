"""
Command-line interface for SQL-Mongo Query Converter.

Provides a CLI tool for converting queries interactively or in batch mode.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional
try:
    from colorama import init, Fore, Style
    init()
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

from . import sql_to_mongo, mongo_to_sql
from .validator import QueryValidator
from .logger import get_logger, ConverterLogger
from .exceptions import ConverterError
import logging


def colorize(text: str, color: str) -> str:
    """Colorize text if colorama is available."""
    if not COLORS_AVAILABLE:
        return text

    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'blue': Fore.BLUE,
        'cyan': Fore.CYAN,
        'magenta': Fore.MAGENTA,
    }

    return f"{colors.get(color, '')}{text}{Style.RESET_ALL if COLORS_AVAILABLE else ''}"


def print_success(message: str):
    """Print a success message."""
    print(colorize(f"✓ {message}", 'green'))


def print_error(message: str):
    """Print an error message."""
    print(colorize(f"✗ Error: {message}", 'red'), file=sys.stderr)


def print_warning(message: str):
    """Print a warning message."""
    print(colorize(f"⚠ Warning: {message}", 'yellow'))


def print_info(message: str):
    """Print an info message."""
    print(colorize(message, 'cyan'))


def convert_sql_to_mongo_cmd(args):
    """Handle SQL to MongoDB conversion command."""
    logger = get_logger('cli')

    try:
        # Read query
        if args.query:
            sql_query = args.query
        elif args.file:
            sql_query = Path(args.file).read_text().strip()
        else:
            print_error("Either --query or --file must be specified")
            return 1

        # Validate if requested
        if args.validate:
            print_info("Validating SQL query...")
            QueryValidator.validate_sql_query(sql_query)
            print_success("Query validation passed")

        # Convert
        print_info("Converting SQL to MongoDB...")
        result = sql_to_mongo(sql_query)

        # Output
        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2))
            print_success(f"Result written to {args.output}")
        else:
            print_info("\nMongoDB Query:")
            print(json.dumps(result, indent=2))

        print_success("Conversion completed successfully")
        return 0

    except ConverterError as e:
        print_error(str(e))
        if args.verbose:
            logger.exception("Conversion failed")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        if args.verbose:
            logger.exception("Unexpected error during conversion")
        return 1


def convert_mongo_to_sql_cmd(args):
    """Handle MongoDB to SQL conversion command."""
    logger = get_logger('cli')

    try:
        # Read query
        if args.query:
            mongo_query = json.loads(args.query)
        elif args.file:
            mongo_query = json.loads(Path(args.file).read_text())
        else:
            print_error("Either --query or --file must be specified")
            return 1

        # Validate if requested
        if args.validate:
            print_info("Validating MongoDB query...")
            QueryValidator.validate_mongo_query(mongo_query)
            print_success("Query validation passed")

        # Convert
        print_info("Converting MongoDB to SQL...")
        result = mongo_to_sql(mongo_query)

        # Output
        if args.output:
            Path(args.output).write_text(result)
            print_success(f"Result written to {args.output}")
        else:
            print_info("\nSQL Query:")
            print(result)

        print_success("Conversion completed successfully")
        return 0

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {str(e)}")
        return 1
    except ConverterError as e:
        print_error(str(e))
        if args.verbose:
            logger.exception("Conversion failed")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        if args.verbose:
            logger.exception("Unexpected error during conversion")
        return 1


def interactive_mode(args):
    """Run interactive conversion mode."""
    print_info("=" * 60)
    print_info("SQL-Mongo Query Converter - Interactive Mode")
    print_info("=" * 60)
    print_info("Commands:")
    print_info("  sql <query>   - Convert SQL to MongoDB")
    print_info("  mongo <json>  - Convert MongoDB to SQL")
    print_info("  quit/exit     - Exit interactive mode")
    print_info("=" * 60)

    while True:
        try:
            user_input = input(colorize("\n> ", 'green')).strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print_info("Goodbye!")
                break

            parts = user_input.split(None, 1)
            if len(parts) < 2:
                print_warning("Invalid command. Use 'sql <query>' or 'mongo <json>'")
                continue

            command, query = parts
            command = command.lower()

            if command == 'sql':
                result = sql_to_mongo(query)
                print_info("\nMongoDB Query:")
                print(json.dumps(result, indent=2))
            elif command == 'mongo':
                mongo_query = json.loads(query)
                result = mongo_to_sql(mongo_query)
                print_info("\nSQL Query:")
                print(result)
            else:
                print_warning(f"Unknown command: {command}")

        except KeyboardInterrupt:
            print_info("\nGoodbye!")
            break
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {str(e)}")
        except ConverterError as e:
            print_error(str(e))
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SQL-Mongo Query Converter CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert SQL to MongoDB
  sql-mongo-converter sql2mongo --query "SELECT * FROM users WHERE age > 25"

  # Convert MongoDB to SQL
  sql-mongo-converter mongo2sql --query '{"collection": "users", "find": {"age": {"$gt": 25}}}'

  # Interactive mode
  sql-mongo-converter interactive

  # Batch conversion from file
  sql-mongo-converter sql2mongo --file queries.sql --output result.json
        """
    )

    parser.add_argument('--version', action='version', version='%(prog)s 2.0.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--log-file', help='Write logs to file')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # SQL to MongoDB command
    sql2mongo = subparsers.add_parser('sql2mongo', help='Convert SQL to MongoDB')
    sql2mongo.add_argument('-q', '--query', help='SQL query to convert')
    sql2mongo.add_argument('-f', '--file', help='Read SQL query from file')
    sql2mongo.add_argument('-o', '--output', help='Write output to file')
    sql2mongo.add_argument('--validate', action='store_true', help='Validate query before conversion')
    sql2mongo.set_defaults(func=convert_sql_to_mongo_cmd)

    # MongoDB to SQL command
    mongo2sql = subparsers.add_parser('mongo2sql', help='Convert MongoDB to SQL')
    mongo2sql.add_argument('-q', '--query', help='MongoDB query JSON to convert')
    mongo2sql.add_argument('-f', '--file', help='Read MongoDB query from JSON file')
    mongo2sql.add_argument('-o', '--output', help='Write output to file')
    mongo2sql.add_argument('--validate', action='store_true', help='Validate query before conversion')
    mongo2sql.set_defaults(func=convert_mongo_to_sql_cmd)

    # Interactive mode
    interactive = subparsers.add_parser('interactive', help='Run in interactive mode')
    interactive.set_defaults(func=interactive_mode)

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger = get_logger()
        logger.set_level(logging.DEBUG)

    if hasattr(args, 'log_file') and args.log_file:
        logger = get_logger()
        logger.add_file_handler(args.log_file)

    # Execute command
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
