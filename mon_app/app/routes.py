import os
from datetime import datetime
import fitz
from .routes import *


from flask import Blueprint,  send_file ,render_template, redirect, url_for, request, flash, send_from_directory, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from . import db
from .models import User, Semestre, Groupe, Matiere, Lecon

bp = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Auth ----------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "etudiant")
        if User.query.filter_by(email=email).first():
            flash("Cet email existe déjà.", "error")
            return redirect(url_for("main.register"))
        user = User.create_user(name=name, email=email, password=password, role=role)
        flash("Compte créé. Vous pouvez vous connecter.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.accueil"))
        flash("Identifiants invalides.", "error")
    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))

# ---------- Home ----------
@bp.route("/")
def accueil():
    recents = Lecon.query.order_by(Lecon.created_at.desc()).limit(8).all()
    return render_template("accueil.html", recents=recents)

# ---------- Navigation ----------
@bp.route("/semestres")
def semestres():
    items = Semestre.query.all()
    return render_template("semestres.html", semestres=items)

@bp.route("/semestre/<int:semestre_id>/groupes")
def groupes(semestre_id):
    semestre = Semestre.query.get_or_404(semestre_id)
    return render_template("groupes.html", semestre=semestre, groupes=semestre.groupes)

@bp.route("/groupe/<int:groupe_id>/matieres")
def matieres(groupe_id):
    groupe = Groupe.query.get_or_404(groupe_id)
    return render_template("matieres.html", groupe=groupe, matieres=groupe.matieres)

@bp.route("/matiere/<int:matiere_id>/lecons")
def lecons(matiere_id):
    matiere = Matiere.query.get_or_404(matiere_id)
    return render_template("lecons.html", matiere=matiere, lecons=matiere.lecons)

# ---------- PDF View / Download ----------
@bp.route("/pdf/<int:lecon_id>")
def get_pdf(lecon_id):
    lecon = Lecon.query.get_or_404(lecon_id)

    # Build absolute path
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], lecon.fichier_pdf)

    if not os.path.exists(file_path):
        abort(404, description="Le fichier PDF n'existe pas sur le serveur.")

    # Serve with PDF mimetype (browser viewer opens automatically)
    return send_file(file_path, mimetype="application/pdf")

@bp.route("/view/<int:lecon_id>")
def view_pdf(lecon_id):
    lecon = Lecon.query.get_or_404(lecon_id)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], lecon.fichier_pdf)

    # Open PDF
    pdf_doc = fitz.open(file_path)

    # Prepare folder for images
    img_folder = os.path.join(current_app.static_folder, "pdf_images")
    os.makedirs(img_folder, exist_ok=True)

    image_urls = []

    for i, page in enumerate(pdf_doc):
        pix = page.get_pixmap(dpi=150)  # Adjust DPI for quality
        img_filename = f"{lecon.id}_page_{i+1}.png"
        img_path = os.path.join(img_folder, img_filename)
        pix.save(img_path)
        image_urls.append(url_for("static", filename=f"pdf_images/{img_filename}"))

    return render_template("lecon.html", lecon=lecon, image_urls=image_urls)


@bp.route('/view_pdf/<int:lecon_id>')
def download_pdf(lecon_id):
    lecon = Lecon.query.get_or_404(lecon_id)
    # Build absolute path
    file_path = os.path.join(current_app.root_path, 'static', 'uploads', lecon.fichier_pdf)

    # Check if file exists
    if not os.path.exists(file_path):
        abort(404, description="Le fichier PDF n'existe pas sur le serveur.")

    return send_file(file_path, mimetype='application/pdf')

# ---------- Upload (Prof) ----------
@bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if current_user.role not in ("prof", "admin"):
        abort(403)

    semestres = Semestre.query.all()
    if request.method == "POST":
        titre = request.form.get("titre")
        type_doc = request.form.get("type_doc", "lecon")
        matiere_id = request.form.get("matiere_id", type=int)
        file = request.files.get("pdf")

        if not file or not allowed_file(file.filename):
            flash("Veuillez sélectionner un fichier PDF valide.", "error")
            return redirect(url_for("main.upload"))

        # --- get related objects ---
        matiere = Matiere.query.get_or_404(matiere_id)
        groupe = matiere.groupe
        semestre = groupe.semestre

        # --- build folder path safely ---
        base_folder = current_app.config["UPLOAD_FOLDER"]
        sub_folder = os.path.join(
            secure_filename(semestre.nom),
            secure_filename(groupe.nom),
            secure_filename(matiere.nom)
        )
        full_path = os.path.join(base_folder, sub_folder)
        os.makedirs(full_path, exist_ok=True)

        # --- save file ---
        filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
        save_path = os.path.join(full_path, filename)
        file.save(save_path)

        # store relative path in DB (use forward slashes for URLs)
        rel_path = os.path.join(sub_folder, filename).replace("\\", "/")

        lecon = Lecon(
            titre=titre,
            type_doc=type_doc,
            fichier_pdf=rel_path,
            professeur_id=current_user.id,
            matiere_id=matiere_id
        )
        db.session.add(lecon)
        db.session.commit()

        flash("Document uploadé avec succès.", "success")
        return redirect(url_for("main.lecons", matiere_id=matiere_id))

    return render_template("upload.html", semestres=semestres)
