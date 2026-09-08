# AI Code Converter

AI Code Converter is a FastAPI web application that uses Google Gemini to
translate source code between programming languages and generate new code from
natural-language prompts. It includes account authentication, saved
conversion history, profile management, password changes, and a browser-based
developer workspace.

## Features

- Convert complete programs between languages with an AI-generated explanation.
- Generate runnable code from a natural-language description.
- Automatically detect the language for generated code.
- Register accounts and sign in with email and password.
- Store users and conversion history locally in SQLite.
- View, copy, delete, or clear saved conversion history.
- Update profile information and change a password.
- Display a countdown when Gemini rate limits are returned.
- Serve the frontend and backend from one FastAPI application.

## Technology

- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Google Gemini through the `google-genai` SDK
- **Authentication:** JWT access tokens and PBKDF2-SHA256 password hashes
- **Database:** SQLite using Python's standard-library `sqlite3` module
- **Validation:** Pydantic and `email-validator`
- **Frontend:** HTML, CSS, and vanilla JavaScript
- **Testing:** Pytest

## Project structure

```text
AI_CODE_CONVERTER/
├── backend/
│   ├── main.py                 FastAPI application and API routes
│   ├── database.py             SQLite connection and collection-like helpers
│   ├── models/
│   │   ├── schemas.py          Conversion and generation request models
│   │   └── user_schemas.py     Registration and profile request models
│   ├── services/
│   │   ├── auth_service.py     Password hashing and JWT handling
│   │   └── code_converter.py   Gemini conversion and generation logic
│   ├── static/                 Served frontend JavaScript, CSS, and favicon
│   └── test_*.py               Automated and manual smoke-test files
├── frontend/                   HTML page templates
├── .env                        Local secrets and runtime configuration
├── .env.example                Safe environment-variable template
├── requirements.txt            Python dependencies
└── README.md
```

The SQLite database is created automatically at `backend/ai_code_converter.db`
unless `SQLITE_DB_PATH` points somewhere else. It is ignored by Git.

## Prerequisites

- Windows, macOS, or Linux
- Python 3.10 or newer
- A Google Gemini API key

## Installation

1. Open a terminal in the project directory.
2. Create and activate a virtual environment:

	 **Windows PowerShell**

	 ```powershell
	 python -m venv .venv
	 .\.venv\Scripts\Activate.ps1
	 ```

	 **macOS/Linux**

	 ```bash
	 python3 -m venv .venv
	 source .venv/bin/activate
	 ```

3. Install the dependencies:

	 ```text
	 pip install -r requirements.txt
	 ```

## Environment configuration

The application already loads values from the root `.env` file. Keep your
existing API key there; this project does not require removing or replacing it.
Do not commit `.env` or share its contents.

If setting up a new copy of the project, use `.env.example` as a template and
set these values in `.env`:

| Variable | Required | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | Yes | Google Gemini API key used for conversion and generation |
| `SQLITE_DB_PATH` | No | SQLite database path; defaults to `backend/ai_code_converter.db` |
| `JWT_SECRET_KEY` | Recommended | Long random secret used to sign access tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime; defaults to `1440` minutes |

The API key is read by `backend/services/code_converter.py` via
`GEMINI_API_KEY`; it is never hard-coded in the source files.

## Run the application

From the project root, with the virtual environment activated:

```text
uvicorn backend.main:app --reload
```

Open <http://127.0.0.1:8000/> in a browser. FastAPI's interactive API
documentation is available at <http://127.0.0.1:8000/docs>.

The `--reload` option is intended for development. Omit it when running a
stable local instance.

## API routes

### Pages

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Sign-in and registration page |
| `GET` | `/converter` | Code conversion workspace |
| `GET` | `/generate` | Prompt-to-code workspace |
| `GET` | `/history-page` | Saved conversion history |
| `GET` | `/profile` | Profile management |
| `GET` | `/profile/forgot-password` | Password-change page |

### Authentication and profile

| Method | Route | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/register` | No | Create an account |
| `POST` | `/login` | No | Return a JWT access token |
| `GET` | `/api/profile` | Bearer token | Read the current profile |
| `PUT` | `/api/profile` | Bearer token | Update profile details or password |
| `POST` | `/api/forgot-password` | No | Change a password using account email |

### Conversion and history

| Method | Route | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/convert` | Bearer token | Convert source code with Gemini |
| `POST` | `/generate` | Bearer token | Generate code from a prompt |
| `GET` | `/history` | Bearer token | List the current user's conversions |
| `DELETE` | `/history/{conversion_id}` | Bearer token | Delete one conversion |
| `DELETE` | `/history` | Bearer token | Delete all current-user conversions |

Protected API requests use this header:

```text
Authorization: Bearer <token returned by /login>
```

## Testing

Run the automated tests from the project root:

```text
pytest
```

`backend/test_generate.py` tests response parsing, code-fence removal,
generation endpoint behavior, validation, and quota errors without making live
Gemini requests. `backend/test_gemini.py` is an optional manual smoke test; it
makes a real Gemini request only when run directly and a valid API key is
configured. `backend/test_sqlite.py` prints basic local database information.

## Security notes

- Keep `.env` private. The existing `GEMINI_API_KEY` is preserved and should
	remain configured there.
- Use a long random `JWT_SECRET_KEY` outside local experimentation.
- Do not commit database files, virtual environments, or Python cache folders.
- The current CORS configuration allows all origins for local development. Set
	an explicit frontend origin before deploying publicly.
- Password reset currently verifies the account email only. Add an email
	verification or one-time reset-token flow before production deployment.

## Troubleshooting

- **`ModuleNotFoundError`:** activate `.venv` and run `pip install -r requirements.txt`.
- **Missing Gemini key:** confirm that `GEMINI_API_KEY` exists in the root `.env` file.
- **Quota or rate-limit response:** wait for the retry period or review Gemini
	project billing and quota settings.
- **Database path errors:** ensure the configured parent directory is writable.
- **PowerShell activation blocked:** run PowerShell with an appropriate local
	execution policy, or activate the environment from Command Prompt instead.

## License

No license has been specified for this project yet.
