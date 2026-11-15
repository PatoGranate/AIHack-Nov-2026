"""Append to an existing single-file engine after JointIdentity is defined.

Reuses existing MODEL priors and fingerprint extraction; not a new betting policy.
GBot needs an equivalent explicit adapter only after independent engine selection.
"""
BaseAgent = Agent


class Agent(BaseAgent):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.identity=JointIdentity(SUNDAY_ROSTER,MODEL.get('bots',{}))
        self.identity_posteriors={}
        self.identity_ms=0.
        self.context_model=ContextModel(CONTEXT_PROFILES,CONTEXT_POPULATION)
        self.context_failures=0
        self._decision_hand=None
        self._learned_hand=None
        self.behavior_profiles={}
        # Historical identity is opt-in. Default: every seat starts unseen.
        self.use_historical_identity=self.P.get('use_historical_identity',False)
        self._read_cache={}   # (method, seat) -> value; cleared in _learn. Reads run inside act()'s time budget.

    def pri(self,seat,key,default,k):
        if not self.use_historical_identity:return default,k
        return super().pri(seat,key,default,k)

    def act(self,state):
        self._decision_hand=state['hand_number']
        self._decision_button=state['button']
        return super().act(state)

    def _learn(self,summary):
        self._read_cache.clear()
        hand=summary.get('hand_number')
        if hand is not None and hand==self._learned_hand:return
        super()._learn(summary)
        if hand is not None:self._learned_hand=hand
        if self._decision_hand is None or self._decision_hand != summary.get('hand_number'):return
        try:
            events=[];street='preflop';board=summary.get('board',[])
            for h in summary.get('history',[]):
                if h['street']!=street:
                    street=h['street'];events.append(['board',street,board[:{'flop':3,'turn':4,'river':5}[street]]])
                if h['action'] in ('small_blind','big_blind'):events.append(['post',h['seat'],h['amount']])
                else:events.append(['act',h['seat'],h['action'],h['amount']])
            labels=['WBot' if s==self.seat else 'seat:'+str(s) for s in range(self.n)]
            counts=hand_counts({'button':self._decision_button,'events':events},labels)
            for s in range(self.n):
                if s!=self.seat:
                    self.context_model.update(s,counts[labels[s]])
                    profile=self.behavior_profiles.setdefault(s,BehaviorProfile())
                    profile.update(counts[labels[s]])
                    # Subsequent action predictions use the same active window
                    # as tags; a detected policy change does not leave stale
                    # all-round evidence silently dominating the next decision.
                    active=profile.recent if profile.changed else profile.recent+profile.previous
                    self.context_model.live[s]=dict(active)
        except (KeyError,ValueError,TypeError):
            self.context_failures+=1

    def opponent_prediction(self,seat,context,actions=('fold','call','raise')):
        ids=self.identity_posteriors.get(seat,{'_unknown':1.}) if self.use_historical_identity else {'_unknown':1.}
        model=self.context_model
        if not self.use_historical_identity:
            model=ContextModel({});model.live=self.context_model.live
        return model.predict(seat,context,actions,ids)

    def opponent_tags(self,seat):
        return self.behavior_profiles.get(seat,BehaviorProfile()).summary()

    def _behavior_rate(self,seat,success,total,key,default,k):
        counts=self.context_model.live.get(seat)
        if not counts:return None
        pv,mass=self.pri(seat,key,default,k)
        return (counts.get(success,0)+pv*mass)/(counts.get(total,0)+mass)

    def vpip(self,seat):
        key=('vpip',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._vpip_uncached(seat)
        self._read_cache[key]=value
        return value

    def _vpip_uncached(self,seat):
        value=self._behavior_rate(seat,'vpip','hands','vpip',self.P['pri_vpip'],12)
        return super().vpip(seat) if value is None else value

    def pfr(self,seat):
        key=('pfr',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._pfr_uncached(seat)
        self._read_cache[key]=value
        return value

    def _pfr_uncached(self,seat):
        value=self._behavior_rate(seat,'pfr','hands','pfr',self.P['pri_pfr'],12)
        return super().pfr(seat) if value is None else value

    def bigrate(self,seat):
        key=('bigrate',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._bigrate_uncached(seat)
        self._read_cache[key]=value
        return value

    def _bigrate_uncached(self,seat):
        value=self._behavior_rate(seat,'big','hands','big',.05,10)
        return super().bigrate(seat) if value is None else value

    def fold3(self,seat):
        key=('fold3',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._fold3_uncached(seat)
        self._read_cache[key]=value
        return value

    def _fold3_uncached(self,seat):
        counts=self.context_model.live.get(seat)
        if not counts:return super().fold3(seat)
        n=counts.get('vs_3bet/opportunities',0)
        pv,mass=self.pri(seat,'f3',.5,4)
        return (counts.get('vs_3bet/fold',0)+pv*mass)/(n+mass),n

    def ftb(self,seat):
        key=('ftb',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._ftb_uncached(seat)
        self._read_cache[key]=value
        return value

    def _ftb_uncached(self,seat):
        counts=self.context_model.live.get(seat)
        if not counts:return super().ftb(seat)
        keys=[k for k in counts if k.startswith(('flop/','turn/','river/')) and k.endswith('/opportunities') and '/vs_' in k]
        n=sum(counts[k] for k in keys)
        folds=sum(counts.get(k.rsplit('/',1)[0]+'/fold',0) for k in keys)
        pv,mass=self.pri(seat,'ftb',self.P['pri_ftb'],8)
        return (folds+pv*mass)/(n+mass)

    def af(self,seat):
        key=('af',seat)
        if key in self._read_cache:return self._read_cache[key]
        value=self._af_uncached(seat)
        self._read_cache[key]=value
        return value

    def _af_uncached(self,seat):
        counts=self.context_model.live.get(seat)
        if not counts:return super().af(seat)
        prefix=lambda key:key.startswith(('flop/','turn/','river/'))
        raises=sum(v for k,v in counts.items() if prefix(k) and k.endswith('/raise'))
        actions=sum(v for k,v in counts.items() if prefix(k) and k.endswith(('/raise','/call','/check')))
        pv,mass=self.pri(seat,'af',.3,10)
        return (raises+pv*mass)/(actions+mass)

    def _id_obs(self,seat,kind,key):
        if seat != self.seat:self.identity.observe(seat,kind,key)

    def _id_post(self,seat):
        # Base extraction invokes this for each touched seat. Update jointly once
        # at the end of _id_learn, after all observations have been collected.
        pass

    def _id_learn(self,hist,bb):
        if not self.use_historical_identity:return
        t0=time.perf_counter()
        super()._id_learn(hist,bb)
        self.identity.finish_hand()
        # Deliberately bound callback cost: exact matching every 25 hands,
        # and at the first hand. Cached predictions are used inside act().
        if self.hands_seen != 1 and self.hands_seen % 25:return
        seats=[s for s in range(self.n) if s != self.seat]
        posterior=self.identity.posterior(seats)
        self.identity_posteriors=posterior
        keys=('vpip','pfr','big','f3','ftr','ftb','af','bluff')
        fallback=MODEL['popstats']
        for seat,probs in posterior.items():
            q={key:sum(p*(fallback[key] if name=='_unknown' else
                         MODEL['bots'].get(name,fallback).get(key,fallback[key]))
                       for name,p in probs.items()) for key in keys}
            q['_conf']=max((p for name,p in probs.items() if name!='_unknown'),default=0.)
            self.post[seat]=q
        self.identity_ms=max(self.identity_ms,(time.perf_counter()-t0)*1000)
