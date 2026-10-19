# Carolinian Native Plant Catalogue: Streamlit Edition

This is a browser-based copy of the desktop Tkinter viewer. The desktop database editor remains the authoritative editing application.

## Repository layout

```text
repository/
  streamlit_app.py
  requirements.txt
  .gitignore
  .streamlit/
    config.toml
  data/
    plants.db
  images/
    referenced image files
```

## Deploy to Streamlit Community Cloud

1. Copy the files from this package into the GitHub repository.
2. Create `data/` and place a published copy of `plants.db` inside it.
3. Create `images/` and copy the image files referenced by the published database.
4. Remove `__pycache__` from GitHub.
5. In Streamlit Community Cloud, set the entry point to `streamlit_app.py`.
6. Redeploy the application.

## Local test

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows, `RUN_STREAMLIT_VIEWER.bat` performs the same launch after dependencies are installed.

## Included interface

- Family View
- Type View using Major and Secondary Growth Groups
- Alphabetical by Common Name
- Alphabetical by Scientific Name
- Full paginated view
- Search and filters
- Responsive plant cards
- Plant-detail dialog
- Structured bloom-period cards
- Read-only SQLite access

The web app never writes to the database.
