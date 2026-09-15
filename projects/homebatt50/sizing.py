#!/usr/bin/env python3
"""HomeBatt50 sizing: loads -> battery/panel/MPPT/wires/fuses + 4 SVG drawings."""
import json

LOADS = [('LED 4x', 4 * 5, 5), ('fan DC', 30, 8), ('phones', 10, 2),
         ('TV', 50, 3), ('router/misc', 5, 8)]
E_DAY = sum(w * h for _, w, h in LOADS)
BATT_WH, DOD = 12.8 * 50, 0.90
autonomy = BATT_WH * DOD / E_DAY
print(f'loads {E_DAY}Wh/day -> autonomy {autonomy:.2f} days')
assert autonomy >= 1.0, 'must cover a full day'

SUN_H, EFF = 5.5, 0.72
need = E_DAY * 1.4
PANEL = next(w for w in (150, 200, 300, 400) if w * SUN_H * EFF >= need)
MPPT = next(a for a in (10, 20, 30, 40) if a >= PANEL / 12.8 * 1.25)
day_load_while_sun = 200
recharge_h = (1 - 0.2) * BATT_WH / (PANEL * EFF - day_load_while_sun / SUN_H)
print(f'panel {PANEL}W + MPPT {MPPT}A; recharge 20->100% in {recharge_h:.1f}h sun')
assert recharge_h < SUN_H, 'must refill within one sun-day'


def vdrop(i, l_m, a_mm2, v_sys):
    return 2 * 0.0172 * l_m * i / a_mm2 / v_sys * 100


WIRES = {'panel_4mm2': vdrop(PANEL / 18, 4, 4, 18),
         'batt_25mm2': vdrop(80, 1, 25, 12.8),
         'dc_2p5mm2': vdrop(8, 3, 2.5, 12.8)}
print('voltage drops %:', {k: round(v, 2) for k, v in WIRES.items()})
assert all(v < 3 for v in WIRES.values()), 'drops < 3%'
FUSES = {'main': 100, 'charge': 25, 'panel': 15, 'dc': 10}
assert FUSES['main'] > 1000 / 12.8 and FUSES['charge'] > MPPT, 'fuse margins'

# ---------------- SVG drawings ----------------
TAH = 'font-family="Tahoma" font-size="12"'


def box(el, x, y, w, h, fill, lines, tx='#e2e8f0'):
    el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="#64748b"/>')
    for i, ln in enumerate(lines):
        el.append(f'<text x="{x + 8}" y="{y + 22 + i * 18}" fill="{tx}" {TAH}>{ln}</text>')


def wire(el, x1, y1, x2, y2, lb='', c='#f87171'):
    el.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="2.5"/>')
    if lb:
        el.append(f'<text x="{(x1 + x2) / 2 - 20}" y="{(y1 + y2) / 2 - 5}" fill="#94a3b8" {TAH}>{lb}</text>')


# 1. wiring
e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="540" {TAH}>',
     '<rect width="780" height="540" fill="#0b1220"/>',
     f'<text x="20" y="28" fill="#fff" font-size="15">مخطط التوصيل الكامل — {PANEL}W / {MPPT}A / 4S 50Ah</text>']
box(e, 20, 60, 150, 90, '#1e3a5f', [f'لوح شمسي {PANEL}W', 'Vmp~18V / 11A', 'ميل 14° جنوبًا'])
box(e, 200, 70, 100, 70, '#713f12', ['قاطع DC', '15A', 'للألواح'])
box(e, 330, 60, 150, 90, '#14532d', [f'MPPT {MPPT}A', 'شمسي←بطارية', '4mm²'])
box(e, 330, 250, 190, 150, '#3b0764', ['بطارية 4S 50Ah', '12.8V / 640Wh', 'BMS 100A داخلي', 'فيوز شحن 25A'])
box(e, 560, 250, 170, 120, '#7c2d12', ['انفرتر 1kW', 'جيبي نقي', 'فيوز 100A / 25mm²'])
box(e, 60, 250, 150, 120, '#0c4a6e', ['أحمال DC 12V', 'LED + مروحة', 'فيوز 10A / 2.5mm²'])
box(e, 560, 400, 170, 70, '#27272a', ['أحمال AC', 'TV + شواحن'])
wire(e, 170, 105, 200, 105, '4mm²')
wire(e, 300, 105, 330, 105)
wire(e, 405, 150, 405, 250, '25A')
wire(e, 520, 300, 560, 300, '100A')
wire(e, 645, 370, 645, 400)
wire(e, 330, 300, 210, 300, '10A')
wire(e, 405, 400, 405, 470)
e.append('<line x1="365" y1="470" x2="445" y2="470" stroke="#4ade80" stroke-width="3"/>')
e.append('<line x1="380" y1="478" x2="430" y2="478" stroke="#4ade80" stroke-width="3"/>')
e.append(f'<text x="330" y="500" fill="#4ade80" {TAH}>تأريض إجباري (قضيب + 6mm²)</text>')
e.append(f'<text x="20" y="520" fill="#94a3b8" {TAH}>الأحمر=موجب (الأسود=سالب موازٍ لكل خط) | هبوط الجهد ‏{WIRES["batt_25mm2"]:.2f}% فقط</text>')
e.append('</svg>')
open('wiring.svg', 'w', encoding='utf-8').write('\n'.join(e))

# 2. battery pack
e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="660" height="440" {TAH}>',
     '<rect width="660" height="440" fill="#0b1220"/>',
     '<text x="20" y="28" fill="#fff" font-size="15">تجميع البطارية 4S — من اليسار B- إلى اليمين B+</text>']
