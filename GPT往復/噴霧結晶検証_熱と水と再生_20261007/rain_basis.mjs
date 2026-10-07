import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.dirname(fileURLToPath(import.meta.url));
const area_m2=2000, vertical_rain_mm=100, concentration_kg_m3=2.617;
const inventory_kg=[10.8,108,540];
export const result={
  scope:'Geometric projection only; no wind, upstream inflow, shielding, or kinetic model. Area is bed-surface area.',
  model_rain_mm_definition:'Equivalent supplied-water volume divided by bed area, expressed in mm; not necessarily meteorological vertical rainfall.',
  formula:'h_effective=h_vertical*cos(theta); V=A*h_effective/1000; capacity=C*V; h_vertical_equal_inventory=1000*M/(C*A*cos(theta)) for full effective contact.',
  area_m2,vertical_rain_mm,concentration_kg_m3,physical_tests:0,physical_success_probability:null,
  cases:[0,20,30,45].map(slope_degrees=>{
    const factor=Math.cos(slope_degrees*Math.PI/180);
    const water_m3=area_m2*vertical_rain_mm/1000*factor;
    return {slope_degrees,projection_factor:factor,equivalent_depth_mm:vertical_rain_mm*factor,water_m3,equilibrium_capacity_kg:concentration_kg_m3*water_m3,
      inventories:inventory_kg.map(m=>({inventory_kg:m,vertical_rain_equal_inventory_mm:1000*m/(concentration_kg_m3*area_m2*factor)}))};
  })
};
await fs.writeFile(path.join(root,'rain_basis.json'),JSON.stringify(result,null,2)+'\n');