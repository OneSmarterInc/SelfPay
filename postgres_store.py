"""Small adapter for the app's fixed SQL statements; values always remain parameters."""
class PostgresConnection:
    def __init__(self,url):
        import psycopg
        from psycopg.rows import dict_row
        self.connection=psycopg.connect(url,row_factory=dict_row,connect_timeout=10,sslmode='require')
    def __enter__(self):return self
    def __exit__(self,kind,value,tb):
        try:
            if kind:self.connection.rollback()
            else:self.connection.commit()
        finally:self.connection.close()
    def execute(self,sql,params=()):
        if sql.startswith('PRAGMA '):return None
        return self.connection.execute(sql.replace('?', '%s'),params)
    def executemany(self,sql,rows):
        with self.connection.cursor() as cursor:
            cursor.executemany(sql.replace('?', '%s'),rows)
    def executescript(self,script):
        script=script.replace('id INTEGER PRIMARY KEY','id BIGSERIAL PRIMARY KEY').replace(' REAL ', ' DOUBLE PRECISION ')
        for statement in script.split(';'):
            if statement.strip():self.connection.execute(statement)
