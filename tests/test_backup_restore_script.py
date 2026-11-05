from sqlalchemy.engine import make_url

from scripts.verify_backup_restore import _connection_args


def test_backup_restore_connection_arguments_exclude_password():
    url = make_url("postgresql+psycopg://truthfit:secret@db.example:5433/truthfit")

    arguments = _connection_args(url)

    assert arguments == [
        "--host",
        "db.example",
        "--port",
        "5433",
        "--username",
        "truthfit",
    ]
    assert "secret" not in arguments
