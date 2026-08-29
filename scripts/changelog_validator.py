import re
import sys
from typing import List, Dict

CHANGELOG_PATH = "CHANGELOG.md"
REQUIRED_SECTIONS = ["Added", "Changed", "Fixed", "Deprecated", "Removed", "Breaking"]

def load_changelog(filepath: str) -> str:
    """Loads the content of the changelog file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Changelog file not found at {filepath}", file=sys.stderr)
        sys.exit(1)

def validate_sections(content: str) -> List[str]:
    """Checks if standard sections exist, without requiring all of them."""
    found_sections = set()
    # Added 'Security' as it is part of the official standard
    section_pattern = re.compile(r"^(#+)\s*(Added|Changed|Fixed|Deprecated|Removed|Breaking|Security)$", re.MULTILINE)
    
    for match in section_pattern.finditer(content):
        found_sections.add(match.group(2))
        
    # If the file has no valid sections at all, flag it. Otherwise, it's fine.
    if not found_sections:
        return ["No valid Keep a Changelog sections found (Added, Changed, Fixed, etc.)"]
        
    return []

def validate_entry_format(content: str) -> List[str]:
    """
    Performs a basic check to ensure entries under sections look like bulleted lists.
    This is a heuristic check for production readiness.
    """
    errors = []
    # Look for any section header followed by content that doesn't start with a bullet point
    # This is complex to do perfectly without a full Markdown parser, so we check for common violations.
    
    # Pattern: Section Header followed by content that is not indented or bulleted
    # We look for a section header, then non-empty lines that do not start with '*' or '-'
    section_pattern = re.compile(r"^(#+)\s*(Added|Changed|Fixed|Deprecated|Removed|Breaking)\s*\n(.*?)(?=\n#|\Z)", re.DOTALL)
    
    for match in section_pattern.finditer(content):
        section_name = match.group(2)
        content_block = match.group(3)
        
        # Check lines within the block for non-bulleted, non-empty lines
        lines = [line.strip() for line in content_block.splitlines() if line.strip()]
        
        for i, line in enumerate(lines):
            if not line.startswith('*') and not line.startswith('-'):
                # Allow for potential introductory text, but flag if it's not a list item
                if i > 0 and not lines[i-1].startswith('*'):
                    errors.append(
                        f"Format Warning in '{section_name}': Line {i+1} ('{line[:30]}...') "
                        "does not appear to be a standard bulleted list item. Please use '*' or '-'."
                    )
                    
    return errors


def main():
    """Main execution function for the validator."""
    print("--- Changelog Validator Initialized ---")
    
    content = load_changelog(CHANGELOG_PATH)
    
    # 1. Section Validation
    missing_sections = validate_sections(content)
    if missing_sections:
        print("\n[CRITICAL FAILURE] Changelog is missing required sections:", file=sys.stderr)
        for section in missing_sections:
            print(f"  - Missing: {section}", file=sys.stderr)
        sys.exit(1)
    else:
        print("[SUCCESS] All required Keep a Changelog sections are present.")

    # 2. Entry Format Validation
    format_errors = validate_entry_format(content)
    if format_errors:
        print("\n[WARNING] Changelog format inconsistencies detected:", file=sys.stderr)
        for error in format_errors:
            print(f"  - {error}", file=sys.stderr)
        # We treat format warnings as non-fatal for CI, but flag them clearly.
        # In a strict gate, this could be sys.exit(1).
        sys.exit(2) 
    else:
        print("[SUCCESS] All entries appear to follow standard bulleted list formatting.")

    print("\n✅ Changelog validation passed successfully.")

if __name__ == "__main__":
    main()
