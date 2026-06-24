# Packing List

A Django web app for generating printable packing lists based on trip details: family members, destinations, activities, and accommodations.

## Stack

- Django 6
- PostgreSQL (SQLite fallback when `DATABASE_URL` is not set)
- Bootstrap 5 templates

## Setup

### Docker (recommended)

Run the app and PostgreSQL together:

```bash
docker compose up --build
```

The web container waits for PostgreSQL, runs migrations, and seeds starter data on first start. Open http://127.0.0.1:8000/

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

3. Run migrations and seed starter data:

   ```bash
   python manage.py migrate
   python manage.py seed_defaults
   ```

4. Start the development server:

   ```bash
   python manage.py runserver
   ```

Open http://127.0.0.1:8000/

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

- Authentication (views use `AppAccessMixin` as a placeholder)
- Azure deployment via environment variables (`DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`)
