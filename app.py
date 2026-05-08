"""
Las · Study Planner · May 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Local:   streamlit run app.py
Deploy:  Push to GitHub → share.streamlit.io

Repo structure:
  your-repo/
  ├── app.py
  ├── requirements.txt
  ├── .gitignore
  └── .streamlit/
      ├── config.toml       ← light theme (committed)
      └── secrets.toml      ← credentials (gitignored, add to Streamlit Cloud secrets)

Supabase table (named: progress):
  id          text        primary key   (e.g. "ms_15_2")
  checked     bool        default false
  updated_at  timestamptz default now()
"""

import streamlit as st
from supabase import create_client
from datetime import datetime, timezone
from collections import defaultdict

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Las · Study Planner · May 2026",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

from datetime import date
TODAY     = date.today()
TODAY_NUM = TODAY.day if (TODAY.month == 5 and TODAY.year == 2026) else None

# ── SUPABASE CLIENT ────────────────────────────────────────────────────────────
# Cached so one connection is reused across all reruns
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )

# ── PERSISTENCE (3 functions — only these changed from v1) ────────────────────
def load_prog() -> dict:
    """Fetch all rows → {session_id: bool}"""
    try:
        result = get_supabase().table("progress").select("id, checked").execute()
        return {row["id"]: row["checked"] for row in result.data}
    except Exception:
        return {}

