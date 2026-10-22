from __future__ import annotations

import base64
import html
import json
import mimetypes
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DATABASE_CANDIDATES = [
    APP_DIR / "data" / "plants.db",
    APP_DIR / "plants.db",
    APP_DIR / "database" / "plants.db",
]
IMAGE_DIR_CANDIDATES = [APP_DIR / "images", APP_DIR / "data" / "images"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = dict(zip(MONTHS, ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]))
MAJOR_ORDER = ["Tree", "Shrub", "Grasses (Graminoids)", "Vines", "Ferns & Allies", "Aquatic", "Flowers & Forbs", "Unclassified"]
JSON_FIELDS = {
    "other_names", "scientific_synonyms", "families", "habitats", "cultivars",
    "secondary_growth_groups", "preferred_light", "preferred_water", "soil_moisture",
    "soil_texture", "soil_chemistry", "spread_methods", "structural_habits",
    "rhizome_habits", "leaf_colours", "bloom_periods", "flower_forms", "fruit_types",
    "fruit_months", "fruit_colours", "fruit_persistence", "fall_colours", "winter_habits",
    "above_ground_months", "toxicity_sources", "good_for", "wildlife_value",
    "host_plant_for", "images"
}

st.set_page_config(page_title="Carolinian Native Plant Catalogue", page_icon="🌿", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {min-width: 285px;}
.block-container {max-width: 1500px;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff; border-color:#cbd8d1 !important; border-radius:14px !important; box-shadow:0 2px 8px rgba(28,63,52,.07);}
[data-testid="stImage"] {margin:0 !important;}
[data-testid="stImage"] img {width:100% !important; height:180px !important; object-fit:cover !important; border-radius:10px !important; background:#e8efeb;}
.card-placeholder {height:180px; border-radius:10px; background:#e8efeb; color:#60756c; display:flex; align-items:center; justify-content:center; margin-bottom:.35rem;}
.plant-card {padding:2px 1px 0 1px; background:#fff; height:155px; overflow:hidden;}
.plant-card h3 {margin:0 0 2px 0; color:#214f43; font-size:1.05rem; line-height:1.25; min-height:2.62rem; max-height:2.62rem; overflow:hidden;}
.scientific {font-style:italic; color:#5d7068; margin-bottom:8px; min-height:2.5rem; max-height:2.5rem; overflow:hidden; line-height:1.2;}
.badge {display:inline-block; background:#e5f0ea; color:#285e50; border-radius:999px; padding:2px 8px; margin:2px 4px 2px 0; font-size:.78rem;}
.detail-section {border:1px solid #d5e0da; border-radius:12px; padding:12px; margin:8px 0; background:#fff;}
.bloom-card {border:1px solid #c8d8d0; border-radius:10px; padding:10px 12px; margin:7px 0; background:#f7faf8;}
.detail-gallery {display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:4px 0 18px 0;}
.detail-gallery a {display:block; border:1px solid #c8d8d0; border-radius:12px; overflow:hidden; background:#e8efeb; box-shadow:0 2px 8px rgba(28,63,52,.08);}
.detail-gallery img {display:block; width:100%; height:340px; object-fit:contain; background:#e8efeb; cursor:zoom-in;}
.detail-image-note {color:#60756c; font-size:.86rem; margin-top:-8px; margin-bottom:14px;}
@media (max-width:760px) {.detail-gallery {grid-template-columns:1fr;} .detail-gallery img {height:300px;}}

.muted {color:#687a72;}
</style>
""", unsafe_allow_html=True)


def loads(value: Any, default=None):
    if value is None or value == "":
        return [] if default is None else default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return [] if default is None else default


def locate_database() -> Path | None:
    for path in DATABASE_CANDIDATES:
        if path.is_file():
            return path
    return None


def locate_image(name: str | None) -> Path | None:
    if not name:
        return None
    safe_name = Path(str(name)).name
    for directory in IMAGE_DIR_CANDIDATES:
        path = directory / safe_name
        if path.is_file():
            return path
    return None


def image_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


@st.cache_data(show_spinner=False)
def load_catalogue(db_path: str, modified_ns: int) -> tuple[list[dict], set[str]]:
    del modified_ns
    uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        columns = {row[1] for row in con.execute("PRAGMA table_info(plants)")}
        rows = [dict(row) for row in con.execute("SELECT * FROM plants WHERE COALESCE(deleted,0)=0 ORDER BY scientific_name COLLATE NOCASE")]
    finally:
        con.close()
    for row in rows:
        for field in JSON_FIELDS.intersection(columns):
            row[field] = loads(row.get(field))
    return rows, columns


def text_values(rows: Iterable[dict], field: str) -> list[str]:
    output = set()
    for row in rows:
        value = row.get(field)
        if isinstance(value, list):
            output.update(str(x).strip() for x in value if str(x).strip())
        elif value is not None and str(value).strip():
            output.add(str(value).strip())
    return sorted(output, key=str.casefold)


def display_secondary(row: dict) -> list[str]:
    values = list(row.get("secondary_growth_groups") or [])
    conifer, deciduous = bool(row.get("is_conifer")), bool(row.get("is_deciduous"))
    if conifer and deciduous:
        values.insert(0, "Conifer + Deciduous")
    elif conifer:
        values.insert(0, "Conifer")
    elif deciduous:
        values.insert(0, "Deciduous")
    return list(dict.fromkeys(values)) or ["Other / No Secondary Group"]


def family_name(row: dict) -> str:
    families = row.get("families") or []
    return str(families[0]).strip() if families and str(families[0]).strip() else "Unassigned Family"


def common_sort(row: dict):
    return ((row.get("common_name") or row.get("scientific_name") or "").casefold(), (row.get("scientific_name") or "").casefold())


def scientific_sort(row: dict):
    return (row.get("scientific_name") or "").casefold()


def measure(low, high) -> str:
    if low is None and high is None:
        return "Not specified"
    if low is None: return f"Up to {high:g} cm"
    if high is None: return f"From {low:g} cm"
    if low == high: return f"{low:g} cm"
    return f"{low:g}–{high:g} cm"


def month_ranges(months: list[str]) -> str:
    indexes = sorted({MONTHS.index(m) for m in months if m in MONTHS})
    if not indexes: return "Bloom period not specified"
    runs, start, previous = [], indexes[0], indexes[0]
    for index in indexes[1:]:
        if index == previous + 1:
            previous = index
        else:
            runs.append((start, previous)); start = previous = index
    runs.append((start, previous))
    return "; ".join(MONTH_NAMES[MONTHS[a]] if a == b else f"{MONTH_NAMES[MONTHS[a]]} – {MONTH_NAMES[MONTHS[b]]}" for a, b in runs)


def chips(values: list[str]) -> str:
    return "".join(f'<span class="badge">{html.escape(str(value))}</span>' for value in values if value)


def line(label: str, value: Any) -> str:
    if isinstance(value, list): value = ", ".join(str(x) for x in value)
    if value in (None, "", [], "Unknown", "N/A"): return ""
    return f"<div><b>{html.escape(label)}:</b> {html.escape(str(value))}</div>"


def detail_section(title: str, pairs: list[tuple[str, Any]]):
    body = "".join(line(label, value) for label, value in pairs)
    if body:
        st.markdown(f'<div class="detail-section"><h4>{html.escape(title)}</h4>{body}</div>', unsafe_allow_html=True)


def bloom_section(periods: list[dict]):
    if not periods:
        st.info("Bloom period not specified")
        return
    st.markdown("#### Bloom Periods")
    for period in periods:
        colours = [str(x) for x in period.get("colours", []) if str(x).strip()]
        notes = str(period.get("notes", "") or "").strip()
        colour_html = chips(colours)
        notes_html = f'<div>{html.escape(notes)}</div>' if notes else ""
        st.markdown(f'<div class="bloom-card"><b>{html.escape(month_ranges(period.get("months", [])))}</b><div>{colour_html}</div>{notes_html}</div>', unsafe_allow_html=True)


def render_detail(row: dict):
    images = [locate_image(name) for name in row.get("images", [])]
    images = [path for path in images if path]
    if images:
        gallery_items = []
        for image_path in images[:8]:
            uri = image_data_uri(image_path)
            label = html.escape(image_path.stem.replace("_", " "))
            gallery_items.append(
                f'<a href="{uri}" target="_blank" rel="noopener" title="Open image by itself">'
                f'<img src="{uri}" alt="{label}" loading="lazy"></a>'
            )
        st.markdown('<div class="detail-gallery">' + ''.join(gallery_items) + '</div>', unsafe_allow_html=True)
        st.markdown('<div class="detail-image-note">Click any photo to open the image by itself in a new browser tab.</div>', unsafe_allow_html=True)
    st.subheader(row.get("common_name") or "No common name")
    st.markdown(f"*{html.escape(row.get('scientific_name') or '')}*")
    st.markdown(chips([row.get("major_growth_group") or "Unclassified"] + display_secondary(row)), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        detail_section("Identity & Classification", [
            ("Family", row.get("families")), ("Other Names", row.get("other_names")),
            ("Habitat", row.get("habitats")), ("Native Status", row.get("native_status")),
            ("Rarity", row.get("rarity")), ("Duration", row.get("duration")),
            ("Commercial Availability", row.get("availability")),
            ("Plant Structure", "Herbaceous" if row.get("herbaceous") == 1 else "Woody" if row.get("herbaceous") == 0 else "Not classified"),
            ("Foliage Type", row.get("foliage_type")), ("At Risk", "Yes" if row.get("at_risk") else "No")])
        detail_section("Growing Conditions", [
            ("Required Light", row.get("preferred_light")), ("Required Water", row.get("preferred_water")),
            ("Soil Moisture", row.get("soil_moisture")), ("Soil Composition", row.get("soil_texture")),
            ("Soil Chemistry", row.get("soil_chemistry")), ("Drought-Tolerant", row.get("drought_tolerant")),
            ("Notes", row.get("needs_notes"))])
        detail_section("Form & Size", [
            ("Height", measure(row.get("height_min_cm"), row.get("height_max_cm"))),
            ("Spread", measure(row.get("spread_min_cm"), row.get("spread_max_cm"))),
            ("Spacing", measure(row.get("spacing_cm"), row.get("spacing_cm"))),
            ("Vine Length", measure(row.get("vine_length_cm"), row.get("vine_length_cm"))),
            ("Spread Method", row.get("spread_methods")), ("Structural Habit", row.get("structural_habits")),
            ("Rhizome Habit", row.get("rhizome_habits")), ("Aggressiveness", row.get("aggressiveness"))])
    with c2:
        detail_section("Flowers, Fruit & Seasons", [
            ("Blooms", row.get("blooms")), ("Flower Form", row.get("flower_forms")),
            ("Fragrant", row.get("fragrant")), ("Showy", row.get("showy")),
            ("Fruit", row.get("fruit")), ("Fruit Type", row.get("fruit_types")),
            ("Fruit Period", row.get("fruit_months")), ("Fruit Colour", row.get("fruit_colours")),
            ("Winter Habit", row.get("winter_habits")), ("Winter Interest", row.get("winter_interest"))])
        if row.get("blooms") != "No": bloom_section(row.get("bloom_periods") or [])
        detail_section("Ecology & Uses", [
            ("Wildlife Value", row.get("wildlife_value")), ("Pollinator Value", "Yes" if row.get("pollinator_value") else "No"),
            ("Host Plant For", row.get("host_plant_for")), ("Good For", row.get("good_for")),
            ("Deer Resistance", row.get("deer_resistance")), ("Rabbit Resistance", row.get("rabbit_resistance")),
            ("Salt Tolerance", row.get("salt_tolerance")), ("Erosion Control", row.get("erosion_control")),
            ("Naturalization", row.get("naturalization"))])
        detail_section("Safety & Care", [
            ("Edible", row.get("edible")), ("Toxic", row.get("toxic")), ("Toxic To", row.get("toxic_to")),
            ("Toxicity Notes", row.get("toxicity_notes")), ("Maintenance", row.get("maintenance")),
            ("Care", row.get("care")), ("General Notes", row.get("general_notes"))])


@st.dialog("Plant Details", width="large")
def plant_dialog(plant_id: int):
    row = next((item for item in st.session_state.catalogue_rows if item.get("id") == plant_id), None)
    if row: render_detail(row)


def render_card(row: dict, key_prefix: str):
    with st.container(border=True, key=f"card_{key_prefix}_{row.get('id')}"):
        image = locate_image(row.get("main_image"))
        if image:
            st.image(str(image), use_container_width=True)
        else:
            st.markdown('<div class="card-placeholder">No image</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="plant-card">'
            f'<h3>{html.escape(row.get("common_name") or "No common name")}</h3>'
            f'<div class="scientific">{html.escape(row.get("scientific_name") or "")}</div>'
            f'{chips([row.get("major_growth_group") or "Unclassified"])}'
            f'{line("Family", family_name(row))}'
            f'{line("Light", row.get("preferred_light"))}'
            f'{line("Water", row.get("preferred_water"))}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("View details", key=f"{key_prefix}_{row.get('id')}", use_container_width=True):
            plant_dialog(int(row["id"]))


def render_grid(rows: list[dict], prefix: str):
    if not rows:
        return
    # Build explicit rows instead of continuously feeding columns. This keeps every
    # card aligned with its row and prevents a masonry-style layout.
    cards_per_row = 4
    for row_start in range(0, len(rows), cards_per_row):
        card_columns = st.columns(cards_per_row, gap="medium")
        batch = rows[row_start:row_start + cards_per_row]
        for index, row in enumerate(batch):
            with card_columns[index]:
                render_card(row, prefix)

def paginate(rows: list[dict], key: str) -> list[dict]:
    page_size = st.selectbox("Plants per page", [24, 48, 96], index=0, key=f"size_{key}")
    pages = max(1, (len(rows) + page_size - 1) // page_size)
    page = st.number_input("Page", 1, pages, 1, key=f"page_{key}")
    begin = (page - 1) * page_size
    return rows[begin:begin + page_size]


def grouped_expander(title: str, rows: list[dict], prefix: str, search_active: bool):
    with st.expander(f"{title} ({len(rows):,})", expanded=search_active):
        render_grid(rows, prefix)


db_path = locate_database()
if not db_path:
    st.error("No catalogue database was found. Add plants.db to data/plants.db in the GitHub repository.")
    st.code("repository/\n  streamlit_app.py\n  requirements.txt\n  data/\n    plants.db\n  images/\n    plant-image-files...")
    st.stop()

try:
    rows, columns = load_catalogue(str(db_path), db_path.stat().st_mtime_ns)
except Exception as exc:
    st.error(f"The catalogue database could not be opened: {exc}")
    st.stop()

st.session_state.catalogue_rows = rows
st.title("🌿 Carolinian Native Plant Catalogue")
st.caption("Explore native plants of the Carolinian Zone by family, growth classification, or name.")

with st.sidebar:
    st.header("Find Plants")
    query = st.text_input("Search names, family, habitat, notes")
    view = st.radio("View", ["Family View", "Type View", "Alphabetical - Common", "Alphabetical - Scientific", "Full"], index=3)
    major = st.multiselect("Major Growth Group", text_values(rows, "major_growth_group"))
    family = st.multiselect("Family", text_values(rows, "families"))
    habitat = st.multiselect("Habitat", text_values(rows, "habitats")) if "habitats" in columns else []
    light = st.multiselect("Required Light", text_values(rows, "preferred_light"))
    water = st.multiselect("Required Water", text_values(rows, "preferred_water"))
    bloom_month = st.multiselect("Bloom Month", MONTHS)
    photos_only = st.checkbox("Photos only")
    at_risk_only = st.checkbox("At Risk only")
    st.divider()
    st.caption(f"Database: {db_path.name}")

needle = query.strip().casefold()
def matches(row: dict) -> bool:
    searchable = " ".join(str(row.get(field) or "") for field in ["scientific_name", "common_name", "other_names", "families", "habitats", "general_notes", "needs_notes"]).casefold()
    bloom_months = [month for period in row.get("bloom_periods", []) for month in period.get("months", [])]
    return (
        (not needle or needle in searchable)
        and (not major or row.get("major_growth_group") in major)
        and (not family or any(x in family for x in row.get("families", [])))
        and (not habitat or any(x in habitat for x in row.get("habitats", [])))
        and (not light or any(x in light for x in row.get("preferred_light", [])))
        and (not water or any(x in water for x in row.get("preferred_water", [])))
        and (not bloom_month or any(x in bloom_month for x in bloom_months))
        and (not photos_only or locate_image(row.get("main_image")) is not None)
        and (not at_risk_only or bool(row.get("at_risk")))
    )

filtered = [row for row in rows if matches(row)]
st.subheader(f"Showing {len(filtered):,} of {len(rows):,} plants")
search_active = bool(query.strip())

if not filtered:
    st.info("No plants match the selected filters.")
elif view == "Full":
    render_grid(paginate(sorted(filtered, key=scientific_sort), "full"), "full")
elif view == "Family View":
    groups = {}
    for row in filtered: groups.setdefault(family_name(row), []).append(row)
    for name in sorted(groups, key=lambda x: (x == "Unassigned Family", x.casefold())):
        grouped_expander(name, sorted(groups[name], key=scientific_sort), f"family_{name}", search_active)
elif view == "Type View":
    groups = {}
    for row in filtered:
        major_name = row.get("major_growth_group") or "Unclassified"
        for secondary in display_secondary(row): groups.setdefault(major_name, {}).setdefault(secondary, []).append(row)
    ordered = MAJOR_ORDER + sorted(set(groups) - set(MAJOR_ORDER), key=str.casefold)
    for major_name in ordered:
        if major_name not in groups:
            continue
        count = len({row["id"] for subgroup in groups[major_name].values() for row in subgroup})
        st.markdown(f"### {major_name} ({count:,})")
        for secondary in sorted(groups[major_name], key=str.casefold):
            secondary_rows = sorted(groups[major_name][secondary], key=scientific_sort)
            with st.expander(f"{secondary} ({len(secondary_rows):,})", expanded=search_active):
                render_grid(secondary_rows, f"type_{major_name}_{secondary}")
else:
    common = view == "Alphabetical - Common"
    groups = {}
    for row in filtered:
        value = row.get("common_name") if common else row.get("scientific_name")
        group = "No Common Name" if common and not value else (value[0].upper() if value and value[0].isalpha() else "# / Other")
        groups.setdefault(group, []).append(row)
    names = [chr(code) for code in range(65, 91) if chr(code) in groups] + [x for x in ["# / Other", "No Common Name"] if x in groups]
    for name in names:
        ordered = sorted(groups[name], key=common_sort if common else scientific_sort)
        grouped_expander(name, ordered, f"alpha_{'common' if common else 'scientific'}_{name}", search_active)
