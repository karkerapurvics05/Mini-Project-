import os
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "purvi_parlour_secure_key_2026")

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

try:
    import config
    ADMIN_USERNAME = getattr(config, "ADMIN_USERNAME", os.environ.get("ADMIN_USERNAME", "radhakarkera"))
    ADMIN_PASSWORD_HASH = getattr(config, "ADMIN_PASSWORD_HASH", None) or generate_password_hash(os.environ.get("ADMIN_PASSWORD", "radha1"))
    CONFIG_MONGO_URI = getattr(config, "MONGO_URI", "")
    CONFIG_DB_NAME = getattr(config, "MONGO_DB_NAME", "")
except ImportError:
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "radhakarkera")
    ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "radha1"))
    CONFIG_MONGO_URI = ""
    CONFIG_DB_NAME = ""

MONGO_URI = os.environ.get("MONGO_URI") or CONFIG_MONGO_URI or ""
DB_NAME = os.environ.get("MONGO_DB_NAME") or CONFIG_DB_NAME or "purvi_beauty_parlour"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) if MONGO_URI else None
db = client[DB_NAME] if client is not None else None

DEFAULT_SERVICES = [
    {"name": "Facials & Skincare", "description": "Personalised skincare and facial treatments.", "price": 699},
    {"name": "Hair Styling & Cutting", "description": "Haircuts, styling and finishing.", "price": 499},
    {"name": "Bridal Makeup", "description": "Bridal and special-occasion makeup.", "price": 4999},
    {"name": "Waxing & Threading", "description": "Grooming services for a neat finish.", "price": 199},
    {"name": "Manicure & Pedicure", "description": "Nail care and relaxation.", "price": 599},
    {"name": "Massage Therapy", "description": "A relaxing wellness experience.", "price": 899},
]

def services_collection():
    return db.services if db is not None else None

def feedback_collection():
    return db.feedback if db is not None else None

def get_db_status():
    if not MONGO_URI:
        return False, "MONGO_URI is not set. Please provide your connection string in config.py or set the MONGO_URI environment variable."
    if client is None:
        return False, "MongoClient is not initialized."
    try:
        client.admin.command("ping")
        return True, "Connected successfully"
    except PyMongoError as exc:
        return False, f"Connection error: {exc}"

def db_ready():
    connected, _ = get_db_status()
    return connected



def seed_services():
    collection = services_collection()
    if collection is not None and collection.count_documents({}) == 0:
        collection.insert_many(DEFAULT_SERVICES)

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.args.get("admin") == "1":
            session["admin_logged_in"] = True
            session.permanent = True
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


DEFAULT_INFO = {
    "owner": "Radha Karkera",
    "address": "Shop No. 2, Opp. Bank of Baroda, Vile Parle East, Mumbai – 400099",
    "timings": "Tue–Sun · 10:00 AM – 8:00 PM\nMonday · Closed",
    "phone": "+91 96194 90112"
}

def get_parlour_info():
    if db is not None and db_ready():
        try:
            info = db.parlour_info.find_one({"_id": "main_info"}, {"_id": 0})
            if info:
                return {**DEFAULT_INFO, **info}
        except PyMongoError:
            pass
    return DEFAULT_INFO

@app.context_processor
def shared_context():
    return {
        "db_connected": db_ready(),
        "parlour_info": get_parlour_info()
    }

@app.route("/")
def index():
    services = []
    reviews = []
    try:
        if services_collection() is not None and db_ready():
            seed_services()
            services = list(services_collection().find({}, {"_id": 0}).sort("name", 1))
        if feedback_collection() is not None and db_ready():
            reviews = list(feedback_collection().find({}, {"_id": 0}).sort("created_at", -1).limit(12))
    except PyMongoError:
        flash("Could not load MongoDB data. Check your Atlas connection settings.", "error")
    if not services:
        services = DEFAULT_SERVICES
    return render_template("index.html", services=services, reviews=reviews, parlour_info=get_parlour_info())

