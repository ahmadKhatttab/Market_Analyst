import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json

from database import db_session
from models import CarAd

# 1.Backend 

@st.cache_data(ttl=300)
def load_and_enrich_data() -> pd.DataFrame:
    """
    Retrieves car listings from the database and applies feature engineering.
    Cached for 5 minutes — no DB hit on every filter interaction.
    """
    try:
        query = db_session.query(CarAd).all()
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return pd.DataFrame()

    if not query:
        return pd.DataFrame()

    data = [
        {
            "id":        car.id,
            "title":     car.title,
            "brand":     car.brand,
            "model":     car.model,
            "year":      car.year,
            "price":     car.price,
            "mileage":   car.mileage,
            "fuel_type": car.fuel_type,
            "city":      car.city,
        }
        for car in query
    ]

    df = pd.DataFrame(data)

    
    for col in ("price", "mileage", "year"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["price", "mileage", "year"])
    df = df[df["price"] > 0].copy()

    # Feature engineering
    df["vehicle_age"]    = (2026 - df["year"]).astype(int)
    df["annual_mileage"] = df["mileage"] / df["vehicle_age"].replace(0, 1)
    df["price_per_km"]   = (df["price"] / df["mileage"].replace(0, 1)).round(3)

    def tier(p):
        if p < 5000:  return "اقتصادية"
        if p < 12000: return "متوسطة"
        if p < 25000: return "فوق المتوسط"
        if p < 50000: return "فاخرة"
        return "فاخرة جداً"
    df["price_tier"] = df["price"].apply(tier)

    return df

# إعدادات الصفحة

