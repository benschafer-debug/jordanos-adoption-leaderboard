#!/usr/bin/env python3
"""Build the Jordano's Digital Adoption Leaderboard as a standalone index.html.

Reads data.json (refreshed from Snowflake by the daily routine) and writes a
self-contained public web page. No build step, no dependencies -- just Python 3.

data.json schema:
{
  "meta":  {"window_label": "last 90 days", "generated": "2026-09-03", "goal": 90},
  "team":  {"combined": 61, "self_serve": 41, "oa": 20, "reps": 42},
  "reps":  [{"rank":1,"name":"...","orders":803,
             "self_serve":0.4159,"oa":0.5691,"rep_entered":0.0149,
             "combined":0.9851,"seg":"Established"}, ...]   # sorted by rank
}
Rates are fractions (0..1). The page ranks ALL reps and splits into two columns.
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))

def load():
    with open(os.path.join(HERE, "data.json")) as f:
        return json.load(f)

def row_html(r, goal):
    ss = r["self_serve"] * 100
    oa = r["oa"] * 100
    rep = r["rep_entered"] * 100
    comb = round(r["combined"] * 100)
    medal = {1: "gold", 2: "silver", 3: "bronze"}.get(r["rank"], "")
    hit = " hit" if comb >= goal else ""
    lowvol = '<span class="tag">low vol</span>' if r.get("seg") == "Low volume" else ""
    name = html.escape(r["name"])
    tip = (f"{name} — {comb}% combined  |  self-serve {round(ss)}%  ·  "
           f"Order Agent {round(oa)}%  ·  rep-entered {round(rep)}%  ·  "
           f"{r['orders']:,} Pepper orders")
    return f'''      <div class="row{hit}" title="{tip}">
        <div class="rank {medal}">{r['rank']}</div>
        <div class="name">{name}{lowvol}</div>
        <div class="track">
          <div class="seg self" style="width:{ss:.2f}%"></div>
          <div class="seg oa" style="width:{oa:.2f}%"></div>
          <div class="seg rep" style="width:{rep:.2f}%"></div>
          <div class="gline"></div>
        </div>
        <div class="val">{comb}<span class="pctsign">%</span></div>
      </div>'''

def build():
    d = load()
    meta, team, reps = d["meta"], d["team"], d["reps"]
    goal = meta.get("goal", 90)
    reps = sorted(reps, key=lambda r: r["rank"])
    n = len(reps)
    half = (n + 1) // 2
    col1 = "\n".join(row_html(r, goal) for r in reps[:half])
    col2 = "\n".join(row_html(r, goal) for r in reps[half:])
    colhead = ('<div class="colhead"><span>#</span><span>Rep</span>'
               '<span class="ch-track">Order mix<span class="ch-goal">'
               f'{goal}%</span></span><span class="ch-val">Combined</span></div>')

    doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Jordano's Digital Adoption Leaderboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap">
<style>
:root{{
  --ground:#EAE8DF; --panel:#FFFFFF; --panel-2:#F4F2EA;
  --ink:#04180E; --muted:#5E6B5F; --line:#E1DFD4;
  --self:#0F8E42; --oa:#83DE86; --rep:#CFCFBE; --goal:#DA5000;
  --hit:#E6F6EA;
  --head-bg:#002710; --head-2:#013A18; --head-ink:#FFFFFF; --head-accent:#95F596; --head-muted:#9FCBAB;
  --shadow:0 1px 2px rgba(0,20,8,.06),0 1px 1px rgba(0,20,8,.04);
}}
@media (prefers-color-scheme: dark){{
  :root{{
    --ground:#05130C; --panel:#0B2216; --panel-2:#0E2A1B;
    --ink:#EAF3EC; --muted:#8DA492; --line:#173a28;
    --self:#1FA355; --oa:#8CE68D; --rep:#40584A; --goal:#FF6A2C;
    --hit:#0f3320;
    --head-bg:#02160B; --head-2:#052916; --head-ink:#FFFFFF; --head-accent:#95F596; --head-muted:#8FBF9D;
    --shadow:0 1px 2px rgba(0,0,0,.4);
  }}
}}
*{{box-sizing:border-box}}
html,body{{margin:0}}
body{{background:var(--ground);color:var(--ink);
  font-family:Inter,system-ui,-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;line-height:1.3}}
img{{max-width:100%}}
.wrap{{max-width:1500px;margin:0 auto;padding:clamp(14px,2vw,26px)}}
.head{{background:linear-gradient(135deg,var(--head-bg),var(--head-2));
  color:var(--head-ink);border-radius:16px;padding:clamp(18px,2.4vw,30px) clamp(20px,2.6vw,34px);
  box-shadow:var(--shadow);position:relative;overflow:hidden}}
.eyebrow{{font-family:Archivo;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  font-size:12px;color:var(--head-accent)}}
h1{{font-family:Archivo;font-weight:900;letter-spacing:-.015em;margin:.15em 0 0;
  font-size:clamp(28px,4vw,48px);line-height:1;text-wrap:balance}}
.sub{{color:var(--head-muted);font-size:clamp(13px,1.1vw,15px);margin-top:.5em;max-width:74ch}}
.chips{{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}}
.chip{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);
  border-radius:11px;padding:9px 15px;min-width:104px}}
.chip .k{{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--head-muted)}}
.chip .v{{font-family:Archivo;font-weight:800;font-size:clamp(20px,2.2vw,27px);line-height:1.1;
  font-variant-numeric:tabular-nums}}
.chip.goal .v{{color:var(--goal)}}
.chip.big .v{{color:var(--head-accent)}}
.legend{{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin:16px 2px 6px;
  font-size:12.5px;color:var(--muted)}}
.legend b{{color:var(--ink);font-weight:600}}
.key{{display:inline-flex;align-items:center;gap:7px}}
.sw{{width:15px;height:15px;border-radius:4px;display:inline-block}}
.sw.self{{background:var(--self)}} .sw.oa{{background:var(--oa)}} .sw.rep{{background:var(--rep)}}
.sw.goal{{width:3px;height:16px;border-radius:0;background:var(--goal)}}
.board{{display:grid;grid-template-columns:1fr 1fr;gap:clamp(14px,1.6vw,26px);margin-top:8px}}
.col{{background:var(--panel);border:1px solid var(--line);border-radius:14px;
  padding:8px 12px 12px;box-shadow:var(--shadow)}}
.colhead{{display:grid;grid-template-columns:38px 158px 1fr 56px;align-items:end;gap:12px;
  padding:6px 4px 8px;border-bottom:1px solid var(--line);
  font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:600}}
.colhead .ch-track{{text-align:left;position:relative}}
.colhead .ch-goal{{position:absolute;left:{goal}%;transform:translateX(-50%);color:var(--goal);
  font-family:Archivo;font-weight:700;white-space:nowrap}}
.colhead .ch-val{{text-align:right}}
.row{{display:grid;grid-template-columns:38px 158px 1fr 56px;align-items:center;gap:12px;
  padding:5px 4px;border-bottom:1px solid var(--line)}}
.row:last-child{{border-bottom:0}}
.row.hit{{background:var(--hit)}}
.rank{{font-family:Archivo;font-weight:800;font-size:17px;text-align:center;color:var(--muted);
  font-variant-numeric:tabular-nums}}
.rank.gold{{color:#C79A24}} .rank.silver{{color:#8C9398}} .rank.bronze{{color:#B26A38}}
.name{{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  display:flex;align-items:center;gap:8px}}
.tag{{font-size:9.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
  color:var(--muted);border:1px solid var(--line);border-radius:20px;padding:1px 7px;flex:none}}
.track{{position:relative;display:flex;height:17px;border-radius:5px;overflow:hidden;
  background:var(--panel-2)}}
.seg{{height:100%}}
.seg.self{{background:var(--self)}} .seg.oa{{background:var(--oa)}} .seg.rep{{background:var(--rep)}}
.seg+.seg{{box-shadow:-1px 0 0 var(--panel)}}
.gline{{position:absolute;top:-2px;bottom:-2px;left:{goal}%;width:2px;background:var(--goal);
  opacity:.92;z-index:2}}
.val{{font-family:Archivo;font-weight:800;font-size:18px;text-align:right;
  font-variant-numeric:tabular-nums;color:var(--ink)}}
.row.hit .val{{color:var(--self)}}
.pctsign{{font-size:12px;font-weight:600;color:var(--muted);margin-left:1px}}
.foot{{margin:16px 4px 4px;font-size:11.5px;color:var(--muted);display:flex;
  flex-wrap:wrap;gap:6px 18px;justify-content:space-between}}
@media (max-width:820px){{ .board{{grid-template-columns:1fr}} }}
</style>
</head>
<body>
<div class="wrap">
  <header class="head">
    <div class="eyebrow">Jordano's Foodservice · Sales Team</div>
    <h1>Digital Adoption Leaderboard</h1>
    <p class="sub">Share of each rep's Pepper orders that came in <b style="color:var(--head-ink)">without the rep keying them</b> — the customer placed it themselves, or it came through Order Agent. The rest is manual, rep-entered ordering. Goal: {goal}%.</p>
    <div class="chips">
      <div class="chip big"><div class="k">Team combined</div><div class="v">{team['combined']}%</div></div>
      <div class="chip"><div class="k">Customer self-serve</div><div class="v">{team['self_serve']}%</div></div>
      <div class="chip"><div class="k">Order Agent</div><div class="v">{team['oa']}%</div></div>
      <div class="chip goal"><div class="k">Goal</div><div class="v">{goal}%</div></div>
      <div class="chip"><div class="k">Reps ranked</div><div class="v">{team['reps']}</div></div>
    </div>
  </header>
  <div class="legend">
    <span class="key"><span class="sw self"></span> <b>Customer self-serve</b></span>
    <span class="key"><span class="sw oa"></span> <b>Order Agent</b></span>
    <span class="key"><span class="sw rep"></span> <b>Rep-entered (manual)</b></span>
    <span class="key"><span class="sw goal"></span> {goal}% goal</span>
    <span style="margin-left:auto">Combined % = self-serve + Order Agent</span>
  </div>
  <div class="board">
    <section class="col">
      {colhead}
{col1}
    </section>
    <section class="col">
      {colhead}
{col2}
    </section>
  </div>
  <div class="foot">
    <span>{meta['window_label'].capitalize()} · Pepper orders only (offline / ERP invoice excluded). Order Agent counts whether the rep or the customer submitted it.</span>
    <span>Updated {meta['generated']} · Hover a rep for the full breakdown</span>
  </div>
</div>
</body>
</html>'''
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(doc)
    print(f"Built index.html — {n} reps, generated {meta['generated']}")

if __name__ == "__main__":
    build()