e.append('<rect x="40" y="120" width="580" height="200" rx="10" fill="none" stroke="#a78bfa" stroke-width="3"/>')
for i in range(4):
    x = 90 + i * 130
    box(e, x, 160, 110, 120, '#1e3a5f', [f'خلية {i + 1}', '3.2V 50Ah', '+|−'])
    e.append(f'<rect x="{x + 10}" y="140" width="90" height="14" fill="#fbbf24"/>')
e.append(f'<text x="90" y="135" fill="#fbbf24" {TAH}>باسبار نحاس (عزم 8Nm + شحم)</text>')
box(e, 90, 40, 530, 60, '#14532d', ['BMS 4S 100A — أسلاك الاستشعار B0(أسود)→B1→B2→B3→B4(أحمر) على التوالي، ثم كابل التوازن!'])
for i in range(5):
    x = 90 + i * 130 - (65 if i else 0) + (65 if i == 0 else 0)
    e.append(f'<line x1="{90 + i * 117}" y1="100" x2="{90 + i * 117}" y2="140" stroke="#4ade80" stroke-width="1.5"/>')
e.append(f'<text x="40" y="360" fill="#f87171" {TAH}>1) وازن الخلايا توازيًا على 3.65V أولًا! 2) ألواح ضغط + شريط 3) صندوق مظلل جيد التهوية</text>')
e.append(f'<text x="40" y="385" fill="#94a3b8" {TAH}>الأطراف: B- أسود يسار ←→ B+ أحمر يمين = 12.8V / BMS يقطع عند 14.6V شحنًا و 10V تفريغًا</text>')
e.append(f'<text x="40" y="410" fill="#94a3b8" {TAH}>⚠ أي شرر على الأطراف = حريق: غطِّ طرفًا أثناء العمل على الآخر</text>')
e.append('</svg>')
open('battery_pack.svg', 'w', encoding='utf-8').write('\n'.join(e))

# 3. mounting
e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="660" height="380" {TAH}>',
     '<rect width="660" height="380" fill="#0b1220"/>',
     '<text x="20" y="28" fill="#fff" font-size="15">التركيب — تعز 13.6° شمالًا: ميل 14° نحو الجنوب</text>']
e.append('<line x1="20" y1="320" x2="640" y2="320" stroke="#64748b" stroke-width="3"/>')
e.append('<rect x="380" y="220" width="200" height="100" fill="#27272a" stroke="#64748b"/>')
e.append(f'<text x="390" y="245" fill="#e2e8f0" {TAH}>غرفة/سطح مظلل</text>')
e.append('<rect x="410" y="260" width="120" height="45" fill="#3b0764" stroke="#a78bfa"/>')
e.append(f'<text x="420" y="287" fill="#e2e8f0" {TAH}>صندوق البطارية + تهوية</text>')
e.append('<line x1="150" y1="320" x2="150" y2="200" stroke="#64748b" stroke-width="5"/>')
e.append('<g transform="rotate(-14 150 200)"><rect x="60" y="188" width="180" height="16" fill="#1e3a5f" stroke="#38bdf8" stroke-width="2"/></g>')
e.append(f'<text x="40" y="360" fill="#94a3b8" {TAH}>قاعدة حديد + اللوح 14° ← الشمس ظهرًا جنوبًا ☀ (نظف الغبار أسبوعيًا!)</text>')
e.append('<line x1="240" y1="200" x2="410" y2="270" stroke="#f87171" stroke-width="2" stroke-dasharray="5,4"/>')
e.append(f'<text x="250" y="250" fill="#94a3b8" {TAH}>كابل 4mm² بمواسير</text>')
e.append('</svg>')
open('mounting.svg', 'w', encoding='utf-8').write('\n'.join(e))

# 4. charge curve
e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="660" height="320" {TAH}>',
     '<rect width="660" height="320" fill="#0b1220"/>',
     '<text x="20" y="28" fill="#fff" font-size="15">منحنى الشحن LiFePO4 (ثابت 13.4V ثم ركبة 14.6V) + يوم شمسي</text>']
X = lambda s: 50 + s / 100 * 560
Y = lambda v: 280 - (v - 12) / 3 * 230
pts = []
for s in range(0, 101, 2):
    v = 13.2 + s * 0.004 if s < 90 else 13.56 + (s - 90) * 0.104
    pts.append(f'{X(s)},{Y(v)}')
e.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#4ade80" stroke-width="3"/>')
e.append(f'<text x="480" y="120" fill="#4ade80" {TAH}>ركبة الامتلاء 14.6V ← BMS يوازن هنا</text>')
pts2 = []
for h in range(0, 13):
    p = max(0, PANEL * (1 - ((h - 6) / 6.5) ** 2))
    pts2.append(f'{50 + h / 12 * 560},{280 - p / PANEL * 200}')
e.append(f'<polyline points="{" ".join(pts2)}" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="6,4"/>')
e.append(f'<text x="80" y="120" fill="#fbbf24" {TAH}>قدرة اللوح {PANEL}W عبر النهار (أصفر متقطع)</text>')
e.append(f'<text x="50" y="305" fill="#94a3b8" {TAH}>شحن كامل من 20% خلال {recharge_h:.1f} ساعات مشمسة</text>')
e.append('</svg>')
open('charge_curve.svg', 'w', encoding='utf-8').write('\n'.join(e))

json.dump({'E_day': E_DAY, 'autonomy_d': round(autonomy, 2), 'panel_W': PANEL,
           'mppt_A': MPPT, 'recharge_h': round(recharge_h, 1), 'fuses': FUSES,
           'drops_pct': {k: round(v, 2) for k, v in WIRES.items()},
           'drawings': ['wiring.svg', 'battery_pack.svg', 'mounting.svg', 'charge_curve.svg']},
          open('results.json', 'w'), indent=1)
print('VERDICT: SIZING [VERIFIED] + 4 drawings written')