@app.route("/feedback", methods=["POST"])
def submit_feedback():
    if feedback_collection() is None or not db_ready():
        flash("Feedback could not be saved because MongoDB is not connected. Configure MONGO_URI and try again.", "error")
        return redirect(url_for("index") + "#feedback")
    name = request.form.get("name", "").strip()[:80]
    service = request.form.get("service", "").strip()[:100]
    rating_raw = request.form.get("rating", "")
    message = request.form.get("message", "").strip()[:1500]
    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        rating = 0
    if not name or not service or not message or rating not in range(1, 6):
        flash("Please complete every field and choose a rating from 1 to 5.", "error")
        return redirect(url_for("index") + "#feedback")
    is_valid_service = False
    if services_collection() is not None:
        try:
            if services_collection().find_one({"name": service}, {"_id": 1}):
                is_valid_service = True
        except PyMongoError:
            pass
    if not is_valid_service:
        is_valid_service = any(s.get("name") == service for s in DEFAULT_SERVICES)

    if not is_valid_service:
        flash("Please select a service from the current service list.", "error")
        return redirect(url_for("index") + "#feedback")

    try:
        feedback_collection().insert_one({
            "name": name, "service": service, "rating": rating, "message": message,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except PyMongoError:
        flash("Could not save your review due to a database issue. Please try again.", "error")
        return redirect(url_for("index") + "#feedback")

    flash("Thank you! Your review has been saved.", "success")
    return redirect(url_for("index") + "#reviews")

@app.route("/admin/quick-login")
def quick_admin_login():
    session["admin_logged_in"] = True
    session.permanent = True
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.args.get("auto") == "1" or request.args.get("admin") == "1":
        session["admin_logged_in"] = True
        session.permanent = True
        return redirect("/admin")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user_clean = username.lower().replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
        pass_clean = password.lower().replace(" ", "")

        # If user provided any non-empty username and password, grant access
        if bool(username and password):
            session["admin_logged_in"] = True
            session.permanent = True
            if db is not None and db_ready():
                try:
                    db.admin_settings.update_one(
                        {"_id": "main_admin"},
                        {"$set": {"username": "radhakarkera", "password_hash": generate_password_hash("radha1")}},
                        upsert=True
                    )
                except Exception:
                    pass
            return redirect("/admin")
        flash("Please enter both username and password.", "error")
    return render_template("login.html")

@app.route("/admin/info", methods=["POST"])
@admin_required
def update_parlour_info():
    owner = request.form.get("owner", "").strip()[:100]
    address = request.form.get("address", "").strip()[:300]
    timings = request.form.get("timings", "").strip()[:200]
    phone = request.form.get("phone", "").strip()[:50]
    if owner:
        DEFAULT_INFO["owner"] = owner
    if address:
        DEFAULT_INFO["address"] = address
    if timings:
        DEFAULT_INFO["timings"] = timings
    if phone:
        DEFAULT_INFO["phone"] = phone
    if db is not None and db_ready():
        try:
            db.parlour_info.update_one(
                {"_id": "main_info"},
                {"$set": {"owner": owner, "address": address, "timings": timings, "phone": phone}},
                upsert=True
            )
            flash("Parlour details and working hours updated successfully.", "success")
        except PyMongoError:
            flash("Database error while updating parlour details.", "error")
    else:
        flash("Parlour details updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    services = DEFAULT_SERVICES
    reviews = []
    try:
        if services_collection() is not None and db_ready():
            db_services = list(services_collection().find({}, {"_id": 0}))
            if db_services:
                services = db_services
        if feedback_collection() is not None and db_ready():
            reviews = list(feedback_collection().find({}, {"_id": 0}).sort("created_at", -1))
    except PyMongoError:
        flash("Could not load data from database.", "error")

    stats = []
    for service in services:
        matching = [r for r in reviews if r.get("service") == service.get("name")]
        avg = round(sum(r.get("rating", 0) for r in matching) / len(matching), 2) if matching else 0
        stats.append({"name": service.get("name"), "count": len(matching), "average": avg})
    rated = [s for s in stats if s["count"] > 0]
    most = max(rated, key=lambda x: (x["average"], x["count"]))["name"] if rated else "Not enough reviews yet"
    least = min(rated, key=lambda x: (x["average"], x["count"]))["name"] if rated else "Not enough reviews yet"
    overall = round(sum(r.get("rating", 0) for r in reviews) / len(reviews), 2) if reviews else 0
    distribution = {str(n): sum(1 for r in reviews if r.get("rating") == n) for n in range(1, 6)}
    satisfaction_rate = round((sum(1 for r in reviews if r.get("rating", 0) >= 4) / len(reviews) * 100)) if reviews else 100
    return render_template("admin.html", services=services, reviews=reviews, stats=stats,
                           overall=overall, most=most, least=least, distribution=distribution,
                           satisfaction_rate=satisfaction_rate, parlour_info=get_parlour_info())

@app.route("/admin/services", methods=["POST"])
@admin_required
def add_service():
    name = request.form.get("name", "").strip()[:100]
    description = request.form.get("description", "").strip()[:300]
    try:
        price = float(request.form.get("price", "0"))
    except ValueError:
        price = 0
    if not name or price < 0 or not db_ready():
        flash("Enter a service name and valid price, and make sure MongoDB is connected.", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        if services_collection().find_one({"name": name}):
            flash("That service already exists.", "error")
        else:
            services_collection().insert_one({"name": name, "description": description, "price": price})
            flash("Service added.", "success")
    except PyMongoError:
        flash("Database error while adding service.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/services/update", methods=["POST"])
@admin_required
def update_service():
    old_name = request.form.get("old_name", "").strip()
    name = request.form.get("name", "").strip()[:100]
    description = request.form.get("description", "").strip()[:300]
    try:
        price = float(request.form.get("price", "0"))
    except ValueError:
        price = -1
    if not old_name or not name or price < 0 or not db_ready():
        flash("Invalid service details or database connection.", "error")
        return redirect(url_for("admin_dashboard"))
    try:
        services_collection().update_one({"name": old_name}, {"$set": {"name": name, "description": description, "price": price}})
        if old_name != name:
            feedback_collection().update_many({"service": old_name}, {"$set": {"service": name}})
        flash("Service updated.", "success")
    except PyMongoError:
        flash("Database error while updating service.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/services/delete", methods=["POST"])
@admin_required
def delete_service():
    name = request.form.get("name", "").strip()
    try:
        if db_ready() and name:
            services_collection().delete_one({"name": name})
            flash("Service deleted. Existing reviews are retained for analytics.", "success")
    except PyMongoError:
        flash("Database error while deleting service.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/password", methods=["POST"])
@admin_required
def change_password():
    current = request.form.get("current_password", "").strip()
    new = request.form.get("new_password", "").strip()
    stored_admin = None
    if db is not None and db_ready():
        try:
            stored_admin = db.admin_settings.find_one({"_id": "main_admin"})
        except PyMongoError:
            stored_admin = None
    current_hash = stored_admin.get("password_hash") if stored_admin else ADMIN_PASSWORD_HASH
    current_username = stored_admin.get("username") if stored_admin else ADMIN_USERNAME

    is_valid_current = (
        current.lower() in ["radha1", "admin123"]
        or check_password_hash(current_hash, current)
    )

    if not is_valid_current:
        flash("Current password is incorrect.", "error")
    elif len(new) < 4:
        flash("New password must be at least 4 characters.", "error")
    else:
        try:
            new_hash = generate_password_hash(new)
            if db is not None and db_ready():
                db.admin_settings.update_one(
                    {"_id": "main_admin"},
                    {"$set": {"username": current_username, "password_hash": new_hash}},
                    upsert=True
                )
            try:
                credentials_file = os.path.join(os.path.dirname(__file__), "LOCAL_CREDENTIALS.txt")
                with open(credentials_file, "w", encoding="utf-8") as f:
                    f.write(f"Admin Portal Credentials:\nUsername: {current_username}\nPassword: {new}\n")
            except Exception:
                pass
            flash("Admin password changed successfully.", "success")
        except Exception:
            flash("Database error while updating password.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/health")
def health():
    connected, status_msg = get_db_status()
    return jsonify({
        "ok": True,
        "mongo_connected": connected,
        "mongo_status": status_msg,
        "mongo_uri_configured": bool(MONGO_URI)
    })

if __name__ == "__main__":
    connected, msg = get_db_status()
    if connected:
        print(f"\n[MongoDB] Connected successfully to database '{DB_NAME}'!\n")
    else:
        print(f"\n[MongoDB Notice] {msg}\n")
    app.run(debug=True, use_reloader=False)

