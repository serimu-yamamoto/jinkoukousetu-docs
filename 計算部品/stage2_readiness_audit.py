"""Deterministic audit of the 2026-10-23 readiness document.
All material densities and design scenarios are assumed inputs, not measurements.
Run with archived dependencies in the same folder. Physical experiments: zero.
"""
import math
from capillo_v22_protocol_audit import CORE, SHELL, mixture_volume
from capillo_v21_system_audit import drainage_height

def nozzle(core, shell, core_d=2.6, outer_d=3.0):
    vc, vs = mixture_volume(core), mixture_volume(shell)
    f = vs/(vc+vs)
    return {
        "core_volume_cm3":vc, "shell_volume_cm3":vs,
        "shell_volume_fraction":f,
        "shell_to_core_mean_speed":(vs/vc)*(core_d**2/(outer_d**2-core_d**2)),
        "equal_speed_wall_0_8mm_um":400*(1-math.sqrt(1-f)),
        "uniform_spherical_shell_0_8mm_um":400*(1-(1-f)**(1/3)),
    }

def audit():
    checks=[]
    def ck(name, actual, expected, tol=1e-8):
        assert abs(actual-expected)<=tol, (name, actual, expected)
        checks.append(name)
    initial=nozzle(CORE,SHELL)
    ck("full shell volume",initial["shell_volume_cm3"],12.780565499956032,1e-8)
    ck("old nozzle ratio rounded",round(initial["shell_to_core_mean_speed"],3),0.637)
    shell19=SHELL.copy()
    shell19[0]-=.8
    shell19[3]-=.2
    reduced=nozzle(CORE,shell19)
    ck("end powder total",sum(SHELL)-sum(shell19),1)
    ck("volumes close with end powder",mixture_volume(shell19)+.8/2.71+.2/1.5,mixture_volume(SHELL))
    fresh=[c+s for c,s in zip(CORE,SHELL)]
    recycled=[.8*x for x in fresh]
    core85=recycled.copy()
    core85[2]+=.9
    core85[6]+=4.1
    shell15=[6.,1.2,0.,.5,.7,.3,6.3]
    ck("85g core",sum(core85),85)
    ck("15g shell",sum(shell15),15)
    assert all(abs(a+b-c)<1e-9 for a,b,c in zip(core85,shell15,fresh))
    checks.append("bulk composition restored")
    wear=2191.5*.60
    recovered=wear*.80
    lost=wear-recovered
    case_a={"wear_t":wear,"recovered_core_t":recovered,"unrecovered_t":lost,
            "virgin_shell_t":recovered/.8*.2,"replacement_output_t":recovered/.8,
            "extra_purge_required_t":0.}
    ck("A replaces full wear",case_a["replacement_output_t"],wear)
    ck("A virgin equals unrecovered",case_a["virgin_shell_t"],lost)
    case_b={"wear_t":wear,"recovered_t":recovered,"core_used_t":recovered*.8,
            "virgin_shell_t":recovered*.2,"purge_t":recovered*.2,
            "replacement_output_t":recovered,"additional_complete_makeup_t":lost,
            "total_virgin_t":lost+recovered*.2}
    ck("B external balance",case_b["total_virgin_t"],lost+case_b["purge_t"])
    ck("B output plus additional makeup",case_b["replacement_output_t"]+case_b["additional_complete_makeup_t"],wear)
    drainage=[]
    for angle in [20.,30.]:
        for rain in [100.,150.]:
            h=drainage_height(rain,10.,.0025,angle)
            kreq=.0025*h/.225
            hp=drainage_height(rain,10.,.006,angle)
            drainage.append({"angle_deg":angle,"rain_mm_h_per_slope_area":rain,
                "water_height_old_k_m":h,"k_for_0_225m_m_s":kreq,
                "water_height_proposed_k_m":hp})
    ck("30deg old head",drainage[2]["water_height_old_k_m"],2/9)
    assert all(x["water_height_proposed_k_m"]<=.225 for x in drainage)
    checks.append("proposed k meets chosen hydraulic envelope")
    tests=2*2*5*2*3
    controls=2*2*3
    # 2 pieces * 20 mm *20 mm * thickness(mm) /1000 => cm3.
    sample_t_max=300/((tests+controls)*.8*(20/mixture_volume(SHELL)))
    ck("interface exposure assemblies",tests,120)
    ck("control assemblies",controls,12)
    return {"status":"conditional arithmetic; physical tests zero","checks":checks,
      "nozzle_full_shell":initial,"nozzle_after_1g_end_powder":reduced,
      "composition_corrected_85_15":nozzle(core85,shell15),
      "recycle_A":case_a,"recycle_B":case_b,"drainage":drainage,
      "paper_100cm2_at_1g_m2_mg":10.,
      "interface_test_assemblies":tests+controls,
      "max_equal_piece_thickness_mm_if_300g_no_air_no_losses":sample_t_max,
      "screening_thresholds_unvalidated":{
        "friction_upper":.10,"snow_response_ratio":[.8,1.2],
        "paper_transfer_g_m2":1.,"irreversibly_fused_mass_pct":1.,
        "strength_recovery_ratio":.8,"mold_strength_retention_ratio":.8,
        "freeze_thaw_fines_increase_pct_initial_dry_mass":1.,
        "fines_cutoff_um":75,"freeze_thaw_cycles":10}}
if __name__=="__main__":
    import json
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
