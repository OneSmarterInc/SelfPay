"""Retired: the bundled 74-entry seed must never replace the live directory."""


def main():
    raise SystemExit(
        'Legacy seed publication is disabled. Use the reviewed directory_sync.py '
        'workflow and a fresh canonical Library export. Existing data was not touched.'
    )


if __name__ == '__main__':
    main()
