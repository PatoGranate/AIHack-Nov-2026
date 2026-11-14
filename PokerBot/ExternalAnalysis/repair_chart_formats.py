from pathlib import Path
import json,re
base=Path('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c')
for path in (base/'poker-comparison.html',base/'poker-v7-validation.html'):
    def fix(match):
        config=json.loads(match[2]);fmt=config['spec'].get('valueFormat')
        if fmt and 'style' not in fmt:fmt['style']='decimal'
        uncertainty=config['spec'].get('uncertainty')
        if uncertainty and 'style' not in uncertainty:uncertainty['style']='bars'
        return match[1]+json.dumps(config).replace('<','\\u003c')+match[3]
    text=re.sub(r'(<script[^>]*data-viz-chart[^>]*>)(.*?)(</script>)',fix,path.read_text(encoding='utf-8'),flags=re.S)
    path.write_text(text,encoding='utf-8')
    print('Updated decimal formats:',path.name)
