"""Reusable public-history observer for any engine, including a future GBot adapter.

Does not choose actions or assume team identities. Import dependencies normally
offline, or concatenate these stdlib-only modules into a standalone upload.
"""
from pokerbot.opponent_evidence import hand_counts
from pokerbot.behavior_profile import BehaviorProfile
from pokerbot.context_model import ContextModel


class ColdObserver:
    def __init__(self):
        self.profiles={};self.context=ContextModel({});self.last_hand=None
        self.processed_hand=None;self.failures=0

    def observe_state(self,state):
        self.last_hand=state['hand_number'];self.button=state['button']
        self.seat=state['seat'];self.n=len(state['stacks'])

    def observe_summary(self,summary):
        hand=summary.get('hand_number')
        if self.last_hand is None or hand!=self.last_hand or hand==self.processed_hand:return
        events=[];street='preflop';board=summary.get('board',[])
        for h in summary.get('history',[]):
            if h['street']!=street:
                street=h['street'];events.append(['board',street,board[:{'flop':3,'turn':4,'river':5}[street]]])
            if h['action'] in ('small_blind','big_blind'):events.append(['post',h['seat'],h['amount']])
            else:events.append(['act',h['seat'],h['action'],h['amount']])
        labels=['WBot' if s==self.seat else 'seat:'+str(s) for s in range(self.n)]
        counts=hand_counts({'button':self.button,'events':events},labels)
        for seat in range(self.n):
            if seat==self.seat:continue
            profile=self.profiles.setdefault(seat,BehaviorProfile());profile.update(counts[labels[seat]])
            active=profile.recent if profile.changed else profile.recent+profile.previous
            self.context.live[seat]=dict(active)
        self.processed_hand=hand

    def tags(self,seat):return self.profiles.get(seat,BehaviorProfile()).summary()

    def prediction(self,seat,context,actions=('fold','call','raise')):
        return self.context.predict(seat,context,actions,{'_unknown':1.})


def wrap_engine(engine_class):
    """Standard Agent callbacks only. Engine opts in to consuming predictions."""
    class ObservedAgent(engine_class):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.opponent_observer=ColdObserver()
        def act(self,state):
            self.opponent_observer.observe_state(state)
            return super().act(state)
        def on_hand_end(self,summary):
            callback=getattr(super(),'on_hand_end',None)
            if callback:callback(summary)
            self.opponent_observer.observe_summary(summary)
    return ObservedAgent
