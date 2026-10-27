# Publicación y release

Checklist para publicar el repositorio en GitHub y el paquete en PyPI.

## 0. Antes de publicar

```bat
python -m pytest
python -m ruff check .
python -m build
```

Verificá además:

- `git status` limpio;
- que no haya PDFs reales ni datos de clientes;
- que `assets/demo.gif` pese menos de 5 MB;
- que `README.md` y `README.en.md` tengan los badges correctos;
- que la versión de `pyproject.toml` y `CHANGELOG.md` coincidan.

## 1. Crear el repositorio en GitHub

El nombre previsto es `puzska/separador-expedientes`.

Si no tenés GitHub CLI:

```bat
winget install --id GitHub.cli
gh auth login
```

Crear el repositorio y subir `main`:

```bat
gh repo create puzska/separador-expedientes --public --source=. --remote=origin --push
```

Si preferís crearlo desde la web, creá el repo vacío y después:

```bat
git remote add origin https://github.com/puzska/separador-expedientes.git
git branch -M main
git push -u origin main
```

## 2. Configurar el repositorio

En GitHub:

- Descripción: `Separá un PDF de expediente judicial en un PDF por trámite, con índice CSV/JSON.`
- Topics: `pdf`, `pypdf`, `pymupdf`, `legaltech`, `judicial`, `expedientes`, `argentina`, `cli`, `python`, `document-automation`.
- Social preview: subir `assets/social-preview.png`.
- Avatar: subir `assets/logo.png`.
- Activar `Private vulnerability reporting` en Settings > Security.
- Activar `Dependabot alerts` y `Dependabot security updates`.
- Activar `Secret scanning` si está disponible.
- En Actions, permitir solo acciones verificadas o las que usa el proyecto.
- En Branches, proteger `main`:
  - requerir pull request antes de mergear;
  - requerir que pase el workflow `CI`;
  - prohibir force push y borrado.

## 3. PyPI

El nombre `separador-expedientes` está libre (verificado el 2026-10-26).

1. Creá una cuenta en https://pypi.org y activá 2FA.
2. Entrá a `Publishing` > `Add a new pending publisher`.
3. Completá:
   - PyPI project name: `separador-expedientes`
   - Owner: `puzska`
   - Repository name: `separador-expedientes`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
4. En GitHub, creá el environment `pypi` en Settings > Environments.
5. No hace falta guardar un token: se usa Trusted Publishing con OIDC.

El workflow `.github/workflows/release.yml` se dispara cuando se publica un
release. Construye el sdist y el wheel, los sube a PyPI y adjunta los artefactos
al release de GitHub.

## 4. Crear el release

El tag local se crea una vez que el commit final está listo:

```bat
git tag -a v2.0.0 -m "v2.0.0"
git push origin main --tags
```

Después, en GitHub:

1. `Releases` > `Draft a new release`.
2. Elegí el tag `v2.0.0`.
3. Título: `v2.0.0`.
4. Notas: copiá la sección `[2.0.0]` de `CHANGELOG.md`.
5. Publicá el release.

El workflow `Release` se encarga del resto. Si falla, revisá:

- que el environment `pypi` exista y coincida con el pending publisher;
- que el workflow se llame `release.yml`;
- que el repositorio y el owner estén bien escritos en PyPI;
- que `id-token: write` esté permitido en el workflow.

## 5. Verificar la instalación

En un entorno limpio:

```bat
python -m venv .venv-pypi
.venv-pypi\Scripts\activate
python -m pip install "separador-expedientes[pypdf]"
separador-expedientes --version
separador-expedientes "ejemplos/expediente_sintetico.pdf" --listar
```

En Linux o macOS:

```bash
python3 -m venv .venv-pypi
source .venv-pypi/bin/activate
python -m pip install "separador-expedientes[pypdf]"
separador-expedientes --version
```

## 6. Badges después del primer release

Cuando PyPI y el release estén publicados, agregá a `README.md` y
`README.en.md`:

```markdown
[![PyPI](https://img.shields.io/pypi/v/separador-expedientes)](https://pypi.org/project/separador-expedientes/)
[![Release](https://img.shields.io/github/v/release/puzska/separador-expedientes)](https://github.com/puzska/separador-expedientes/releases)
```

El badge de CI ya está configurado:

```markdown
[![CI](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml/badge.svg)](https://github.com/puzska/separador-expedientes/actions/workflows/ci.yml)
```

## 7. Después del lanzamiento

- Revisá que el README se vea bien en GitHub, en modo claro y oscuro.
- Verificá que el GIF cargue y que el PNG de fallback exista.
- Probá el quickstart en una máquina limpia.
- Revisá los issues y las discusiones.
- Agregá el release a los milestones.
- Si hay un error en el release, no borres el tag: publicá `v2.0.1`.

## Notas

- `dist/` está en `.gitignore`. El workflow construye los artefactos desde el
  tag; no hacen falta archivos binarios en el repositorio.
- Si publicás un release preliminar, el workflow omite PyPI y solo adjunta los
  artefactos al release.
- No subas expedientes reales para probar el release. Usá
  `ejemplos/expediente_sintetico.pdf`.
