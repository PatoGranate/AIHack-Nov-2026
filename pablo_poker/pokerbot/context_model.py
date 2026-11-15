"""Engine-neutral contextual response posteriors with explicit evidence mass.

Predictions only: adapters decide how to use them in an independently tested EV
engine. Unknown versions are not treated as verified current-version evidence.
"""
class ContextModel:
    def __init__(self,profiles,population=None,prior_mass=20):
        self.profiles=profiles
        self.population=population or {}
        self.prior_mass=prior_mass
        self.live={}

    def update(self,seat,counts):
        row=self.live.setdefault(seat,{})
        for key,n in counts.items():row[key]=row.get(key,0)+n

    def predict(self,seat,context,actions,identities):
        base=[self.population.get(context+'/'+a,0) for a in actions]
        den=sum(base)+len(actions)
        prior=[(n+1)/den for n in base]
        identity_total=sum(identities.values())
        mix=[0.]*len(actions)
        for name,p in identities.items():
            row=self.profiles.get(name,{})
            observed=[row.get(context+'/'+a,0) for a in actions];total=sum(observed)
            local=[(n+12*b)/(total+12) for n,b in zip(observed,prior)]
            for i,value in enumerate(local):mix[i]+=p*value
        if identity_total<=0:mix=prior
        else:mix=[v/identity_total for v in mix]
        row=self.live.get(seat,{})
        observed=[row.get(context+'/'+a,0) for a in actions];n=sum(observed)
        alpha=[v+self.prior_mass*p for v,p in zip(observed,mix)]
        total=sum(alpha)
        return dict(probabilities=dict(zip(actions,[v/total for v in alpha])),
                    alpha=dict(zip(actions,alpha)),observed_n=n,prior_mass=self.prior_mass,
                    status='uncalibrated_prediction_not_action_authorization')
