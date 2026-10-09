from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from domain.analyzer import (
    analyze_text,
    check_api_health,
    get_articles,
    get_article,
    get_comments,
    get_stats,
    login_user,
    post_comment,
    register_user,
)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="../static"
)
app.secret_key = "mtuci-antispam-secret-key-2024"


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    articles = get_articles()
    return render_template("index.html", username=session.get("username"), articles=articles)


@app.route("/article/<int:article_id>")
def article(article_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    art = get_article(article_id)
    if art is None:
        return redirect(url_for("index"))
    comments = get_comments(article_id)
    return render_template(
        "article.html",
        username=session.get("username"),
        article=art,
        comments=comments,
    )


@app.route("/article/<int:article_id>/comment", methods=["POST"])
def comment(article_id):
    if "user_id" not in session:
        return jsonify({"error": "Необходима авторизация"}), 401
    data = request.get_json()
    if not data or not data.get("text", "").strip():
        return jsonify({"error": "Введите текст комментария"}), 400
    result = post_comment(article_id, data["text"].strip(), session["user_id"])
    if "blocked" in result:
        return jsonify(result), 403
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    data = request.get_json()
    result = login_user(data.get("username", ""), data.get("password", ""))
    if "error" in result:
        return jsonify(result), 401
    session["user_id"] = result["id"]
    session["username"] = result["username"]
    session["gender"] = result["gender"]
    return jsonify({"ok": True})


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    data = request.get_json()
    result = register_user(
        data.get("username", ""),
        data.get("password", ""),
        data.get("gender", ""),
    )
    if "error" in result:
        return jsonify(result), 400
    session["user_id"] = result["id"]
    session["username"] = result["username"]
    session["gender"] = result["gender"]
    return jsonify({"ok": True})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/check", methods=["POST"])
def check():
    if "user_id" not in session:
        return jsonify({"error": "Необходима авторизация"}), 401
    data = request.get_json()
    if not data or not data.get("text", "").strip():
        return jsonify({"error": "Введите текст для проверки"}), 400
    result = analyze_text(data["text"].strip(), user_id=session["user_id"])
    return jsonify(result)


@app.route("/stats")
def stats():
    if "user_id" not in session:
        return redirect(url_for("login"))
    data = get_stats()
    return render_template("stats.html", stats=data, username=session.get("username"))


@app.route("/api/health")
def health():
    is_healthy = check_api_health()
    if is_healthy:
        return jsonify({"status": "ok"})
    return jsonify({"status": "unavailable"}), 503
