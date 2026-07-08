import os
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from database import Base, engine, get_db
from models import AdminUser, Booking, GalleryItem

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_IMAGE_DIR = os.path.join(BASE_DIR, "static", "uploads", "images")
UPLOAD_VIDEO_DIR = os.path.join(BASE_DIR, "static", "uploads", "videos")

ALLOWED_IMAGE_EXT = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_VIDEO_EXT = {"mp4", "mov", "webm"}

SHOOT_TYPES = [
    "Baby Shoot",
    "Wedding",
    "Cinematography",
    "Pre-Wedding",
    "Maternity",
    "Birthday / Event",
    "Portrait",
    "Other",
]

Base.metadata.create_all(bind=engine)


def seed_gallery_if_empty():
    from database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(GalleryItem).first() is not None:
            return
        seed_items = [
            {"filename": "images/seed_prewedding_running.jpg", "media_type": "image",
             "category": "Pre-Wedding", "title": "Golden hour, hand in hand"},
            {"filename": "images/seed_wedding_ring.jpg", "media_type": "image",
             "category": "Wedding", "title": "Framed by forever"},
            {"filename": "images/seed_baby_flowers.jpg", "media_type": "image",
             "category": "Baby Shoot", "title": "First summer"},
        ]
        for data in seed_items:
            db.add(GalleryItem(**data))
        db.commit()
    finally:
        db.close()


seed_gallery_if_empty()

app = FastAPI(title="JK Photography")

# Signed-cookie sessions (used for the studio login and for flash messages).
# IMPORTANT: change this secret before deploying anywhere public.
app.add_middleware(SessionMiddleware, secret_key="jk-photography-dev-secret-change-this")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ANONYMOUS_USER = SimpleNamespace(is_authenticated=False, username=None)


# ---------- helpers ----------

def flash(request: Request, message: str, category: str = "info"):
    flashes = request.session.get("flashes", [])
    flashes.append({"message": message, "category": category})
    request.session["flashes"] = flashes


def pop_flashes(request: Request):
    flashes = request.session.pop("flashes", [])
    return flashes


def build_url_for(request: Request):
    from urllib.parse import urlencode
    from starlette.routing import NoMatchFound

    def url_for(name: str, **kwargs):
        if name == "static":
            kwargs["path"] = kwargs.pop("filename")
        try:
            return str(request.url_for(name, **kwargs))
        except NoMatchFound:
            # kwargs aren't path params for this route (e.g. ?category=...) —
            # resolve the bare path, then tack them on as a query string.
            base = str(request.url_for(name))
            if kwargs:
                base = f"{base}?{urlencode(kwargs)}"
            return base
    return url_for


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> Optional[AdminUser]:
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return None
    return db.query(AdminUser).filter(AdminUser.id == admin_id).first()


def render(request: Request, template_name: str, status_code: int = 200, **context):
    admin = context.pop("_admin", None)
    current_user = admin if admin else ANONYMOUS_USER
    if admin:
        current_user = SimpleNamespace(is_authenticated=True, username=admin.username)
    ctx = {
        "request": request,
        "url_for": build_url_for(request),
        "current_user": current_user,
        "flashes": pop_flashes(request),
        **context,
    }
    return templates.TemplateResponse(template_name, ctx, status_code=status_code)


def require_login(request: Request, admin: Optional[AdminUser]):
    """Returns a redirect response if not logged in, else None."""
    if not admin:
        flash(request, "Please log in to access the studio dashboard.", "info")
        return RedirectResponse(url=request.url_for("login"), status_code=303)
    return None


# ---------- public routes ----------

@app.get("/")
def index(request: Request, db: Session = Depends(get_db), admin: Optional[AdminUser] = Depends(get_current_admin)):
    featured = []
    if admin:
        featured = db.query(GalleryItem).order_by(GalleryItem.created_at.desc()).limit(8).all()

    hero_categories = ["Wedding", "Baby Shoot", "Pre-Wedding", "Cinematography"]
    hero_slides = []
    for cat in hero_categories:
        item = db.query(GalleryItem).filter(GalleryItem.category == cat).order_by(GalleryItem.created_at.desc()).first()
        hero_slides.append({"category": cat, "item": item})

    return render(request, "index.html", shoot_types=SHOOT_TYPES, featured=featured, hero_slides=hero_slides, _admin=admin)


