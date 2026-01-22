import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


def save_json(data: Any, filepath: str) -> None:
    """Save data to JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_results(results: Dict[str, Any], output_dir: str = "results") -> str:
    """
    Save benchmark results to timestamped JSON file.

    Returns:
        Path to saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_{timestamp}.json"
    filepath = Path(output_dir) / filename

    save_json(results, str(filepath))

    return str(filepath)


def load_schema(filepath: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    return load_json(filepath)


def load_tests(filepath: str) -> Dict[str, Any]:
    """Load test cases from JSON file."""
    return load_json(filepath)


def read_file_bytes(filepath: str) -> bytes:
    """Read file as bytes."""
    with open(filepath, 'rb') as f:
        return f.read()


def get_mime_type(filepath: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(filepath).suffix.lower()

    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.json': 'application/json',
    }

    return mime_types.get(ext, 'application/octet-stream')
