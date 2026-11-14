from pathlib import Path
root=Path(__file__).resolve().parent
paths=list(root.glob('*.txt'))+list((root/'IndependentChecks').glob('*.txt'))
paths.append(Path('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c/poker-comparison.html'))
for p in paths:
    data=p.read_bytes()
    try:data.decode('utf-8',errors='strict')
    except UnicodeDecodeError:
        text=data.decode('cp1252',errors='strict')
        p.write_text(text,encoding='utf-8')
        print('REPAIRED',p.name)
    p.read_bytes().decode('utf-8',errors='strict')
print('All',len(paths),'checked report/visual files pass strict UTF-8 decoding.')
