from pathlib import Path
import json,sys
D=Path(__file__).resolve().parent
r=json.loads((D/'results.json').read_text())
rows=[x for x in r['rows'] if x['nx']==32]
retained=.75
section={'area_ratio':retained,'centered_solid_I_ratio':retained**3,
'outer_material_composite_I_ratio':1-(1-retained)**3,
'independent_equal_ribs_I_ratio':2*((retained/2)**3),
'assumptions':'same total outer width; parallel-axis term requires composite action; no drainage connectivity, buckling or strength proof',
'specific_volume_price_break_even':1/.7875,
'selective_modulus_ratio_lateral_over_normal_required':[x['normal_ratio']/x['lateral_ratio'] for x in rows]}
assert section['outer_material_composite_I_ratio']==.984375
assert section['independent_equal_ribs_I_ratio']==.10546875
# Direct integration: outer strips [−0.5,−0.125] and [0.125,0.5], I0=1/12.
assert abs(2*(.5**3-.125**3)/3/(1/12)-section['outer_material_composite_I_ratio'])<1e-12
p=D/'section_tradeoff.json'
if '--check' in sys.argv:assert section==json.loads(p.read_text())
else:p.write_text(json.dumps(section,indent=2)+'\n')
print('Section geometry and material-cost conditions checked; no physical trials')
