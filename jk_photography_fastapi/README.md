# JK Photography — Web App (FastAPI)

A photography business web app for JK Photography — Bengaluru. Built with **FastAPI**
(rewritten from the earlier Flask version), with a public landing page, a
password-protected portfolio, a customer booking form, and a studio dashboard.

## What's new in this version

- **Switched backend from Flask to FastAPI** (Uvicorn server, SQLAlchemy ORM, Jinja2 templates)
- **Circular logo badge** — your new logo is cropped into a proper circular mark, used in the nav and footer
- **Private gallery** — the full portfolio now requires the studio password to view.
  Visitors see a "this gallery is private" lock screen instead of your real work.
  The homepage's "Recent Work" section is hidden the same way until you log in.
- **Promotional hero banner stays public** — three of the photos you sent over are
  now seeded into the auto-scrolling hero carousel (Wedding, Baby Shoot, Pre-Wedding),
  since that's meant to attract visitors. Manual **prev/next arrows** were added
  alongside the auto-scroll and category dots.
- **Welcome message on login** — logging in now shows "Welcome, JK Photography."
  and takes you to the **landing page** (not straight to the dashboard). Use the
  nav bar's "Dashboard" link from there whenever you want to manage bookings or uploads.
- **Logging out re-locks the gallery immediately** — once logged out, the portfolio
  and "Recent Work" section go back behind the password gate.
- **Unique service cards** — Baby Shoots / Weddings / Cinematography now have a
  more distinct hover-reveal card design with icons and animated accents.

### A note on the images you sent
Of the 6 sample photos, three had another studio's or designer's watermark on them
(the motorcycle poster credited to "heysiri.graphics," the lakeside couple credited
to "Studio3hree wedding company") or read like a professional/celebrity editorial
shot rather than your own work — I left those out, since presenting someone else's
branded work as JK Photography's own portfolio would be misleading to clients and
risks a copyright issue. The other three (couple running in a field, the ring
silhouette shot, and the baby in the flower field) had no visible watermark, so
those are the ones seeded into your hero banner and gallery as placeholders —
swap them out for your real shoots from the dashboard whenever you're ready.

## Why FastAPI instead of React

You mentioned being open to React or "whatever works" — I kept the front end as
server-rendered HTML/CSS/JS (no build step) rather than adding React, since this
setup runs with a single `python main.py`-style command, matching how you've been
running Tiffin Trail and this project so far. If you'd like a React front end later
(e.g. for a more app-like admin dashboard), that's a reasonable next step, but it
would need Node.js and a build process on your machine.

## What's inside

- **Public site**: home page with the promotional hero carousel, unique service
  cards, about section, booking form (saves to the database)
- **Private portfolio**: `/gallery` — password-gated, shows real uploaded work
  once unlocked
- **Studio login**: one-time setup at `/register`, then `/login`
- **Studio dashboard** (`/dashboard`, login required): manage every customer
  enquiry with a status dropdown, upload photos/videos to the gallery by
  category, remove items

## Tech stack

- Python + **FastAPI** + **Uvicorn**
- SQLAlchemy (SQLite database — `jk_photography.db`, created automatically)
- Starlette `SessionMiddleware` for the studio login session (signed cookie)
- Jinja2 templates, plain HTML/CSS/JS front end — no build step needed

## How to run it locally

1. Open a terminal in this folder.
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Start the app:

   ```
   python main.py
   ```

   (or, equivalently: `uvicorn main:app --reload`)

4. Open your browser to:

   ```
   http://127.0.0.1:5000
   ```

5. First time only: go to `http://127.0.0.1:5000/register` and create your
   studio account (username + password). Only one studio account is needed —
   `/register` will redirect to `/login` once it exists.

6. Log in at `/login`. You'll see "Welcome, JK Photography." and land on the
   homepage — your Recent Work section and full gallery will now be unlocked
   for you. Use the "Dashboard" link in the nav to manage bookings and uploads.

7. To see what a customer sees, log out (top nav) and revisit the site — the
   gallery goes back behind the password gate.

## Where things are stored

- `jk_photography.db` — SQLite database, created automatically on first run
  (`admin_user`, `booking`, `gallery_item` tables)
- `static/uploads/images/` — uploaded and seeded photos
- `static/uploads/videos/` — uploaded videos
- `static/images/jk-logo-circle.png` — your circular logo badge

## Notes for going further

- **Change the session secret** in `main.py` (`SessionMiddleware(..., secret_key=...)`)
  before deploying anywhere public — it's a placeholder for local dev right now.
- **Deploying**: `python main.py` is fine for local testing. For a live site,
  run with Gunicorn managing Uvicorn workers (`gunicorn -k uvicorn.workers.UvicornWorker main:app`)
  behind a host like Render or Railway.
- **Forgot studio password**: since there's no "forgot password" flow yet, if you
  ever lock yourself out, delete `jk_photography.db` and `/register` again — note
  this also clears bookings and gallery entries, so only do this in testing.
- **Rethinking the gallery lock**: most photography businesses keep their portfolio
  public specifically to win new clients from people browsing their work. Since you
  asked for it private, that's what's built — but if you'd rather have the gallery
  public and reserve the password gate only for the dashboard (bookings/uploads),
  that's a quick change, just say the word.
