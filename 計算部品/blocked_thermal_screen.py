"""Blocked thermal observation allocation; no physical-performance prediction."""
from math import ceil
def allocate(histories, batches=3):
    if len(histories)!=3 or len(set(histories))!=3 or batches!=3:
        raise ValueError("This balanced screen uses three histories and three preparation batches.")
    out=[]
    for b in range(1,batches+1):
        for j,h in enumerate(histories):
            parent=f"B{b}-{h}"
            out.append(dict(parent_portion=parent, preparation_batch=f"B{b}",history=h,
                            joint_carrier_position=(j+b-1)%3+1,
                            baseline_dsc_aliquot=parent+"-D0",
                            hotstage_then_dsc_aliquot=parent+"-HD1",
                            observed_timepoints=["30C_before","50C_arrival","50C_0.5h","50C_1h","50C_5h","50C_8h","30C_after"],
                            status="not_prepared",measurements=None))
    return out
def schedule(histories=3,batches=3,capacity=1,hold_h=8):
    if not all(type(x) is int and x>0 for x in (histories,batches,capacity)) or hold_h<=0:
        raise ValueError("positive allocation parameters required")
    # Do not pack leftovers across independent preparation blocks.
    cycles=batches*ceil(histories/capacity)
    return dict(simultaneous_history_capacity=capacity,cycles=cycles,
                hold_hours_only=cycles*hold_h,
                confirmed_capacity=False,overhead_hours=None,total_quote_yen=None)