# Helper for AJAX dependent selects (matières by groupe)
@bp.route("/api/matieres")
def api_matieres():
    groupe_id = request.args.get("groupe_id", type=int)
    if not groupe_id:
        return {"matieres": []}
    mats = Matiere.query.filter_by(groupe_id=groupe_id).all()
    return {"matieres": [{"id": m.id, "nom": m.nom} for m in mats]}

#------------------------------
@bp.route("/manage_lecons", methods=["GET", "POST"])
@login_required
def manage_lecons():
    if current_user.role not in ("prof", "admin"):
        abort(403)

    semestres = Semestre.query.all()
    selected_semestre = request.args.get("semestre_id", type=int)
    selected_groupe = request.args.get("groupe_id", type=int)
    selected_matiere = request.args.get("matiere_id", type=int)

    groupes = Groupe.query.filter_by(semestre_id=selected_semestre).all() if selected_semestre else []
    matieres = Matiere.query.filter_by(groupe_id=selected_groupe).all() if selected_groupe else []
    lecons_query = Lecon.query.filter_by(matiere_id=selected_matiere) if selected_matiere else Lecon.query.filter_by(id=None)

    # if teacher, only show their own lessons
    if current_user.role == "prof":
        lecons_query = lecons_query.filter_by(professeur_id=current_user.id)
    lecons = lecons_query.all()

    # Handle deletion
    if request.method == "POST":
        lecon_id = request.form.get("lecon_id", type=int)
        lecon = Lecon.query.get_or_404(lecon_id)
        if current_user.role != "admin" and lecon.professeur_id != current_user.id:
            abort(403)
        try:
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], lecon.fichier_pdf))
        except Exception:
            pass
        db.session.delete(lecon)
        db.session.commit()
        flash("Leçon / Exercice supprimé avec succès.", "success")
        return redirect(url_for("main.manage_lecons", semestre_id=selected_semestre, groupe_id=selected_groupe, matiere_id=selected_matiere))

    return render_template(
        "manage_lecons.html",
        semestres=semestres,
        groupes=groupes,
        matieres=matieres,
        lecons=lecons,
        selected_semestre=selected_semestre,
        selected_groupe=selected_groupe,
        selected_matiere=selected_matiere
    )



# ---------- Admin ----------
@bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)

    if request.method == "POST":
        action = request.form.get("action")

        # --- Create user ---
        if action == "create_user":
            name = request.form.get("user_name")
            email = request.form.get("user_email")
            password = request.form.get("user_password")
            role = request.form.get("user_role", "etudiant")
            if User.query.filter_by(email=email).first():
                flash("Email déjà utilisé.", "error")
            else:
                user = User.create_user(name=name, email=email, password=password, role=role)
                db.session.add(user)
                db.session.commit()
                flash(f"Compte {role} créé avec succès.", "success")

        # --- Delete user ---
        elif action == "delete_user":
            user_id = request.form.get("user_id", type=int)
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash("Compte supprimé.", "success")

        # --- Add semestre ---
        elif action == "add_semestre":
            nom = request.form.get("semestre_nom")
            if nom and not Semestre.query.filter_by(nom=nom).first():
                db.session.add(Semestre(nom=nom))
                db.session.commit()
                flash("Semestre ajouté.", "success")

        # --- Delete semestre ---
        elif action == "delete_semestre":
            semestre_id = request.form.get("semestre_id", type=int)
            semestre = Semestre.query.get(semestre_id)
            if semestre:
                db.session.delete(semestre)
                db.session.commit()
                flash("Semestre supprimé.", "success")

        # --- Add groupes ---
        elif action == "add_groupes":
            semestre_id = request.form.get("semestre_id", type=int)
            nombre = request.form.get("nombre", type=int)
            base_nom = request.form.get("base_nom", "Groupe")
            semestre = Semestre.query.get_or_404(semestre_id)
            for i in range(1, nombre + 1):
                db.session.add(Groupe(nom=f"{base_nom} {i}", semestre=semestre))
            db.session.commit()
            flash(f"{nombre} groupes ajoutés.", "success")

        # --- Delete groupe ---
        elif action == "delete_groupe":
            groupe_id = request.form.get("groupe_id", type=int)
            groupe = Groupe.query.get(groupe_id)
            if groupe:
                db.session.delete(groupe)
                db.session.commit()
                flash("Groupe supprimé.", "success")

        # --- Add matiere ---
        elif action == "add_matiere":
            groupe_id = request.form.get("groupe_id", type=int)
            nom = request.form.get("matiere_nom")
            if groupe_id and nom:
                db.session.add(Matiere(nom=nom, groupe_id=groupe_id))
                db.session.commit()
                flash("Matière ajoutée.", "success")

        # --- Delete matiere ---
        elif action == "delete_matiere":
            matiere_id = request.form.get("matiere_id", type=int)
            matiere = Matiere.query.get(matiere_id)
            if matiere:
                db.session.delete(matiere)
                db.session.commit()
                flash("Matière supprimée.", "success")

    # Load data for template
    users = User.query.all()
    semestres = Semestre.query.all()
    groupes = Groupe.query.all()
    matieres = Matiere.query.all()

    return render_template(
        "admin.html",
        users=users,
        semestres=semestres,
        groupes=groupes,
        matieres=matieres
    )


# ---------- Weather (simple client-side widget placeholder) ----------
@bp.route("/meteo")
def meteo():
    return render_template("meteo.html")
