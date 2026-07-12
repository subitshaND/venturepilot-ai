import json
import os
import re
import traceback

import markdown
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from database import init_db
from models import delete_report, get_report_by_id, get_reports_by_user, save_report
from services.granite_service import generate_startup_blueprint

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# ── Register the auth blueprint ──────────────────────────────────────────────
from auth import auth as auth_blueprint          # noqa: E402
app.register_blueprint(auth_blueprint)

# ── Initialise the database on startup ───────────────────────────────────────
with app.app_context():
    init_db()

# ── Inject current_user into every template ──────────────────────────────────
from auth import login_required                  # noqa: E402
from models import get_user_by_id                # noqa: E402

@app.context_processor
def inject_user():
    uid = session.get("user_id")
    user = get_user_by_id(uid) if uid else None
    return {"current_user": user}

# ── Section number → template data key ───────────────────────────────────────
_SECTION_KEYS = {
    1:  "business_summary",
    2:  "business_model_canvas",
    3:  "competitor_analysis",
    4:  "swot_analysis",
    5:  "estimated_budget",
    6:  "funding_recommendations",
    7:  "revenue_model",
    8:  "gtm_strategy",
    9:  "roadmap",
    10: "future_scope",
}


def _parse_sections(ai_text: str) -> dict:
    """
    Split the AI response on '## N.' headings and convert each section
    from markdown to HTML.  Returns a dict keyed by _SECTION_KEYS values.
    """
    chunks = re.split(r"(?=^## \d+\.)", ai_text, flags=re.MULTILINE)
    sections: dict = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"^## (\d+)\.", chunk)
        if not m:
            continue
        num = int(m.group(1))
        key = _SECTION_KEYS.get(num)
        if key:
            # Strip fenced code blocks that sometimes wrap tables
            chunk = re.sub(r"^```(?:markdown)?\s*\n", "", chunk, flags=re.MULTILINE)
            chunk = re.sub(r"\n```\s*$", "", chunk)
            sections[key] = markdown.markdown(
                chunk,
                extensions=["tables", "nl2br"],
            )
    return sections


# ── Existing routes (unchanged) ───────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/form")
@login_required
def form():
    return render_template("form.html")


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    form_data = request.form.to_dict()

    try:
        print("Calling Granite...")
        ai_response = generate_startup_blueprint(form_data)
        print("===== AI RESPONSE =====")
        print(ai_response)

        sections = _parse_sections(ai_response)
        result_data = {**form_data, **sections}

        # ── Auto-save report for logged-in users ──────────────────────────
        uid = session.get("user_id")
        if uid:
            save_report(
                user_id=uid,
                startup_name=form_data.get("startup_name", ""),
                industry=form_data.get("industry", ""),
                business_stage=form_data.get("business_stage", ""),
                report_data=json.dumps(result_data),
            )

        return render_template("result.html", data=result_data)

    except Exception as e:
        traceback.print_exc()
        error_html = markdown.markdown(f"**Error:** {str(e)}")
        return render_template(
            "result.html",
            data={
                **form_data,
                "business_summary":        error_html,
                "business_model_canvas":   "",
                "competitor_analysis":     "",
                "swot_analysis":           "",
                "estimated_budget":        "",
                "funding_recommendations": "",
                "revenue_model":           "",
                "gtm_strategy":            "",
                "roadmap":                 "",
                "future_scope":            "",
            },
        )


@app.route("/result")
@login_required
def result():
    return render_template("result.html", data={})


# ── My Reports ────────────────────────────────────────────────────────────────

@app.route("/my-reports")
@login_required
def my_reports():
    uid = session["user_id"]
    reports = get_reports_by_user(uid)
    return render_template("my_reports.html", reports=reports)


@app.route("/my-reports/<int:report_id>")
@login_required
def view_report(report_id):
    report = get_report_by_id(report_id)
    if report is None or report["user_id"] != session["user_id"]:
        abort(404)
    data = json.loads(report["report_data"])
    return render_template("result.html", data=data, report=report)


@app.route("/my-reports/<int:report_id>/delete", methods=["POST"])
@login_required
def delete_report_route(report_id):
    deleted = delete_report(report_id, session["user_id"])
    if deleted:
        flash("Report deleted.", "success")
    else:
        flash("Report not found.", "danger")
    return redirect(url_for("my_reports"))


if __name__ == "__main__":
    app.run(debug=True)
