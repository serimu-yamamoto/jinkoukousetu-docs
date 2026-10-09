"""Kinematic similarity and machine dwell only; not entanglement dynamics."""
import math
def vibration(diameter_m,amplitude_m,frequency_hz,g=9.8):
    if not all(math.isfinite(x) and x>0 for x in [diameter_m,amplitude_m,frequency_hz,g]):
        raise ValueError("Positive finite inputs required")
    return dict(diameter_m=diameter_m,amplitude_m=amplitude_m,frequency_hz=frequency_hz,
        amplitude_over_diameter=amplitude_m/diameter_m,
        peak_acceleration_over_g=amplitude_m*(2*math.pi*frequency_hz)**2/g,
        peak_velocity_m_s=amplitude_m*2*math.pi*frequency_hz)
def scaled_kinematics(reference,target_diameter_m,reference_time_s):
    if not math.isfinite(reference_time_s) or reference_time_s<=0:raise ValueError("Invalid time")
    s=target_diameter_m/reference['diameter_m']
    if not math.isfinite(s) or s<=0:raise ValueError("Invalid scale")
    v=vibration(target_diameter_m,reference['amplitude_m']*s,reference['frequency_hz']/math.sqrt(s))
    v.update(length_scale=s,reference_event_time_s=reference_time_s,
       matched_cycle_duration_s=reference_time_s*math.sqrt(s),
       reference_cycles=reference['frequency_hz']*reference_time_s)
    return v
def moving_dwell(footprint_m,speed_m_s,frequency_hz,course_m,operating_fraction,overhead_min):
    if not all(math.isfinite(x) and x>0 for x in [footprint_m,speed_m_s,frequency_hz,course_m,operating_fraction]) or operating_fraction>1 or not math.isfinite(overhead_min) or overhead_min<0:
        raise ValueError("Invalid machine assumptions")
    return dict(footprint_m_assumed=footprint_m,speed_m_s_assumed=speed_m_s,
       local_dwell_s=footprint_m/speed_m_s,local_cycles=frequency_hz*footprint_m/speed_m_s,
       course_closure_min=course_m/(speed_m_s*operating_fraction)/60+overhead_min)
def dwell_budget(course_m,closure_min,overhead_min,operating_fraction,event_duration_s,footprint_m):
    if not all(math.isfinite(x) and x>0 for x in [course_m,closure_min,operating_fraction,event_duration_s,footprint_m]) or operating_fraction>1 or not math.isfinite(overhead_min) or not 0<=overhead_min<closure_min:
        raise ValueError("Invalid closure budget")
    vmin=course_m/(60*(closure_min-overhead_min)*operating_fraction)
    return dict(minimum_travel_speed_m_s=vmin,
       footprint_for_comparison_event_m=vmin*event_duration_s,
       speed_for_comparison_event_m_s=footprint_m/event_duration_s,
       caveat="Event is a literature observation time, not a required or sufficient grooming duration.")
