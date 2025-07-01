# Requires:
# coke_anecdotes.txt, berkshire_anecdotes etc.
# python view_thoughts.py coke_anecdotes.txt

# Might sometimes produce artifacts when the console output overflows, thus safer to use for a reading session:
# python view_thoughts.py coke_anecdotes.txt --start 1 --end 1000

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
import re
import argparse

console = Console()

def parse_thoughts(file_path, start_line=None, end_line=None):
    with open(file_path, "r", encoding="utf-8") as f:
        if start_line is not None or end_line is not None:
            # Read specific line range
            lines = f.readlines()
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else len(lines)
            content = ''.join(lines[start_idx:end_idx])
        else:
            # Read entire file
            content = f.read()

    # Pattern to capture <think>...</think> block followed by response (anything until next <think> or EOF)
    pattern = re.compile(
        r"<think>(.*?)</think>\s*(.*?)(?=(?:<think>)|$)", re.DOTALL
    )

    parsed = []
    for match in pattern.finditer(content):
        think_text = match.group(1).strip()
        response = match.group(2).strip()
        parsed.append((think_text, response))

    return parsed

def display_blocks(parsed_blocks, start_line=None, end_line=None):
    # Show line range info if specified
    if start_line or end_line:
        range_info = f"Lines {start_line or 1} to {end_line or 'end'}"
        console.print(f"[bold yellow]📄 Viewing {range_info}[/bold yellow]")
        console.print()

    for i, (thought, response) in enumerate(parsed_blocks, start=1):
        console.rule(f"[bold cyan]🧠 Block {i}")

        if thought:
            console.print(Text(thought, style="dim italic"))

        if response == "0":
            console.print(Panel(Text("No anecdote found.", style="red"), title="❌ Response"))
        else:
            console.print(Panel(Text(response, style="bold green"), title="✅ Anecdote"))

def main():
    parser = argparse.ArgumentParser(description="Parse and display Berkshire anecdotes with optional line range")
    parser.add_argument("filename", nargs="?", default="berkshire_anecdotes.txt", 
                       help="Input file path (default: berkshire_anecdotes.txt)")
    parser.add_argument("--start", type=int, help="Start line number (1-indexed)")
    parser.add_argument("--end", type=int, help="End line number (1-indexed)")
    parser.add_argument("--lines", type=str, help="Line range in format 'start-end' (e.g., '1-1000' or '2001-3000')")
    
    args = parser.parse_args()
    
    start_line = args.start
    end_line = args.end
    
    # Parse --lines argument if provided
    if args.lines:
        try:
            if '-' in args.lines:
                parts = args.lines.split('-')
                start_line = int(parts[0]) if parts[0] else None
                end_line = int(parts[1]) if parts[1] else None
            else:
                raise ValueError("Invalid format")
        except (ValueError, IndexError):
            console.print("[red]Error: --lines should be in format 'start-end' (e.g., '1-1000')[/red]")
            return
    
    # Validate line numbers
    if start_line is not None and start_line < 1:
        console.print("[red]Error: Start line must be >= 1[/red]")
        return
    
    if end_line is not None and start_line is not None and end_line < start_line:
        console.print("[red]Error: End line must be >= start line[/red]")
        return
    
    try:
        parsed_blocks = parse_thoughts(args.filename, start_line, end_line)
        
        if not parsed_blocks:
            console.print("[yellow]No thought blocks found in the specified range.[/yellow]")
            return
            
        display_blocks(parsed_blocks, start_line, end_line)
        
    except FileNotFoundError:
        console.print(f"[red]Error: File '{args.filename}' not found.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    main()
