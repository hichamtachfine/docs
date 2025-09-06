from datetime import datetime
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256
from . import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="etudiant")  # admin, prof, etudiant
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

    @classmethod
    def create_user(cls, name, email, password, role="etudiant"):
        u = cls(name=name, email=email, role=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return u

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Semestre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    groupes = db.relationship("Groupe", backref="semestre", cascade="all, delete")

class Groupe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    semestre_id = db.Column(db.Integer, db.ForeignKey("semestre.id"), nullable=False)
    matieres = db.relationship("Matiere", backref="groupe", cascade="all, delete")

class Matiere(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    groupe_id = db.Column(db.Integer, db.ForeignKey("groupe.id"), nullable=False)
    lecons = db.relationship("Lecon", backref="matiere", cascade="all, delete")

class Lecon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    type_doc = db.Column(db.String(20), default="lecon")  # lecon | exercice
    fichier_pdf = db.Column(db.String(300), nullable=False)  # stored filename path
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    professeur_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    matiere_id = db.Column(db.Integer, db.ForeignKey("matiere.id"), nullable=False)
    professeur = db.relationship("User", foreign_keys=[professeur_id])
    


