import json,glob,sys,collections
D=sys.argv[1]
def pos_name(seat,button,n):
    # distance after button: 1=SB,2=BB,... last=BTN
    k=(seat-button)%n
    if k==0: return 'BTN'
    if k==1: return 'SB'
    if k==2: return 'BB'
    rem=n-k  # seats until button: 1=CO,2=HJ
    return {1:'CO',2:'HJ'}.get(rem,'EP')
agg=collections.defaultdict(lambda: collections.Counter())
sizes=collections.defaultdict(list)
for f in sorted(glob.glob(D+'/saturday_r*.json')):
    d=json.load(open(f)); v=d['round']['version']; me=d['seat']
    r=int(f[-8:-5]); grp='v%d'%v
    for h in d['hands']:
        n=len(h['start_stacks']); p=pos_name(me,h['button'],n)
        raised=False; c=agg[(grp,p)]
        for e in h['events']:
            if e[0]=='board': break
            if e[0]!='act': continue
            _,s,a,amt=e
            if s==me:
                if not raised:
                    c['fi']+=1
                    if a=='raise': c['open']+=1; sizes[(grp,'all')].append(amt/20)
                    elif a=='call': c['limp']+=1
                break
            if a=='raise': raised=True
            if a=='call' and not raised: pass
for v in sorted({g for g,_ in agg}):
    row=[]
    for p in ['EP','HJ','CO','BTN','SB']:
        c=agg[(v,p)]; row.append('%s %.3f(%d)'%(p,c['open']/max(1,c['fi']),c['fi']))
    sz=sizes[(v,'all')]; cs=collections.Counter(round(x,2) for x in sz).most_common(4)
    print(v,' '.join(row),' sizes',cs)
