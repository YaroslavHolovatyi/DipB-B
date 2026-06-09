# Local Setup —  Debian

| Tool | Why we  are building project with |

| Build tools, git, openssl headers | Required for building Python wheels and native deps |
| Docker + Compose | Runs PostgreSQL (with PostGIS) and Redis in containers — keeps your laptop clean |
| Python 3.12 + uv | FastAPI backend runtime + the fastest Python package manager |
| PostgreSQL client (`psql`) | Inspect the database directly from the terminal |
| Node.js 22 LTS via nvm | Runs the Expo dev server and the build tooling |
| EAS CLI | Builds installable `.apk` / `.ipa` artefacts for the demo |
| Expo Go (on your phone) | Loads the dev build over the QR code without a native build |
| VS Code | Editor with Python + ESLint + Prettier support |
| GitHub CLI / SSH key | Pull / push to GitHub |
| OpenAI account + API key | Powers the receipt OCR (Vision) and Tavern Tales (GPT-4o) |
| DBeaver (optional) | GUI for inspecting the database visually |
| HTTPie (optional) | Friendly curl alternative for hitting the API |
| direnv (optional) | Auto-loads `.env` when you `cd` into the project |