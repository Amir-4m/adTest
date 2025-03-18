from django.db.models import Func, Value, DateTimeField


class AtTimeZone(Func):
    function = ''
    template = '%(expressions)s AT TIME ZONE %(timezone)s'
    output_field = DateTimeField()

    def __init__(self, datetime_field, timezone, **extra):
        # Pass the datetime field and timezone separately
        expressions = (datetime_field,)
        super().__init__(*expressions, timezone=Value(timezone), **extra)

    def as_sql(self, compiler, connection):
        # Override as_sql to manually construct the SQL
        lhs_sql, lhs_params = compiler.compile(self.source_expressions[0])
        rhs_sql, rhs_params = compiler.compile(self.extra['timezone'])
        sql = f"{lhs_sql} AT TIME ZONE {rhs_sql}"
        params = lhs_params + rhs_params
        return sql, params