st.set_page_config(
    page_title="Market_Analyst",
   
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        iframe { border: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

col_refresh, _ = st.columns([1, 9])
with col_refresh:
    if st.button(" تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

df_market = load_and_enrich_data()

if df_market.empty:
    st.warning("قاعدة البيانات فارغة ")
    st.stop()


tab_dash, tab_data = st.tabs(["لوحة التحكم", "  Raw Data  "])

with tab_dash:
    cars_json = json.dumps(
        df_market[[
            "id", "title", "brand", "model", "year", "price",
            "mileage", "fuel_type", "city", "vehicle_age", "price_tier"
        ]].to_dict(orient="records"),
        ensure_ascii=False,
    )

    CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #f4f3ef; --surface: #ffffff;
    --border: rgba(0,0,0,0.08); --border-md: rgba(0,0,0,0.14);
    --text: #1a1a18; --muted: #6b6b66; --hint: #9d9d98;
    --accent: #1a56db; --accent-lt: #e8f0fe;
    --green: #3b6d11; --green-lt: #eaf3de;
    --amber: #854f0b; --amber-lt: #faeeda;
    --red: #a32d2d; --red-lt: #fcebeb;
    --radius: 10px; --radius-sm: 6px;
  }
  body { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5; }
  .page { padding: 20px 24px 40px; max-width: 1200px; margin: 0 auto; }
  .page-title { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
  .page-sub { font-size: 13px; color: var(--muted); margin-bottom: 20px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; align-items: center; }
  .search-wrap { position: relative; flex: 1; min-width: 200px; }
  .search-wrap i { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: var(--hint); font-size: 16px; pointer-events: none; }
  input[type=text] { width: 100%; padding: 9px 36px 9px 12px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: 14px; background: var(--surface); color: var(--text); outline: none; transition: border-color .15s; }
  input[type=text]:focus { border-color: var(--accent); }
  input[type=text]::placeholder { color: var(--hint); }
  select { padding: 8px 12px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: 13px; background: var(--surface); color: var(--text); cursor: pointer; outline: none; }
  select:focus { border-color: var(--accent); }
  .clear-btn { padding: 8px 14px; border: 1px solid var(--border-md); border-radius: var(--radius-sm); font-size: 13px; background: var(--surface); color: var(--muted); cursor: pointer; display: flex; align-items: center; gap: 5px; transition: background .15s; white-space: nowrap; }
  .clear-btn:hover { background: var(--bg); color: var(--text); }
  .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
  @media(max-width:700px) { .metrics { grid-template-columns: repeat(2,1fr); } }
  .metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }
  .metric-label { font-size: 11px; font-weight: 600; color: var(--hint); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 8px; display: flex; align-items: center; gap: 5px; }
  .metric-value { font-size: 26px; font-weight: 700; color: var(--text); line-height: 1; margin-bottom: 4px; }
  .metric-sub { font-size: 12px; color: var(--muted); }
  
  /*  تقسيم إلى قسمين متساويين بدلاً من ثلاثة */
  .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
  @media(max-width:800px) { .charts-row { grid-template-columns: 1fr; } }
  
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
  .card-title { font-size: 12px; font-weight: 600; color: var(--hint); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 14px; }
  .dist-bars { display: flex; align-items: flex-end; gap: 3px; height: 90px; }
  .dist-bin { flex: 1; border-radius: 3px 3px 0 0; background: var(--accent); opacity: .75; cursor: pointer; transition: opacity .15s; position: relative; }
  .dist-bin:hover { opacity: 1; }
  .dist-bin:hover::after { content: attr(data-tip); position: absolute; bottom: calc(100% + 4px); left: 50%; transform: translateX(-50%); background: var(--text); color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 4px; white-space: nowrap; pointer-events: none; z-index: 10; }
  .dist-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--hint); margin-top: 4px; }
  .tier-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
  .tier-pill { padding: 4px 10px; border-radius: 99px; font-size: 11px; font-weight: 600; cursor: pointer; border: 1px solid transparent; transition: all .15s; }
  .tier-pill:hover { opacity: .8; }
  .brand-list { display: flex; flex-direction: column; gap: 8px; }
  .brand-row { display: flex; align-items: center; gap: 8px; }
  .brand-name { font-size: 12px; color: var(--muted); width: 70px; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .brand-track { flex: 1; height: 22px; background: var(--bg); border-radius: var(--radius-sm); overflow: hidden; }
  .brand-fill { height: 100%; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; font-size: 11px; font-weight: 600; transition: width .5s ease; white-space: nowrap; }
  .brand-count { font-size: 11px; color: var(--hint); width: 42px; text-align: right; }
  .table-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
  .table-header-bar { padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
  .table-header-bar span:first-child { font-size: 12px; font-weight: 600; color: var(--hint); text-transform: uppercase; letter-spacing: .04em; }
  .results-badge { background: var(--accent-lt); color: var(--accent); font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 99px; }
  .table-scroll { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: right; padding: 10px 14px; font-size: 11px; font-weight: 600; color: var(--hint); text-transform: uppercase; letter-spacing: .03em; background: var(--bg); border-bottom: 1px solid var(--border); }
  td { padding: 11px 14px; border-bottom: 1px solid var(--border); color: var(--text); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #fafaf8; }
  .td-title { font-weight: 500; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .td-price { font-weight: 700; color: var(--accent); }
  .td-age { color: var(--muted); font-size: 12px; }
  .badge { display: inline-block; padding: 2px 9px; border-radius: 99px; font-size: 11px; font-weight: 600; }
  .b-blue  { background: var(--accent-lt); color: var(--accent); }
  .b-green { background: var(--green-lt);  color: var(--green);  }
  .b-amber { background: var(--amber-lt);  color: var(--amber);  }
  .b-red   { background: var(--red-lt);    color: var(--red);    }
  .no-data { padding: 40px; text-align: center; color: var(--muted); font-size: 14px; }
"""

    HTML_BODY = """
<div class="page">
  <h1 class="page-title">محلل السوق الذكي</h1>
  <p class="page-sub">تحليل تفاعلي لإعلانات السيارات المسحوبة من OpenSooq</p>

  <div class="controls">
    <div class="search-wrap">
      <i class="ti ti-search"></i>
      <input type="text" id="q" placeholder="ابحث عن ماركة أو موديل..."/>
    </div>
    <select id="selBrand"><option value="">كل الماركات</option></select>
    <select id="selYear"><option value="">كل السنوات</option></select>
    <select id="selSort">
      <option value="price_asc">السعر &#x2191;</option>
      <option value="price_desc">السعر &#x2193;</option>
      <option value="year_desc">الأحدث أولاً</option>
      <option value="mile_asc">أقل مسافة</option>
    </select>
    <button class="clear-btn" onclick="clearAll()">
      <i class="ti ti-x" style="font-size:14px"></i> مسح
    </button>
  </div>

  <div style="margin-bottom:6px;font-size:11px;font-weight:600;color:var(--hint);text-transform:uppercase;letter-spacing:.04em">تصفية حسب الفئة السعرية</div>
  <div class="tier-row" id="tierRow"></div>

  <div class="metrics">
    <div class="metric-card">
      <div class="metric-label"><i class="ti ti-list-numbers" style="font-size:14px"></i> الإعلانات</div>
      <div class="metric-value" id="mTotal">&#x2014;</div>
      <div class="metric-sub" id="mTotalSub">من قاعدة البيانات</div>
    </div>
    <div class="metric-card">
      <div class="metric-label"><i class="ti ti-coin" style="font-size:14px"></i> متوسط السعر</div>
      <div class="metric-value" id="mAvg">&#x2014;</div>
      <div class="metric-sub">دينار أردني</div>
    </div>
    <div class="metric-card">
      <div class="metric-label"><i class="ti ti-trending-down" style="font-size:14px"></i> أدنى سعر</div>
      <div class="metric-value" id="mMin">&#x2014;</div>
      <div class="metric-sub" id="mMinSub">&#x2014;</div>
    </div>
    <div class="metric-card">
      <div class="metric-label"><i class="ti ti-road" style="font-size:14px"></i> متوسط المسافة</div>
      <div class="metric-value" id="mMile">&#x2014;</div>
      <div class="metric-sub">كيلومتر</div>
    </div>
  </div>

  <div class="charts-row">
    <div class="card">
      <div class="card-title">توزيع الأسعار</div>
      <div class="dist-bars" id="distBars"></div>
      <div class="dist-labels" id="distLabels"></div>
    </div>
    <div class="card">
      <div class="card-title">الماركات — متوسط السعر</div>
      <div class="brand-list" id="brandList"></div>
    </div>
  </div>

  <div class="table-card">
    <div class="table-header-bar">
      <span>قائمة الإعلانات</span>
      <span class="results-badge" id="tableCount">0 نتيجة</span>
    </div>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>العنوان</th><th>الماركة</th><th>السنة</th>
            <th>السعر (JOD)</th><th>المسافة (كم)</th>
            <th>الفئة</th><th>الوقود</th><th>المدينة</th><th>العمر</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
</div>
"""

    JS_TEMPLATE = """
const ALL = CARS_DATA_PLACEHOLDER;

const TIER_COLORS = {
  'اقتصادية':    ['#eaf3de','#3b6d11'],
  'متوسطة':      ['#e8f0fe','#1a56db'],
  'فوق المتوسط': ['#faeeda','#854f0b'],
  'فاخرة':       ['#fcebeb','#a32d2d'],
  'فاخرة جداً':  ['#f3e8ff','#6d28d9'],
};

function unique(key) { return [...new Set(ALL.map(c => c[key]))].sort(); }
function fillSelect(id, vals) {
  const el = document.getElementById(id);
  vals.forEach(v => { const o = document.createElement('option'); o.value=v; o.textContent=v; el.appendChild(o); });
}
fillSelect('selBrand', unique('brand'));
fillSelect('selYear',  unique('year').reverse());

// Tier pills
let activeTier = '';
const TIER_ORDER = ['اقتصادية','متوسطة','فوق المتوسط','فاخرة','فاخرة جداً'];
function buildTiers() {
  const tiers = new Set(ALL.map(c => c.price_tier));
  const el = document.getElementById('tierRow');
  el.innerHTML = TIER_ORDER.filter(t => tiers.has(t)).map(t => {
    const [bg, col] = TIER_COLORS[t] || ['#f1efe8','#5f5e5a'];
    return `<span class="tier-pill" data-tier="${t}"
      style="background:${bg};color:${col};border-color:${col}33"
      onclick="toggleTier('${t}')">${t}</span>`;
  }).join('');
}
function toggleTier(t) {
  activeTier = activeTier === t ? '' : t;
  document.querySelectorAll('.tier-pill').forEach(p => {
    const on = p.dataset.tier === activeTier;
    p.style.opacity      = activeTier && !on ? '0.4' : '1';
    p.style.fontWeight   = on ? '700' : '600';
    p.style.borderWidth  = on ? '2px' : '1px';
  });
  render();
}
buildTiers();

// Filtering
function getFiltered() {
  const q     = document.getElementById('q').value.toLowerCase();
  const brand = document.getElementById('selBrand').value;
  const year  = document.getElementById('selYear').value;
  const sort  = document.getElementById('selSort').value;
  let rows = ALL.filter(c => {
    if (brand && c.brand     !== brand) return false;
    if (year  && String(c.year) !== year) return false;
    if (activeTier && c.price_tier !== activeTier) return false;
    if (q && ![c.title,c.brand,c.model,c.city].some(v=>v.toLowerCase().includes(q))) return false;
    return true;
  });
  if (sort==='price_asc')  rows.sort((a,b)=>a.price  -b.price);
  if (sort==='price_desc') rows.sort((a,b)=>b.price  -a.price);
  if (sort==='year_desc')  rows.sort((a,b)=>b.year   -a.year);
  if (sort==='mile_asc')   rows.sort((a,b)=>a.mileage-b.mileage);
  return rows;
}

function renderKPIs(rows) {
  const n = rows.length;
  document.getElementById('mTotal').textContent    = n.toLocaleString();
  document.getElementById('mTotalSub').textContent = `من ${ALL.length} إعلان`;
  if (!n) {
    ['mAvg','mMin','mMile'].forEach(id => document.getElementById(id).textContent = '—');
    document.getElementById('mMinSub').textContent = '—'; return;
  }
  const avg  = Math.round(rows.reduce((s,c)=>s+c.price,    0)/n);
  const min  = rows.reduce((a,b)=>a.price<b.price?a:b);
  const mile = Math.round(rows.reduce((s,c)=>s+c.mileage, 0)/n);
  document.getElementById('mAvg').textContent         = avg.toLocaleString();
  document.getElementById('mMin').textContent         = min.price.toLocaleString();
  document.getElementById('mMinSub').textContent      = `${min.brand} ${min.year}`;
  document.getElementById('mMile').textContent        = mile.toLocaleString();
}

function renderDist(rows) {
  const el=document.getElementById('distBars'), lb=document.getElementById('distLabels');
  if (!rows.length) { el.innerHTML='<span style="color:#9d9d98;font-size:12px">لا بيانات</span>'; lb.innerHTML=''; return; }
  const prices=rows.map(c=>c.price), mn=Math.min(...prices), mx=Math.max(...prices);
  const BINS=9, step=(mx-mn)/BINS||1, counts=Array(BINS).fill(0);
  prices.forEach(p=>{ const i=Math.min(Math.floor((p-mn)/step),BINS-1); counts[i]++; });
  const maxC=Math.max(...counts)||1;
  el.innerHTML=counts.map((c,i)=>{
    const h=Math.round((c/maxC)*82)+4;
    const tip=`${Math.round(mn+i*step).toLocaleString()}–${Math.round(mn+(i+1)*step).toLocaleString()} JOD (${c})`;
    return `<div class="dist-bin" style="height:${h}px" data-tip="${tip}"></div>`;
  }).join('');
  lb.innerHTML=`<span>${Math.round(mn).toLocaleString()}</span><span>${Math.round(mx).toLocaleString()} JOD</span>`;
}

function renderBrands(rows) {
  const el=document.getElementById('brandList');
  if (!rows.length) { el.innerHTML='<span style="color:#9d9d98;font-size:12px">لا بيانات</span>'; return; }
  const map={};
  rows.forEach(c=>{ if(!map[c.brand]) map[c.brand]={sum:0,count:0}; map[c.brand].sum+=c.price; map[c.brand].count++; });
  const avgs=Object.entries(map).map(([b,d])=>({brand:b,avg:Math.round(d.sum/d.count),count:d.count})).sort((a,b)=>b.avg-a.avg).slice(0,7);
  const maxA=avgs[0]?.avg||1;
  const pal=['#1a56db','#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#dbeafe'];
  const txt=['#fff','#fff','#fff','#1e3a6e','#1e3a6e','#1e3a6e','#1e3a6e'];
  el.innerHTML=avgs.map((b,i)=>{
    const w=Math.round(b.avg/maxA*100);
    return `<div class="brand-row">
      <span class="brand-name">${b.brand}</span>
      <div class="brand-track">
        <div class="brand-fill" style="width:${w}%;background:${pal[i]};color:${txt[i]}">
          ${w>25?b.avg.toLocaleString()+' JOD':''}
        </div>
      </div>
      <span class="brand-count">${b.count} ✦</span>
    </div>`;
  }).join('');
}

const FUEL_BADGE={'بنزين':'b-blue','ديزل':'b-amber','هجين':'b-green','كهرباء':'b-red'};
function renderTable(rows) {
  document.getElementById('tableCount').textContent=`${rows.length} نتيجة`;
  const tb=document.getElementById('tbody');
  if (!rows.length) { tb.innerHTML=`<tr><td colspan="9"><div class="no-data">لا توجد نتائج تطابق الفلاتر المختارة</div></td></tr>`; return; }
  tb.innerHTML=rows.slice(0,20).map(c=>{
    const [tbg,tcol]=TIER_COLORS[c.price_tier]||['#f1efe8','#5f5e5a'];
    return `<tr>
      <td class="td-title" title="${c.title}">${c.title}</td>
      <td>${c.brand}</td><td>${c.year}</td>
      <td class="td-price">${c.price.toLocaleString()}</td>
      <td>${c.mileage.toLocaleString()}</td>
      <td><span class="badge" style="background:${tbg};color:${tcol}">${c.price_tier}</span></td>
      <td><span class="badge ${FUEL_BADGE[c.fuel_type]||'b-blue'}">${c.fuel_type}</span></td>
      <td>${c.city}</td>
      <td class="td-age">${c.vehicle_age} سنة</td>
    </tr>`;
  }).join('');
}

function render() {
  const rows=getFiltered();
  renderKPIs(rows); renderDist(rows); renderBrands(rows); renderTable(rows);
}

function clearAll() {
  document.getElementById('q').value='';
  ['selBrand','selYear'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('selSort').value='price_asc';
  activeTier='';
  document.querySelectorAll('.tier-pill').forEach(p=>{ p.style.opacity='1'; p.style.fontWeight='600'; p.style.borderWidth='1px'; });
  render();
}

document.getElementById('q').addEventListener('input', render);
['selBrand','selYear','selSort'].forEach(id=>
  document.getElementById(id).addEventListener('change', render)
);
render();
"""

    js_code = JS_TEMPLATE.replace("CARS_DATA_PLACEHOLDER", cars_json)

    html_code = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"/>
<link rel="stylesheet" href="https://unpkg.com/@tabler/icons-webfont@latest/tabler-icons.min.css"/>
<style>{CSS}</style>
</head>
<body>
{HTML_BODY}
<script>{js_code}</script>
</body>
</html>"""

    components.html(html_code, height=1100, scrolling=True)

# Tab 2 — البيانات الخام: بحث + ترتيب + تصدير CSV

with tab_data:
    st.markdown("### البيانات الخام")

    search_raw = st.text_input(" بحث نصي", placeholder="ابحث في العنوان أو الماركة أو المدينة...")

    col_sort, col_dir = st.columns([2, 1])
    with col_sort:
        sort_col = st.selectbox("ترتيب حسب", ["price", "year", "mileage", "vehicle_age"])
    with col_dir:
        ascending = st.selectbox("الاتجاه", ["تنازلي ↓", "تصاعدي ↑"]) == "تصاعدي ↑"

    df_raw = df_market.copy()
    if search_raw:
        mask = df_raw[["title", "brand", "model", "city"]].apply(
            lambda col: col.str.contains(search_raw, case=False, na=False)
        ).any(axis=1)
        df_raw = df_raw[mask]

    df_raw = df_raw.sort_values(sort_col, ascending=ascending)

    display_cols = [
        "title", "brand", "model", "year", "price", "mileage",
        "fuel_type", "city", "vehicle_age", "price_tier", "price_per_km",
    ]
    st.dataframe(df_raw[display_cols], use_container_width=True, height=500)

    st.download_button(
        label="⬇ تحميل كـ CSV",
        data=df_raw[display_cols].to_csv(index=False, encoding="utf-8-sig"),
        file_name="car_market_data.csv",
        mime="text/csv",
    )