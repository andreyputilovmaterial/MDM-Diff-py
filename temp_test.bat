@ECHO OFF


SET "MDD_A=examples/path/p221366_wave19.mdd"
SET "MDD_B=examples\different_path_here/2\p221366_v77.mdd"

SET "MDD_A_TEMP=%MDD_A:/=\%"
SET "MDD_B_TEMP=%MDD_B:/=\%"
SET SET "DUMMY_A=%MDD_A_TEMP:\=" & SET "MDD_A_FNAME=%"
SET SET "DUMMY_B=%MDD_B_TEMP:\=" & SET "MDD_B_FNAME=%"

SET "PATH_A=%MDD_A%\..\"

ECHO "%MDD_A_FNAME%"
ECHO "%MDD_B_FNAME%"
ECHO %PATH_A%"
