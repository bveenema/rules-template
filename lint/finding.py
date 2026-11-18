"""One failure line, same shape for every rule."""


def format_finding(rule: str, path: str, line: int | None, message: str) -> str:
    if path and line:
        where = f"{path}:{line}"
    elif path:
        where = path
    else:
        where = rule
    return f"{rule}: {where}: {message}"
