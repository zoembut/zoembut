"""Buat kartu statistik GitHub bergaya pop-art untuk profil zoembut.

Dijalankan oleh GitHub Actions (.github/workflows/profile.yml). Data diambil lewat GraphQL
memakai GITHUB_TOKEN, lalu ditulis ke assets/stats-light.svg dan assets/stats-dark.svg.
Huruf judul memakai font Bangers (SIL Open Font License, lihat Bangers-OFL.txt).
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

USER = os.environ.get('PROFILE_USER', 'zoembut')
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'assets')
YEL, PINK, CYAN, INK = '#FFE500', '#FF2E88', '#21D4FD', '#111111'

QUERY = '''query($login:String!){user(login:$login){createdAt followers{totalCount}
 repositories(ownerAffiliations:OWNER,privacy:PUBLIC){totalCount}
 contributionsCollection{totalCommitContributions totalPullRequestContributions restrictedContributionsCount
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'''


def fetch():
    token = os.environ['GITHUB_TOKEN']
    body = json.dumps({'query': QUERY, 'variables': {'login': USER}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body,
                                 headers={'Authorization': 'bearer ' + token, 'User-Agent': USER + '-profile'})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if 'errors' in data:
        sys.exit('GraphQL: ' + json.dumps(data['errors'])[:300])
    return data['data']['user']


def streaks(days):
    """Runtun terpanjang dan runtun saat ini (hari ini boleh belum ada kontribusi)."""
    best = run = 0
    for d in days:
        run = run + 1 if d['contributionCount'] else 0
        best = max(best, run)
    current = 0
    tail = days[:-1] if days and not days[-1]['contributionCount'] else days
    for d in reversed(tail):
        if not d['contributionCount']:
            break
        current += 1
    return current, best


font = TTFont(os.path.join(HERE, 'Bangers-Regular.ttf'))
GS, CMAP, UPM = font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm


def text_path(text, size, tracking=0.04):
    pen, x, s = SVGPathPen(GS), 0.0, size / UPM
    for ch in text:
        g = CMAP.get(ord(ch)) or CMAP[ord('?')]
        GS[g].draw(TransformPen(pen, (s, 0, 0, -s, x, 0)))
        x += GS[g].width * s + tracking * size
    return pen.getCommands(), x - tracking * size


def card(theme, u, days):
    dark = theme == 'dark'
    paper, line, sub = ('#1B1824', '#FFFFFF', '#C9C3DD') if dark else ('#FFFFFF', INK, '#33303D')
    cc = u['contributionsCollection']
    total = cc['contributionCalendar']['totalContributions']
    current, best = streaks(days)
    active = sum(1 for d in days if d['contributionCount'])
    stats = [
        (f'{total:,}'.replace(',', '.'), 'kontribusi setahun', YEL),
        (str(current), 'hari beruntun', PINK),
        (str(best), 'runtun terpanjang', CYAN),
        (str(active), 'hari aktif', YEL),
    ]
    W, H = 830, 300
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="{total} kontribusi setahun, runtun {current} hari, terpanjang {best} hari, {active} hari aktif">',
           f'<defs><pattern id="ht" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="1.4" fill="{INK}" opacity=".18"/></pattern></defs>',
           f'<rect x="8" y="8" width="{W-12}" height="{H-12}" fill="{"#000" if dark else INK}"/>',
           f'<rect x="2" y="2" width="{W-12}" height="{H-12}" fill="{paper}" stroke="{line}" stroke-width="3.5"/>']
    cw = (W - 12 - 30 - 3 * 14) / 4
    for i, (num, label, col) in enumerate(stats):
        x = 17 + i * (cw + 14)
        d, w = text_path(num, 54)
        out.append(f'<g transform="rotate({(-1.4, 1.1, -0.8, 1.4)[i]} {x+cw/2} 70)">'
                   f'<rect x="{x+4}" y="22" width="{cw}" height="96" fill="{INK}"/>'
                   f'<rect x="{x}" y="18" width="{cw}" height="96" fill="{col}" stroke="{INK}" stroke-width="3"/>'
                   f'<rect x="{x}" y="18" width="{cw}" height="96" fill="url(#ht)"/>'
                   f'<path d="{d}" transform="translate({x+cw/2-w/2} 78)" fill="{INK}"/>'
                   f'<text x="{x+cw/2}" y="102" text-anchor="middle" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
                   f'font-size="14" font-weight="700" fill="{INK}">{label}</text></g>')
    # Grafik batang kontribusi 26 minggu terakhir.
    weeks = [days[i:i + 7] for i in range(max(0, len(days) - 182), len(days), 7)]
    sums = [sum(d['contributionCount'] for d in w) for w in weeks]
    top = max(sums) or 1
    bx, by, bw, bh = 30, 268, (W - 12 - 60) / len(sums), 112
    out.append(f'<text x="30" y="146" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="13" font-weight="700" fill="{sub}">'
               f'Kontribusi per minggu, 26 minggu terakhir</text>')
    colors = [YEL, PINK, CYAN]
    for i, s in enumerate(sums):
        h = max(3, bh * s / top)
        out.append(f'<rect x="{bx+i*bw+2:.1f}" y="{by-h:.1f}" width="{bw-4:.1f}" height="{h:.1f}" fill="{colors[i%3] if s else ("#3A3550" if dark else "#E5E1EE")}" '
                   f'stroke="{INK}" stroke-width="{2 if s else 0}"><title>{s} kontribusi</title></rect>')
    stamp = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).strftime('%d/%m/%Y %H:%M WIB')
    out.append(f'<text x="{W-24}" y="{H-14}" text-anchor="end" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="11" fill="{sub}">diperbarui {stamp}</text>')
    out.append('</svg>')
    return ''.join(out)


def main():
    u = fetch()
    days = [d for w in u['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']]
    os.makedirs(OUT, exist_ok=True)
    for theme in ('light', 'dark'):
        path = os.path.join(OUT, f'stats-{theme}.svg')
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(card(theme, u, days))
        print('ditulis', path)


if __name__ == '__main__':
    main()