def save_prog(sid: str, value: bool):
    """Upsert a single row. Called on every checkbox toggle."""
    try:
        get_supabase().table("progress").upsert({
            "id":         sid,
            "checked":    value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass  # degrade gracefully — UI still works, just won't persist

def on_toggle(sid: str):
    """Streamlit on_change callback."""
    val = st.session_state[f"cb_{sid}"]
    st.session_state.checked[sid] = val
    save_prog(sid, val)

# Initialise session state from Supabase on first load
if "checked" not in st.session_state:
    st.session_state.checked = load_prog()

# ── GLOBAL CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: #F7F6F3 !important;
    color: #1A1A18 !important;
}
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] { background-color: #EFEDE8 !important; }
[data-testid="stHeader"]         { background-color: #2C2C2A !important; }

/* ── Card: white body, coloured left stripe ── */
.scard {
    background: #FFFFFF !important;
    border-radius: 9px;
    padding: 12px 16px;
    margin: 5px 0;
    border-left: 5px solid #ccc;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    transition: box-shadow .15s;
}
.scard:hover { box-shadow: 0 3px 10px rgba(0,0,0,0.11); }
.scard.done  { opacity: .32; }

.stag {
    font-size: 11px; font-weight: 700;
    padding: 3px 10px; border-radius: 20px;
    display: inline-block; letter-spacing: .05em;
    text-transform: uppercase; margin-bottom: 7px;
}
.smeta  { font-size: 12px; font-weight: 500; color: #666; margin-bottom: 5px; }
.stopic { font-size: 14px; font-weight: 600; color: #1A1A18; line-height: 1.45; }
.snote  { font-size: 12px; color: #999; margin-top: 5px; font-style: italic; }

/* ── Sidebar ── */
[data-testid="stSidebar"] * { color: #1A1A18 !important; }
[data-testid="stSidebar"] h3 { font-size: 17px !important; font-weight: 700 !important; }
.big-pct  { font-size: 42px; font-weight: 800; color: #1A1A18; text-align: center; line-height: 1; }
.big-sub  { font-size: 13px; color: #777; text-align: center; margin: 3px 0 14px; }
.sec-head { font-size: 12px; font-weight: 700; letter-spacing: .06em;
            text-transform: uppercase; color: #888; margin: 14px 0 6px; }
.cat-row  { display:flex; align-items:center; gap:8px; margin:5px 0; font-size:13px; }
.cat-lbl  { width:94px; color:#333; font-weight:500; flex-shrink:0; }
.bar-bg   { flex:1; background:#E0DDD8; border-radius:6px; height:8px; }
.bar-fill { height:8px; border-radius:6px; }
.cat-n    { font-size:12px; color:#888; width:36px; text-align:right; }
.leg      { display:flex; align-items:center; gap:8px; margin:4px 0; }
.leg-dot  { width:13px; height:13px; border-radius:4px; flex-shrink:0; }
.leg-lbl  { font-size:12px; color:#333; }

div[data-testid="stCheckbox"] { margin-top: 9px !important; }
[data-testid="stInfo"] { background:#EEF4FC !important; border-color:#AACCEE !important; }
[data-testid="stInfo"] * { color:#1A3A5C !important; font-size:13px !important; }
h2 { color: #1A1A18 !important; }
p  { color: #444    !important; }
</style>
""", unsafe_allow_html=True)

# ── COLOUR HELPERS ─────────────────────────────────────────────────────────────
def clr(act, subj):
    """Returns (tag_bg, tag_text, card_border_colour)."""
    a = act.lower(); s = (subj or "").lower()
    if "school exam" in a: return "#FFCCAA","#8B3A00","#D4804A"
    if "mock test"   in a: return "#D3D1C7","#2C2C2A","#888880"
    if "mock prep"   in a: return "#E5E3DC","#555550","#BBBBBB"
    if "analysis"    in a: return "#E8E6E0","#555550","#BBBBBB"
    if "free" in a or "travel" in a: return "#EEEDE9","#999990","#CCCCCC"
    if "hw" in a:
        if "math booklet" in s:                              return "#FAE0C0","#7A4A00","#D4924A"
        if "english"      in s:                              return "#FFE0EC","#9A1030","#DD6080"
        if any(x in s for x in ("school rec","cleanup","pack")): return "#E8E8E8","#444444","#BBBBBB"
        return "#E8D5F5","#5A2A8E","#A070CC"
    if "new chapter" in a:
        if "physics" in s: return "#B5D4F4","#0A3870","#3A7BC8"
        if "chem"    in s: return "#C0DD97","#1E4808","#5A9A30"
        if "math"    in s: return "#FAC775","#4A2800","#C07820"
    if "revision" in a:
        if "physics" in s: return "#C8E2F8","#0A3870","#5090D0"
        if "chem"    in s: return "#D4EDB8","#1E4808","#6AA040"
        if "math"    in s: return "#FAE8C0","#5A3000","#D08030"
    if "exam prep" in a or "practice" in a:
        if "physics" in s:                               return "#C4DDF5","#083060","#3A7BC8"
        if "chem"    in s:                               return "#B8E0A0","#0A3008","#5A9A30"
        if "math"    in s:                               return "#F5C860","#3A2000","#C07820"
        if "english" in s:                               return "#FFD0DC","#701020","#CC4060"
        if "cs" in s or "computer" in s:                 return "#DDD0F0","#3A1070","#8050C0"
    return "#E8E8E4","#444440","#BBBBBB"

def tag(act, subj):
    a = act.lower(); s = (subj or "").lower()
    if "school exam" in a: return "★ EXAM"
    if "mock test"   in a: return "MOCK"
    if "mock prep"   in a: return "MOCK PREP"
    if "analysis"    in a: return "ANALYSIS"
    if "free"  in a:       return "FREE"
    if "travel" in a:      return "TRAVEL"
    if "hw" in a:
        if "math booklet" in s:                               return "HW · BOOKLET"
        if "english"      in s:                               return "HW · ENGLISH"
        if any(x in s for x in ("school rec","cleanup","pack")): return "HW · ADMIN"
        return "HW · CENTUM"
    if "new chapter" in a:
        if "physics" in s: return "PHYS 12 · NEW"
        if "chem"    in s: return "CHEM 12 · NEW"
        if "math"    in s: return "MATH 12 · NEW"
    if "revision" in a:
        if "physics" in s: return "PHYS 11 · REV"
        if "chem"    in s: return "CHEM 11 · REV"
        if "math"    in s: return "MATH 11 · REV"
    if "exam prep" in a or "practice" in a:
        if "physics" in s: return "PHYS · PREP"
        if "chem"    in s: return "CHEM · PREP"
        if "math"    in s: return "MATH · PREP"
        if "english" in s: return "ENG · PREP"
        if "cs" in s or "computer" in s: return "CS · PREP"
    return act[:12].upper()

# ── SCHEDULE DATA ──────────────────────────────────────────────────────────────
# (id, phase, day_num, day_label, time, activity, subject, topic, duration, note)
SCHEDULE = [
    # PRE-GOA
    ("pre_8_1","Pre-Goa",8,"Thu 8 May","1:15 – 2:00 pm",
     "HW","Centum HW","Centum homework","45 min",""),
    ("pre_8_2","Pre-Goa",8,"Thu 8 May","2:00 – 4:00 pm",
     "New Chapter","Physics",
     "Current Electricity — Ohm's law, Kirchhoff's laws, Wheatstone bridge","2 h","Continued on 16 May"),

    # GOA
    ("goa_9_1","Goa",9,"Fri 9 May","9:00 am – 3:00 pm",
     "Travel","—","Travel to Goa","—",""),
    ("goa_9_3","Goa",9,"Fri 9 May","5:00 – 6:30 pm",
     "HW","Math Booklet",
     "Continuity — definitions, theorems, types of continuity","1.5 h","Arrive Goa; settle first"),
    ("goa_9_4","Goa",9,"Fri 9 May","6:30 – 7:45 pm",
     "HW","School Records","Update school records","1.25 h",""),

    ("goa_10_1","Goa",10,"Sat 10 May","9:00 – 11:30 am",
     "HW","English Project","English project — main body (bulk done today)","2.5 h","Priority #1 for the trip"),
    ("goa_10_2","Goa",10,"Sat 10 May","12:30 – 2:00 pm",
     "HW","Math Booklet",
     "Differentiation — rules, chain rule, implicit, log","1.5 h","After lunch"),
    ("goa_10_3","Goa",10,"Sat 10 May","3:30 – 4:30 pm",
     "Revision","Mathematics (11th)","Trig — ratios, identities, key formulae","1 h","Notes/phone; no desk needed"),

    ("goa_11_1","Goa",11,"Sun 11 May","9:00 – 10:30 am",
     "HW","School Records + Centum HW","School records + pending Centum HW","1.5 h",""),
    ("goa_11_2","Goa",11,"Sun 11 May","10:30 am – 12:00 pm",
     "HW","English Project",
     "English project — conclusion + edits  ✓ COMPLETE TODAY","1.5 h","Finish fully today"),
    ("goa_11_3","Goa",11,"Sun 11 May","1:30 – 2:30 pm",
     "Revision","Mathematics (11th)","Trig — equations, inverse trig, practice","1 h","After lunch rest"),
    ("goa_11_4","Goa",11,"Sun 11 May","2:30 – 3:30 pm",
     "Revision","Chemistry (11th)",
     "Chemical Bonding — bond types, VSEPR, hybridisation","1 h",""),

    ("goa_12_1","Goa",12,"Mon 12 May","9:00 – 10:30 am",
     "HW","Math Booklet","Math Booklet — complete all remaining  ✓ DONE","1.5 h","Fully done today"),
    ("goa_12_2","Goa",12,"Mon 12 May","10:30 – 11:30 am",
     "Revision","Chemistry (11th)",
     "Chemical Bonding — polarity, MOT, molecular geometry","1 h",""),
    ("goa_12_3","Goa",12,"Mon 12 May","11:30 am – 12:30 pm",
     "HW","School Records + Cleanup","School records + final HW check","1 h","Keep afternoon free"),

    ("goa_13_1","Goa",13,"Tue 13 May","9:00 – 10:00 am",
     "HW","School Records + Cleanup",
     "Final HW audit — confirm ALL items complete","1 h","All done by EOD"),
    ("goa_13_2","Goa",13,"Tue 13 May","10:00 – 11:30 am",
     "Revision","Chemistry (11th)",
     "Organic Chemistry Basics + Hydrocarbons — key reactions","1.5 h",""),
    ("goa_13_3","Goa",13,"Tue 13 May","11:30 am+",
     "Free","—","Pack, relax, family time","—","No study after 11:30"),

    ("goa_14_1","Goa",14,"Wed 14 May","7:00 – 8:30 pm",
     "Revision","Mathematics (11th)",
     "Trig — final consolidation, unclear concepts","1.5 h","Home from Goa; settle first"),

    # MAIN SPRINT
    ("ms_15_1","Main Sprint",15,"Thu 15 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break (home 1:45 pm)","45 min",""),
    ("ms_15_2","Main Sprint",15,"Thu 15 May","2:30 – 4:15 pm",
     "New Chapter","Mathematics",
     "C&D Part 1 — continuity: definitions, theorems, IVT, sandwich","1 h 45 min",""),

    ("ms_16_1","Main Sprint",16,"Fri 16 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_16_2","Main Sprint",16,"Fri 16 May","2:30 – 4:15 pm",
     "New Chapter","Mathematics",
     "C&D Part 2 — differentiability, MVT, Rolle's theorem","1 h 45 min",""),
    ("ms_16_3","Main Sprint",16,"Fri 16 May","4:30 – 6:30 pm",
     "New Chapter","Physics",
     "Current Electricity — complete chapter + practice problems","2 h","Finishes May 8 start"),

    ("ms_17_1","Main Sprint",17,"Sat 17 May","9:00 – 11:30 am",
     "New Chapter","Physics",
     "Moving Charges & Magnetism — Biot-Savart, Ampere, force","2.5 h","Sat Centum 12:30 – 4:30"),
    ("ms_17_2","Main Sprint",17,"Sat 17 May","5:45 – 7:45 pm",
     "New Chapter","Chemistry",
     "Alcohols, Phenols & Ethers Part 1 — nomenclature, prep methods","2 h","Home ~5:15 · 30-min break"),

    ("ms_18_1","Main Sprint",18,"Sun 18 May","8:00 – 10:00 am",
     "Mock Prep","—","Light review — all chapters covered so far","2 h","No new content"),
    ("ms_18_2","Main Sprint",18,"Sun 18 May","10:00 am – 1:00 pm",
     "Mock Test","—","Full Mock Test (Mock 1)","3 h",""),
    ("ms_18_3","Main Sprint",18,"Sun 18 May","1:30 – 3:00 pm",
     "Analysis","—","Mock analysis — error log + weak chapter list","1.5 h",""),
    ("ms_18_4","Main Sprint",18,"Sun 18 May","5:00 – 7:00 pm",
     "Revision","Mathematics (11th)",
     "Limits & Derivatives — standard limits, L'Hôpital, first principles","2 h",""),

    ("ms_19_1","Main Sprint",19,"Mon 19 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_19_2","Main Sprint",19,"Mon 19 May","2:30 – 4:15 pm",
     "New Chapter","Mathematics",
     "AoD Part 1 — increasing/decreasing, tangents & normals","1 h 45 min",""),
    ("ms_19_3","Main Sprint",19,"Mon 19 May","7:30 – 9:00 pm",
     "Revision","Physics (11th)",
     "Motion — straight line, plane, projectile (key formulae + problems)","1.5 h","Mon/Wed eve only"),

    ("ms_20_1","Main Sprint",20,"Tue 20 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_20_2","Main Sprint",20,"Tue 20 May","2:30 – 4:15 pm",
     "New Chapter","Chemistry",
     "Alcohols, Phenols & Ethers Part 2 — reactions, properties","1 h 45 min","Evening free"),

    ("ms_21_1","Main Sprint",21,"Wed 21 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_21_2","Main Sprint",21,"Wed 21 May","2:30 – 4:15 pm",
     "New Chapter","Mathematics",
     "AoD Part 2 — maxima/minima, rate of change, approximations","1 h 45 min",""),
    ("ms_21_3","Main Sprint",21,"Wed 21 May","7:30 – 9:00 pm",
     "Revision","Physics (11th)",
     "Kinetic Theory + Thermodynamics — key laws, equations, PYQs","1.5 h",""),

    ("ms_22_1","Main Sprint",22,"Thu 22 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_22_2","Main Sprint",22,"Thu 22 May","2:30 – 4:15 pm",
     "New Chapter","Chemistry",
     "Aldehydes, Ketones & Carboxylic Acids Part 1 — nomenclature, prep","1 h 45 min","Evening free"),

    ("ms_23_1","Main Sprint",23,"Fri 23 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ms_23_2","Main Sprint",23,"Fri 23 May","2:30 – 4:15 pm",
     "New Chapter","Chemistry",
     "Aldehydes, Ketones & Carboxylic Acids Part 2 — reactions, NAR","1 h 45 min",""),
    ("ms_23_3","Main Sprint",23,"Fri 23 May","4:30 – 6:30 pm",
     "Practice","Mathematics",
     "C&D + AoD — exam-style problems  ⚠ Math exam in 3 days!","2 h","All 6 new chapters done today"),

    ("ms_24_1","Main Sprint",24,"Sat 24 May","9:00 – 11:30 am",
     "Practice","Physics",
     "Current Electricity + Moving Charges — revision + JEE problems","2.5 h","Sat Centum 12:30 – 4:30"),
    ("ms_24_2","Main Sprint",24,"Sat 24 May","5:45 – 7:45 pm",
     "Practice","Mathematics",
     "C&D + AoD — full revision sweep  ⚠ exam May 26","2 h","Home ~5:15 · 30-min break"),

    # EXAM PREP
    ("ep_25_1","Exam Prep",25,"Sun 25 May","10:00 am – 12:00 pm",
     "Exam Prep","Mathematics","C&D + AoD — problem sets, formula sheet","2 h","Math exam TOMORROW"),
    ("ep_25_2","Exam Prep",25,"Sun 25 May","2:00 – 4:00 pm",
     "Exam Prep","Mathematics","Past papers + weak areas","2 h",""),
    ("ep_25_3","Exam Prep",25,"Sun 25 May","4:00 – 5:30 pm",
     "Exam Prep","CS","CS prep overview (exam May 27)","1.5 h",""),

    ("ep_26_1","Exam Prep",26,"Mon 26 May","Morning",
     "School Exam","Mathematics","★ MATH SCHOOL EXAM","—","C&D + AoD  |  No Centum today"),
    ("ep_26_2","Exam Prep",26,"Mon 26 May","2:00 – 4:00 pm",
     "Exam Prep","CS","CS prep (exam tomorrow)","2 h","Rest post-exam"),

    ("ep_27_1","Exam Prep",27,"Tue 27 May","Morning",
     "School Exam","CS","★ CS SCHOOL EXAM","—","No Centum today"),
    ("ep_27_2","Exam Prep",27,"Tue 27 May","2:00 – 4:00 pm",
     "Exam Prep","Physics",
     "Current Electricity + Moving Charges — begin exam revision","2 h","Physics exam June 1"),

    ("ep_28_1","Exam Prep",28,"Wed 28 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ep_28_2","Exam Prep",28,"Wed 28 May","2:30 – 4:15 pm",
     "Exam Prep","Physics","Current Electricity — problem sets + weak areas","1 h 45 min",""),
    ("ep_28_3","Exam Prep",28,"Wed 28 May","7:30 – 9:00 pm",
     "Revision","Physics (11th)",
     "Motion — rotational + laws of motion (exam revision)","1.5 h",""),

    ("ep_29_1","Exam Prep",29,"Thu 29 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ep_29_2","Exam Prep",29,"Thu 29 May","2:30 – 4:15 pm",
     "Exam Prep","Physics","Moving Charges — exam-style questions, weak areas","1 h 45 min",""),

    ("ep_30_1","Exam Prep",30,"Fri 30 May","1:45 – 2:30 pm",
     "HW","Centum HW","Centum HW + rest break","45 min",""),
    ("ep_30_2","Exam Prep",30,"Fri 30 May","2:30 – 4:30 pm",
     "Revision","Physics (11th)","Kinetic Theory + Thermodynamics — exam revision","2 h",""),
    ("ep_30_3","Exam Prep",30,"Fri 30 May","4:45 – 6:45 pm",
     "Exam Prep","Chemistry",
     "Alcohols + Aldehydes/Ketones — revision (Chem exam June 4)","2 h",""),

    ("ep_31_1","Exam Prep",31,"Sat 31 May","9:00 – 11:30 am",
     "Exam Prep","Chemistry",
     "Aldehydes, Ketones & Carboxylic Acids — full revision","2.5 h","Chem exam June 4"),
    ("ep_31_2","Exam Prep",31,"Sat 31 May","5:45 – 7:45 pm",
     "Exam Prep","English",
     "English — exam prep + project review (exam June 3)","2 h","Home ~5:15 · 30-min break"),
]

# ── DERIVED STATS ──────────────────────────────────────────────────────────────
TRACKABLE = [s for s in SCHEDULE if s[5].lower() not in ("travel","free")]
TOTAL     = len(TRACKABLE)
DONE      = sum(1 for s in TRACKABLE if st.session_state.checked.get(s[0], False))

CATS = [
    ("New Chapters", "#3A7BC8", lambda s: "new chapter" in s[5].lower()),
    ("Revision",     "#5A9A30", lambda s: "revision"    in s[5].lower()),
    ("HW",           "#A070CC", lambda s: "hw"          in s[5].lower()),
    ("Practice/Prep","#C07820",
     lambda s: any(x in s[5].lower() for x in ("exam prep","practice","mock","analysis"))),
]

PHASES = [
    ("Pre-Goa",    "📅  Pre-Goa · 8 May",        "#D6EDD6","#1A4A1A"),
    ("Goa",        "🌊  Goa Trip · 9–14 May",     "#C8E4F4","#0A3058"),
    ("Main Sprint","⚡  Main Sprint · 15–24 May",  "#EEE8D8","#3A2C10"),
    ("Exam Prep",  "📝  Exam Prep · 25–31 May",   "#F4E0D0","#5A2810"),
]

by_phase = defaultdict(lambda: defaultdict(list))
for row in SCHEDULE:
    by_phase[row[1]][(row[2], row[3])].append(row)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📚 Las · May 2026")
    st.divider()

    pct = int(DONE / TOTAL * 100) if TOTAL else 0
    st.markdown(f'<div class="big-pct">{pct}%</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="big-sub">{DONE} of {TOTAL} sessions complete</div>',
        unsafe_allow_html=True,
    )
    st.progress(DONE / TOTAL if TOTAL else 0)

    st.markdown('<div class="sec-head">By Category</div>', unsafe_allow_html=True)
    for label, colour, fn in CATS:
        items = [s for s in TRACKABLE if fn(s)]
        d = sum(1 for s in items if st.session_state.checked.get(s[0], False))
        t = len(items)
        pp = int(d / t * 100) if t else 0
        st.markdown(f"""
        <div class="cat-row">
          <span class="cat-lbl">{label}</span>
          <div class="bar-bg">
            <div class="bar-fill" style="width:{pp}%;background:{colour};"></div>
          </div>
          <span class="cat-n">{d}/{t}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-head">By Phase</div>', unsafe_allow_html=True)
    for pk, _, ph_bg, ph_fg in PHASES:
        items = [s for s in TRACKABLE if s[1] == pk]
        d = sum(1 for s in items if st.session_state.checked.get(s[0], False))
        t = len(items)
        pp = int(d / t * 100) if t else 0
        short = pk.replace(" Sprint","").replace(" Prep","")
        st.markdown(f"""
        <div class="cat-row">
          <span class="cat-lbl">{short}</span>
          <div class="bar-bg">
            <div class="bar-fill" style="width:{pp}%;background:{ph_fg};"></div>
          </div>
          <span class="cat-n">{d}/{t}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sec-head">Legend</div>', unsafe_allow_html=True)
    LEGEND = [
        ("PHYS 12 · NEW","#B5D4F4","#0A3870"),("CHEM 12 · NEW","#C0DD97","#1E4808"),
        ("MATH 12 · NEW","#FAC775","#4A2800"),("PHYS 11 · REV","#C8E2F8","#0A3870"),
        ("CHEM 11 · REV","#D4EDB8","#1E4808"),("MATH 11 · REV","#FAE8C0","#5A3000"),
        ("HW · CENTUM",  "#E8D5F5","#5A2A8E"),("HW · BOOKLET", "#FAE0C0","#7A4A00"),
        ("HW · ENGLISH", "#FFE0EC","#9A1030"),("MOCK",         "#D3D1C7","#2C2C2A"),
        ("PRACTICE/PREP","#F5C860","#3A2000"),("★ EXAM",       "#FFCCAA","#8B3A00"),
    ]
    for lbl, bg, fg in LEGEND:
        st.markdown(f"""
        <div class="leg">
          <div class="leg-dot" style="background:{bg};border:1.5px solid {fg}66;"></div>
          <span class="leg-lbl">{lbl}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()
    with st.expander("⚙️ Reset progress"):
        st.caption("Type **reset** to clear all ticks")
        val = st.text_input("", placeholder="reset",
                            label_visibility="collapsed", key="reset_input")
        if val.strip().lower() == "reset":
            get_supabase().table("progress").delete().neq("id","__never__").execute()
            st.session_state.checked = {}
            st.success("All progress cleared.")
            st.rerun()

# ── MAIN ───────────────────────────────────────────────────────────────────────
st.markdown("## 📚 Las — Study Planner · May 2026")
st.caption("Tick each block when you're done. Progress saves to the cloud instantly.")
st.write("")

tab_objs = st.tabs([p[1] for p in PHASES])

for tab, (phase_key, _, ph_bg, ph_fg) in zip(tab_objs, PHASES):
    with tab:
        phase_days = by_phase[phase_key]
        if not phase_days:
            st.info("Nothing scheduled here yet.")
            continue

        for (dnum, dlabel), sessions in sorted(phase_days.items()):
            day_track = [s for s in sessions if s[5].lower() not in ("travel","free")]
            day_done  = sum(1 for s in day_track
                            if st.session_state.checked.get(s[0], False))
            day_total = len(day_track)
            all_done  = day_done == day_total and day_total > 0
            is_today  = TODAY_NUM == dnum
            has_exam  = any("school exam" in s[5].lower() for s in sessions)

            icon  = "📍" if is_today else ("✅" if all_done else ("⭐" if has_exam else "📅"))
            prog  = f"{day_done} / {day_total} done" if day_total else ""
            label = f"{icon}  {dlabel}    {prog}"
            auto_open = is_today or (
                TODAY_NUM is not None and dnum <= TODAY_NUM and not all_done
            )

            with st.expander(label, expanded=bool(auto_open)):
                for row in sessions:
                    sid, _, _, _, time, act, subj, topic, dur, note = row
                    is_checkable = act.lower() not in ("travel","free")
                    checked      = st.session_state.checked.get(sid, False)
                    tag_bg, tag_fg, border = clr(act, subj)
                    tlabel = tag(act, subj)

                    col_cb, col_card = st.columns([0.04, 0.96])
                    with col_cb:
                        if is_checkable:
                            st.checkbox("", key=f"cb_{sid}", value=checked,
                                        on_change=on_toggle, args=(sid,))
                    with col_card:
                        done_cls  = "done" if (checked and is_checkable) else ""
                        note_html = f'<div class="snote">💬 {note}</div>' if note else ""
                        st.markdown(f"""
                        <div class="scard {done_cls}"
                             style="border-left-color:{border};">
                          <span class="stag"
                                style="background:{tag_bg};color:{tag_fg};">{tlabel}</span>
                          <div class="smeta">⏰ {time} &nbsp;·&nbsp; {dur}</div>
                          <div class="stopic">{topic}</div>
                          {note_html}
                        </div>""", unsafe_allow_html=True)

        if phase_key == "Main Sprint":
            st.info(
                "**Mon – Thu:** home 1:45 pm · break till 2:30 · "
                "study 2:30 – 4:15 (1 h 45 m) · Laksh 4:15 pm\n\n"
                "**Mon / Wed evenings:** Laksh home ~7:30 · study 7:30 – 9:00\n\n"
                "**Fri:** study 2:30 – 7:00 (no Laksh)\n\n"
                "**Sat:** morning 9:00 – 11:30 · Centum 12:30 – 4:30 · "
                "home ~5:15 · study 5:45 – 7:45"
            )