"""Engine-neutral, stdlib-only joint roster identification.

No game actions or hidden cards enter this module. Unknown identities may repeat;
named teams cannot occupy two seats. Posterior confidence is model-dependent,
not a statistical guarantee. Tempering defaults must be calibrated temporally.
"""
import math


def logsum(values):
    values=list(values)
    if not values:return float('-inf')
    top=max(values)
    if top == float('-inf'):return top
    return top+math.log(sum(math.exp(v-top) for v in values))


class JointIdentity:
    def __init__(self, roster, profiles, temperature=.25, unknown_prior=.2, decay=.997):
        self.names=tuple(dict.fromkeys(roster))
        if len(self.names)>8:raise ValueError('joint model supports at most eight named opponents')
        self.profiles=profiles
        self.temperature=temperature
        self.unknown_prior=unknown_prior
        self.decay=decay
        self.scores={}
        self.pending={}
        self.observations={}

    def observe(self,seat,kind,key):
        probs=[self.profiles.get(n,{}).get(kind,{}).get(key,0.) for n in self.names]
        population=sum(probs)/max(1,len(probs))
        # Unknown has a larger unseen-event floor, allowing a new version to win.
        unknown=.8*population+.2*.02
        evidence=[self.temperature*math.log((.95*p+.05*.02)/unknown) for p in probs]+[0.]
        row=self.pending.setdefault(seat,[0.]*(len(self.names)+1))
        for i,v in enumerate(evidence):row[i]+=v
        self.observations[seat]=self.observations.get(seat,0)+1

    def finish_hand(self):
        for row in self.scores.values():
            for i in range(len(row)):row[i]*=self.decay
        for seat,obs in self.pending.items():
            row=self.scores.setdefault(seat,[0.]*len(obs))
            # Bound a hand's correlated evidence without changing its direction.
            scale=min(1.,2./max(1e-9,max(abs(v) for v in obs)))
            for i,v in enumerate(obs):row[i]+=v*scale
        self.pending.clear()

    def posterior(self,seats):
        seats=tuple(seats);k=len(self.names)
        if not k:return {s:{'_unknown':1.} for s in seats}
        named_prior=math.log((1-self.unknown_prior)/k)
        unknown_prior=math.log(self.unknown_prior)
        rows=[]
        for seat in seats:
            score=self.scores.get(seat,[0.]*(k+1))
            rows.append([v+named_prior for v in score[:k]]+[unknown_prior])
        # Forward/backward subset DP computes exact assignment marginals.
        forward=[{0:0.}]
        for row in rows:
            nxt={}
            for mask,value in forward[-1].items():
                for i in range(k+1):
                    if i<k and mask>>i&1:continue
                    target=mask if i==k else mask|1<<i
                    nxt[target]=logsum((nxt.get(target,float('-inf')),value+row[i]))
            forward.append(nxt)
        back=[{} for _ in range(len(seats)+1)]
        back[-1]={m:0. for m in forward[-1]}
        for t in range(len(seats)-1,-1,-1):
            for mask in forward[t]:
                terms=[]
                for i in range(k+1):
                    if i<k and mask>>i&1:continue
                    target=mask if i==k else mask|1<<i
                    terms.append(rows[t][i]+back[t+1][target])
                back[t][mask]=logsum(terms)
        z=back[0][0];out={}
        for t,seat in enumerate(seats):
            probs={}
            for i,name in enumerate(self.names+('_unknown',)):
                terms=[]
                for mask,value in forward[t].items():
                    if i<k and mask>>i&1:continue
                    target=mask if i==k else mask|1<<i
                    terms.append(value+rows[t][i]+back[t+1][target])
                probs[name]=math.exp(logsum(terms)-z) if terms else 0.
            out[seat]=probs
        return out
