import sys


EXPECTED = (3, 12)


def main() -> None:
    actual = sys.version_info[:2]
    if actual != EXPECTED:
        expected = ".".join(map(str, EXPECTED))
        current = ".".join(map(str, sys.version_info[:3]))
        raise SystemExit(
            f"TruthFit requires Python {expected}.x; current interpreter is {current}. "
            "Activate the project virtual environment before continuing."
        )
    print(f"Python runtime OK: {sys.version.split()[0]}")


if __name__ == "__main__":
    main()
