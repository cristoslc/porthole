# initdb

Place Guacamole's schema SQL here before first run.

Download from the Guacamole Docker image:

```bash
docker run --rm guacamole/guacamole:1.5.5 /opt/guacamole/bin/initdb.sh --postgresql > 01-schema.sql
```

Then generate peer connections via porthole:

```bash
porthole seed-guac > 02-connections.sql
```

Both files are auto-applied by PostgreSQL on first container start.
Do NOT place .env or secrets in this directory.
