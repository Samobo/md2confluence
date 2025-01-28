# Utiliser une image Python officielle comme image de base
FROM python:3.9-slim

# Installer uv
RUN pip install uv

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers du projet dans le conteneur
COPY . /app

# Créer un environnement virtuel
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Installer les dépendances du projet
RUN uv pip install -r pyproject.toml

# Commande pour exécuter l'application
ENTRYPOINT ["uv", "run", "md2cf"]