@app.get("/gallery")
def gallery(request: Request, category: str = "all", db: Session = Depends(get_db), admin: Optional[AdminUser] = Depends(get_current_admin)):
    categories = ["all", "Baby Shoot", "Wedding", "Cinematography", "Pre-Wedding", "Maternity", "Birthday / Event", "Portrait", "Other"]

    if not admin:
        return render(request, "gallery.html", items=[], categories=categories, active_category=category, locked=True, _admin=admin)

    query = db.query(GalleryItem).order_by(GalleryItem.created_at.desc())
    if category != "all":
        query = query.filter(GalleryItem.category == category)
    items = query.all()
    return render(request, "gallery.html", items=items, categories=categories, active_category=category, locked=False, _admin=admin)


@app.get("/book", name="book")
def book_form(request: Request, admin: Optional[AdminUser] = Depends(get_current_admin)):
    return render(request, "book.html", shoot_types=SHOOT_TYPES, form={}, _admin=admin)


@app.post("/book", name="book_submit")
def book_submit(
    request: Request,
    name: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    location: str = Form(""),
    shoot_type: str = Form(""),
    event_date: str = Form(""),
    message: str = Form(""),
    db: Session = Depends(get_db),
    admin: Optional[AdminUser] = Depends(get_current_admin),
):
    name, email, phone, location, shoot_type, event_date, message = (
        name.strip(), email.strip(), phone.strip(), location.strip(),
        shoot_type.strip(), event_date.strip(), message.strip(),
    )

    errors = []
    if not name:
        errors.append("Please tell us your name.")
    if not email:
        errors.append("Please share an email so we can reach you.")
    if not phone:
        errors.append("Please share a phone number.")
    if not location:
        errors.append("Please tell us the shoot location.")
    if shoot_type not in SHOOT_TYPES:
        errors.append("Please choose a shoot type.")

    if errors:
        for e in errors:
            flash(request, e, "error")
        form_data = {"name": name, "email": email, "phone": phone, "location": location,
                     "shoot_type": shoot_type, "event_date": event_date, "message": message}
        return render(request, "book.html", shoot_types=SHOOT_TYPES, form=form_data, _admin=admin)

    booking = Booking(
        name=name, email=email, phone=phone, location=location,
        shoot_type=shoot_type, event_date=event_date, message=message,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return render(request, "booking_success.html", booking=booking, _admin=admin)


# ---------- auth routes ----------

@app.get("/register", name="register")
def register_form(request: Request, db: Session = Depends(get_db)):
    if db.query(AdminUser).first() is not None:
        flash(request, "A studio account already exists. Please log in.", "info")
        return RedirectResponse(url=request.url_for("login"), status_code=303)
    return render(request, "register.html")


@app.post("/register", name="register_submit")
def register_submit(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    confirm_password: str = Form(""),
    db: Session = Depends(get_db),
):
    if db.query(AdminUser).first() is not None:
        flash(request, "A studio account already exists. Please log in.", "info")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    username, email = username.strip(), email.strip()

    if not username or not email or not password:
        flash(request, "All fields are required.", "error")
    elif password != confirm_password:
        flash(request, "Passwords do not match.", "error")
    elif len(password) < 6:
        flash(request, "Password should be at least 6 characters.", "error")
    else:
        admin = AdminUser(username=username, email=email, password_hash=generate_password_hash(password))
        db.add(admin)
        db.commit()
        flash(request, "Studio account created. Please log in.", "success")
        return RedirectResponse(url=request.url_for("login"), status_code=303)

    return render(request, "register.html")


@app.get("/login", name="login")
def login_form(request: Request, db: Session = Depends(get_db)):
    if db.query(AdminUser).first() is None:
        return RedirectResponse(url=request.url_for("register"), status_code=303)
    return render(request, "login.html")


@app.post("/login", name="login_submit")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    admin = db.query(AdminUser).filter(AdminUser.username == username.strip()).first()
    if admin and check_password_hash(admin.password_hash, password):
        request.session["admin_id"] = admin.id
        flash(request, "Welcome, JK Photography.", "success")
        destination = next or str(request.url_for("index"))
        return RedirectResponse(url=destination, status_code=303)
    flash(request, "Invalid username or password.", "error")
    return render(request, "login.html")


@app.post("/unlock", name="unlock")
def unlock(
    request: Request,
    password: str = Form(""),
    next: str = Form(""),
    db: Session = Depends(get_db),
):
    admin = db.query(AdminUser).first()
    destination = next or str(request.url_for("gallery"))
    if admin and check_password_hash(admin.password_hash, password):
        request.session["admin_id"] = admin.id
        flash(request, "Welcome, JK Photography.", "success")
        return RedirectResponse(url=destination, status_code=303)
    flash(request, "Incorrect password.", "error")
    return RedirectResponse(url=destination, status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.pop("admin_id", None)
    flash(request, "Logged out. See you soon!", "info")
    return RedirectResponse(url=request.url_for("index"), status_code=303)


# ---------- admin dashboard ----------

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), admin: Optional[AdminUser] = Depends(get_current_admin)):
    redirect = require_login(request, admin)
    if redirect:
        return redirect
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    gallery_items = db.query(GalleryItem).order_by(GalleryItem.created_at.desc()).all()
    return render(request, "dashboard.html", bookings=bookings, gallery_items=gallery_items, shoot_types=SHOOT_TYPES, _admin=admin)


