# SmartHR — API Documentation (drf-spectacular)

This project uses drf-spectacular to generate OpenAPI (Swagger / Redoc) for the Django REST Framework API.

How to view docs locally

1. Start the Django app (dev) — ensure your virtualenv and DB are configured.

```pwsh
# Activate environment (example)
# . venv/Scripts/Activate.ps1
python manage.py runserver
```

2. Open the documentation pages in the browser:

- OpenAPI JSON/YAML: http://localhost:8000/api/schema/
- Swagger UI: http://localhost:8000/api/docs/
- Redoc: http://localhost:8000/api/redoc/

What I added

- View-level @extend_schema annotations across all app views with descriptive summaries, request/response hints and tags grouped by app (Accounts, Applications, Interviews, Jobs, Profiles, Analytics).
- Serializer help_text and extra_kwargs for clearer field documentation in the generated schema.
- A simple test that asserts the schema is generated and contains the expected tags and representative paths.

How to run the tests

```pwsh
# inside your environment
python manage.py test
```

Notes

- The API schema endpoints are protected by the default REST framework permission (IsAuthenticated). Use an authenticated API client or temporarily allow public access if you prefer to view schema without logging in.
- If you want richer examples in the schema, we can add @extend_schema_serializer examples or explicit examples per operation next.
