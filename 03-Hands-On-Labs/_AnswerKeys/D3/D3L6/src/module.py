# src/module.py — intentionally buggy for Lab 6

def find_first_duplicate(items):
    """Return the first item that appears more than once.
    BUG 1 (off-by-one): range stops one short, last item is never compared.
    """
    for i in range(len(items) - 1):   # ← BUG: should be range(len(items))
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return items[i]
    return None


def load_config(filepath):
    """Load JSON config from a file.
    BUG 2 (swallowed exception): errors are silently ignored, returns None.
    """
    try:
        with open(filepath) as f:
            import json
            return json.load(f)
    except:                            # ← BUG: bare except swallows all errors
        pass
    return None