@app.post("/dashboard/booking/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    request: Request,
    status: str = Form(""),
    db: Session = Depends(get_db),
    admin: Optional[AdminUser] = Depends(get_current_admin),
):
    redirect = require_login(request, admin)
    if redirect:
        return redirect

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        flash(request, "Booking not found.", "error")
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    if status in ["New", "Contacted", "Confirmed", "Completed"]:
        booking.status = status
        db.commit()
        flash(request, "Booking status updated.", "success")

    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)


@app.post("/dashboard/upload")
async def upload_media(
    request: Request,
    title: str = Form(""),
    category: str = Form("Other"),
    media_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Optional[AdminUser] = Depends(get_current_admin),
):
    redirect = require_login(request, admin)
    if redirect:
        return redirect

    if not media_file or not media_file.filename:
        flash(request, "Please choose a file to upload.", "error")
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    filename = media_file.filename
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    if ext in ALLOWED_IMAGE_EXT:
        media_type = "image"
        save_dir = UPLOAD_IMAGE_DIR
        rel_dir = "images"
    elif ext in ALLOWED_VIDEO_EXT:
        media_type = "video"
        save_dir = UPLOAD_VIDEO_DIR
        rel_dir = "videos"
    else:
        flash(request, "Unsupported file type. Use jpg, png, webp, gif for photos or mp4, mov, webm for video.", "error")
        return RedirectResponse(url=request.url_for("dashboard"), status_code=303)

    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    content = await media_file.read()
    with open(os.path.join(save_dir, unique_name), "wb") as f:
        f.write(content)

    item = GalleryItem(
        filename=f"{rel_dir}/{unique_name}",
        media_type=media_type,
        category=category,
        title=title.strip() or filename,
    )
    db.add(item)
    db.commit()
    flash(request, "Uploaded to gallery.", "success")
    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)


@app.post("/dashboard/gallery/{item_id}/delete")
def delete_media(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Optional[AdminUser] = Depends(get_current_admin),
):
    redirect = require_login(request, admin)
    if redirect:
        return redirect

    item = db.query(GalleryItem).filter(GalleryItem.id == item_id).first()
    if item:
        file_path = os.path.join(BASE_DIR, "static", "uploads", item.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.delete(item)
        db.commit()
        flash(request, "Removed from gallery.", "info")

    return RedirectResponse(url=request.url_for("dashboard"), status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)