"""Only the user-authorized final armament obscurer families, static conversion."""
from pathlib import Path
import import_v3_armament_ui as base
base.OUT=base.ROOT/'ui/v3_authorized/armament_final'
base.CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_armament_final_20261107')
base.SELECT={
 'partition_data_win.cpk':[f'flash/trial/t_riron_kakusi{i}.spc' for i in range(1,7)],
 'partition_data_win_us.cpk':[f'flash/trial/t_riron_kakusi_s{i}_US.spc' for i in range(1,7)],
}
if __name__=='__main__':base.main(include_supplied=False)
