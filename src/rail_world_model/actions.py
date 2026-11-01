"""Explanatory straight camera plans; not acquired or reconstructed pose GT."""
from .contracts import validate_action

PROFILES=('stop','const5','const10','accel','decel')


def straight_action(profile,transitions=188,fps=24):
    if profile not in PROFILES:
        raise ValueError('Unknown motion profile')
    if isinstance(transitions,bool) or not isinstance(transitions,int) or transitions<1:
        raise ValueError('transitions must be a positive integer')
    if isinstance(fps,bool) or not isinstance(fps,(int,float)) or not 0<fps<1000:
        raise ValueError('fps must be finite and positive')
    result=[]
    for i in range(transitions):
        midpoint=(i+0.5)/transitions
        kmh={'stop':0,'const5':5,'const10':10,'accel':10*midpoint,'decel':10*(1-midpoint)}[profile]
        result.append([0.0,0.0,kmh/3.6/fps,1.0,0.0,0.0,0.0,1.0,0.0])
    validate_action(result,transitions)
    return result
