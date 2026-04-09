"""Detect the dominant programming language of the current working directory."""

from __future__ import annotations

from pathlib import Path

EXTENSION_MAP: dict[str, set[str]] = {
    "python": {".py", ".pyx", ".pyi"},
    "javascript": {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
    "c_cpp": {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"},
    "rust": {".rs"},
    "go": {".go"},
}

MARKER_FILES: dict[str, set[str]] = {
    "python": {"pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "requirements.txt"},
    "javascript": {"package.json", "tsconfig.json", ".npmrc", "bun.lockb", "deno.json"},
    "c_cpp": {"CMakeLists.txt", "Makefile", "meson.build", ".clang-format"},
    "rust": {"Cargo.toml"},
    "go": {"go.mod", "go.sum"},
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "target", "vendor",
    "build", "dist", ".venv", "venv", ".tox", "env",
}

MARKER_WEIGHT = 10
THRESHOLD = 5

_cached_result: str | None = None


def detect_language(path: Path | None = None) -> str:
    """Detect the dominant language. Returns a biome id string.

    Result is cached per process.
    """
    global _cached_result
    if _cached_result is not None:
        return _cached_result

    if path is None:
        path = Path.cwd()

    scores: dict[str, int] = {lang: 0 for lang in EXTENSION_MAP}

    # Check marker files (strong signal)
    for lang, markers in MARKER_FILES.items():
        for marker in markers:
            if (path / marker).exists():
                scores[lang] += MARKER_WEIGHT

    # Walk directory tree (max 3 levels deep)
    _scan_directory(path, scores, depth=0, max_depth=3)

    best_lang = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best_lang] >= THRESHOLD:
        _cached_result = best_lang
    else:
        _cached_result = "generic"

    return _cached_result


def _scan_directory(path: Path, scores: dict[str, int], depth: int, max_depth: int) -> None:
    """Recursively scan for file extensions up to max_depth."""
    if depth >= max_depth:
        return

    # Build a reverse lookup: extension → language
    ext_to_lang: dict[str, str] = {}
    for lang, exts in EXTENSION_MAP.items():
        for ext in exts:
            ext_to_lang[ext] = lang

    try:
        for entry in path.iterdir():
            if entry.is_dir():
                if entry.name not in SKIP_DIRS:
                    _scan_directory(entry, scores, depth + 1, max_depth)
            elif entry.is_file():
                lang = ext_to_lang.get(entry.suffix)
                if lang:
                    scores[lang] += 1
    except PermissionError:
        pass


def reset_cache() -> None:
    """Clear the cached detection result. Useful for testing."""
    global _cached_result
    _cached_result = None
