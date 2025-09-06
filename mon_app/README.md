# Campus Docs — Flask (SQLite)

Application universitaire en Flask avec rôles (administrateur, professeur, étudiant), upload et visualisation de PDFs (PDF.js), et navigation **Semestre → Groupe → Matière → Leçon/Exercice**.

## Démarrage rapide

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

- Accéder à http://localhost:5000
- Créez un compte admin en définissant des variables d'environnement AVANT le premier lancement (optionnel) :
  - `ADMIN_EMAIL="admin@example.com"`
  - `ADMIN_PASSWORD="admin123"`

Sous Linux/Mac :
```bash
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="admin123"
python run.py
```

Sous Windows PowerShell :
```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="admin123"
python run.py
```

Sinon, créez un compte via **Inscription**, puis modifiez son rôle en **admin** directement dans la base (ou ajoutez un admin via variables d'env).

## Notes
- Les fichiers uploadés sont stockés dans `uploads/`.
- PDF.js est chargé depuis un CDN et affiche les PDFs dans une iframe.
- Thème blanc & vert via Tailwind (CDN).

## Structure
Voir l'arborescence du projet.
