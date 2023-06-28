def str_to_float(string: str | float) -> float:
    try:
        return int(string)
    except ValueError:
        return float(str(string).replace(",", "."))
