# Packing List

Every time I pack for a trip, I start by making a packinglist. But I always forget to put something on there. To help myself and my family, I made this packinglist app.

It is a Django web app for generating printable packing lists based on trip details: who is coming, where we're going, what we're doing and where we're staying. For example, it will always include sunscreen for a beach trip and a warm hat when the weather is cold.

## Stack

- Django 6
- PostgreSQL (SQLite fallback when `DATABASE_URL` is not set, for development)
- Bootstrap 5 templates

## Setup

### Docker (recommended)

Run the app and PostgreSQL together:

```bash
docker compose up --build
```

The web container waits for PostgreSQL, runs migrations, and creates the initial login user. Open http://127.0.0.1:8000/ and sign in with the credentials from `APP_USERNAME` / `APP_PASSWORD` in `docker-compose.yml` (default `admin` / `changeme`).

**Don't forget to change the admin password!**

To run in the background:

```bash
docker compose up --build -d
```

### Local development

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy environment file and start PostgreSQL only:

   ```bash
   copy .env.example .env
   docker compose up -d db
   ```

3. Run migrations, create a user, and optionally seed starter data:

   ```bash
   python manage.py migrate
   python manage.py ensure_user --username admin --password your-password
   python manage.py seed_defaults
   ```

4. Start the development server (bind to all interfaces for LAN access):

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

Open http://127.0.0.1:8000/

## Authentication

All pages require login. Django session cookies keep you signed in across browser restarts (up to two weeks).

Create additional users:

```bash
python manage.py createsuperuser
```

Or set `APP_USERNAME` and `APP_PASSWORD` before starting Docker — the entrypoint runs `ensure_user` on each start but only creates the user if it does not already exist.

## Local network access

To use the app from phones or other devices on your Wi‑Fi:

1. Set `ALLOWED_HOSTS=*` in `.env` or `docker-compose.yml` (requires `DEBUG=True`).
2. Find your PC's LAN IP with `ipconfig` (e.g. `192.168.1.42`). (set static IP address in your router, so the address doesn't change)
3. Open `http://192.168.1.42:8000/` on the other device.
4. Allow inbound TCP port 8000 through Windows Firewall if needed.
5. If form submissions fail with a CSRF error, set `CSRF_TRUSTED_ORIGINS=http://192.168.1.42:8000`.

After changing settings, rebuild/restart: `docker compose up --build -d`.

## Packing item matching

An item is included on a trip list when:

- **Always** is checked (optionally limited to specific family members on the item), or
- at least one **destination, activity, or accommodation** on the item matches the trip **and** at least one relevant **family member** is on the trip (when family members are tagged on the item, one of them must be on the trip; otherwise any trip member satisfies this condition).

When an item has **weather** type(s) selected (Hot and/or Cold), at least one must match a weather type on the trip. Matching weather is enough for inclusion — accommodation and other category tags are not required. Items with no weather selected are unaffected.

**Who packs this item** controls how lines appear:

- **Individual** — one line per applicable person, labeled with their name
- **Adults / children** — one shared line for adults and one for children
- **Shared** — one line for everyone on the trip

Family members can be marked as **Adult** or **Child** when managing members.

## Tests

```bash
python manage.py test
```

## Future work

- Cloud (Azure?) deployment via environment variables (`DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`)
- Make it possible to use the packinglist online rather than printed: persist 'checked' state of items on packing list. 
- If previous is done, allow users to exclude items from the list or add trip-specific custom items
- Add more users, so I know who to blame when something is checked off but not packed
- Improve the UI of the packingitems list: add filtering and searching
