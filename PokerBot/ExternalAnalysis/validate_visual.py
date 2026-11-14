from pathlib import Path
import re,json
p=Path('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c/poker-comparison.html')
s=p.read_text(encoding='utf-8')
configs=[json.loads(x) for x in re.findall(r'<script[^>]*data-viz-chart[^>]*>(.*?)</script>',s,re.S)]
assert len(configs)==3
assert [len(c['rows']) for c in configs]==[7,7,21]
assert all(r['lower']<=r['rate']<=r['upper'] for r in configs[0]['rows'])
assert all(0<=r['rate']<=1 and abs(r['rate']-r['events']/r['opportunities'])<1e-12 for r in configs[2]['rows'])
assert not any(x in s for x in ('__DATA__','__FAST__','__STRICT__','__STYLE__'))
assert len(s.encode())<1000000
ids=re.findall(r'\bid="([^"]+)"',s)
assert len(ids)==len(set(ids))
js=re.search(r'<script type="module">(.*?)</script>',s,re.S).group(1)
Path('PokerBot/ExternalAnalysis/Tournament/visual_script.mjs').write_text(js,encoding='utf-8')
print('Validated three chart payloads, 7 bots, intervals, style denominators, unique IDs and fragment size.')
