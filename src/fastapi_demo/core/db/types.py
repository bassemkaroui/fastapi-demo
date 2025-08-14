from sqlalchemy.types import UserDefinedType
from ulid import ULID


class PGULID(UserDefinedType):
    """
    Map the Postgres 'ulid' type to python-ulid's ULID objects.
    - On bind (python -> db) we accept ulid.ULID, str or bytes.
    - On result (db -> python) we return ulid.ULID for convenience.
    """

    cache_ok = True

    def get_col_spec(self, **kw) -> str:  # type: ignore[no-untyped-def] # noqa: ARG002, PLR6301
        # the literal type name in Postgres
        return "ulid"

    def bind_processor(self, dialect):  # type: ignore[no-untyped-def] # noqa: ARG002, PLR6301
        def process(value):  # type: ignore[no-untyped-def]
            if value is None:
                return None
            if isinstance(value, ULID):
                return str(value)
            if isinstance(value, str):
                ULID.from_str(value)
                return value

        return process

    def result_processor(self, dialect, coltype):  # type: ignore[no-untyped-def] # noqa: ARG002, PLR6301
        def process(value):  # type: ignore[no-untyped-def]
            if value is None:
                return None
            if isinstance(value, str):
                return ULID.from_str(value)
            if isinstance(value, bytes):
                return ULID.from_bytes(value)
            if isinstance(value, ULID):
                return value

        return process
