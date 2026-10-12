# Cars CRUD

A small training application: FastAPI, SQLite, plain HTML, CSS, and vanilla
JavaScript. Create, list, view, edit, and delete cars. No login, ORM, template
engine, Node.js, or frontend build step.

FastAPI serves ordinary HTML files. The browser renders them and JavaScript
calls the JSON API. This is not server-side templating.

## Run the app

Use Python 3.11 or newer. Run the commands from the extracted `cars-crud` folder.

### macOS / Linux

Check the interpreter before creating the virtual environment:

```bash
python3 --version
```

It must report Python 3.11 or newer. On macOS, `python3` may select Apple's
Python 3.9 even when a newer Python is installed. In that case, use the newer
interpreter explicitly, for example `python3.12 -m venv .venv`. An existing
virtual environment keeps the Python version it was created with; to rebuild
an incompatible one, use `python3.12 -m venv --clear .venv` and reinstall the
dependencies below.

```bash
cd cars-crud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Windows PowerShell

```powershell
cd cars-crud
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the application at `http://127.0.0.1:8000`.
Interactive API documentation is at `http://127.0.0.1:8000/docs`.
Stop the server with Ctrl+C.

The database and its table are created automatically on startup. No setup SQL
or migrations are needed for this first version. Existing rows survive restarts.

## What is included

```text
cars-crud/
|-- app/
|   |-- __init__.py
|   |-- main.py                  # App factory, HTML routes, JSON API
|   |-- schemas.py               # Input/output models and validation
|   |-- database.py              # SQLite CRUD using parameterized SQL
|   `-- static/
|       |-- index.html           # List cars and delete from the list
|       |-- car-form.html        # Shared create/edit form
|       |-- car-detail.html      # View one car and delete it
|       |-- style.css
|       `-- app.js               # fetch(), DOM updates, form submission
|-- tests/
|   |-- conftest.py              # Isolated test databases and TestClient
|   |-- unit/test_schemas.py
|   |-- integration/test_database.py
|   |-- api/test_cars_api.py
|   `-- e2e/
|       |-- conftest.py          # Live server and browser fixtures
|       `-- test_browser.py
|-- requirements.txt
|-- requirements-dev.txt
|-- pytest.ini
|-- .gitignore
|-- VERIFICATION.md
`-- README.md
```

`cars.db` is generated in the project root and is not included in the download.

## Car fields

| Field | Rule |
| --- | --- |
| `id` | Generated positive integer; cannot be supplied in create/update input |
| `make` | Required string, 1-60 characters after trimming |
| `model` | Required string, 1-60 characters after trimming |
| `year` | Required JSON integer, 1886-2100 inclusive |
| `color` | Optional string, up to 40 characters; defaults to an empty string |

Text fields are trimmed. Unknown fields, blank make/model values, and invalid
years are rejected. The year range is an explicit training-app rule, not a
dynamic check against the current year. Duplicate cars are allowed.

## Pages

| URL | Purpose |
| --- | --- |
| `/` | List cars; view, edit, or delete a car |
| `/cars/new` | Create a car |
| `/cars/{id}` | View one car |
| `/cars/{id}/edit` | Edit a car |
| `/docs` | Try the API interactively |

JavaScript is required for the car UI. HTML form constraints catch basic input
mistakes; the API validates independently. Deletion requires browser confirmation.

## JSON API

| Method | URL | Success |
| --- | --- | --- |
| GET | `/api/cars` | `200`, array of cars, newest first |
| POST | `/api/cars` | `201`, created car and a `Location` header |
| GET | `/api/cars/{id}` | `200`, one car |
| PUT | `/api/cars/{id}` | `200`, updated car |
| DELETE | `/api/cars/{id}` | `204`, empty response body |

A missing car returns `404`. Invalid input or a non-positive/non-integer ID
returns `422`. `PUT` replaces all editable fields: supply make, model, and year;
omitting color resets it to empty. Partial `PATCH` updates are intentionally
not included.

Example request body for create or update:

```json
{
  "make": "Toyota",
  "model": "Corolla",
  "year": 2024,
  "color": "Silver"
}
```

Example with curl on macOS/Linux:

```bash
curl -i -X POST http://127.0.0.1:8000/api/cars \
  -H 'Content-Type: application/json' \
  -d '{"make":"Toyota","model":"Corolla","year":2024,"color":"Silver"}'

curl http://127.0.0.1:8000/api/cars
```

## Run the tests

Use the virtual environment created above. On Windows, replace `python` below
with `.\.venv\Scripts\python.exe` when the environment is not activated.

Install test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run the backend tests; no browser installation is needed:

```bash
python -m pytest tests/unit tests/integration tests/api -q
```

Run one category:

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python -m pytest tests/api -q
```

Install Chromium and run the end-to-end browser tests:

```bash
python -m playwright install chromium
python -m pytest tests/e2e -q
```

On Linux, Playwright may also need operating-system dependencies:

```bash
python -m playwright install --with-deps chromium
```

To see the browser window on a machine with a graphical desktop:

```bash
python -m pytest tests/e2e --headed
```

After installing Chromium, run everything:

```bash
python -m pytest -q
```

The browser tests start and stop their own server on a free local port. You do
not need to run Uvicorn separately. Every test gets a fresh temporary SQLite
file. Test execution does not use or reset your real `cars.db`.

The E2E fixtures use the Playwright Python library directly; the
`pytest-playwright` plugin is not needed in this project.

### The three test tiers

| Tier | What these tests exercise |
| --- | --- |
| Unit | Validation, whitespace normalization, required fields, and boundaries |
| Integration | Actual SQLite CRUD, transactions, SQL parameters, and persistence across app restarts |
| E2E | Real browser interactions through JavaScript, HTTP, FastAPI, and SQLite |

API tests inspect HTTP status codes, response bodies, validation errors, and
headers. They use the real application and a real test database, so they are
also integration tests. Their separate directory is for learning, not a fourth
test tier. TestClient does not open a network socket.

The five browser tests cover full CRUD, cancelling/confirming deletion, input
validation, safe text rendering, and cancelling edits. See `VERIFICATION.md`
for which checks were actually run in the build environment.

## Database and scope

The app uses Python's built-in `sqlite3` module. Each operation opens and closes
its own connection. SQL parameters are bound with `?` placeholders, not string
interpolation. The UI inserts car values with `textContent`, not `innerHTML`.

To reset your local data, stop the server and delete `cars.db`. This permanently
deletes your cars. The next startup creates an empty database.

An alternative database location can be supplied with `CARS_DB_PATH` before
starting the server, for example on macOS/Linux:

```bash
CARS_DB_PATH=/tmp/practice-cars.db python -m uvicorn app.main:app --reload
```

This is a local training app, not a production deployment template. There is no
authentication or authorization: anyone able to reach it can change the data.
Keep it bound to `127.0.0.1`. Pagination, migrations, user accounts, and advanced
architecture are deliberately omitted.

## Official references

The following documentation covers the library mechanisms used in the code:

- FastAPI static files: https://fastapi.tiangolo.com/tutorial/static-files/
- FastAPI file/HTML responses: https://fastapi.tiangolo.com/advanced/custom-response/
- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- SQLite connections and SQL parameters: https://docs.python.org/3/library/sqlite3.html
- Pydantic fields and validation: https://docs.pydantic.dev/latest/concepts/fields/
- Playwright Python library: https://playwright.dev/python/docs/library
