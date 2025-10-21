\ Model mp
\ LP format - for model browsing. Use MPS format to capture full model detail.
Maximize
  - 20 traversed[1,2] - 20 traversed[1,6] - 20 traversed[1,7]
   - 20 traversed[2,3] - 20 traversed[2,7] - 20 traversed[2,8]
   - 20 traversed[2,1] - 20 traversed[3,4] - 20 traversed[3,8]
   - 20 traversed[3,2] - 20 traversed[4,5] - 20 traversed[4,8]
   - 20 traversed[4,3] - 20 traversed[5,6] - 20 traversed[5,9]
   - 20 traversed[5,4] - 20 traversed[6,7] - 20 traversed[6,1]
   - 20 traversed[6,5] - 20 traversed[7,8] - 20 traversed[7,9]
   - 20 traversed[7,1] - 20 traversed[7,2] - 20 traversed[7,6]
   - 20 traversed[8,9] - 20 traversed[8,2] - 20 traversed[8,3]
   - 20 traversed[8,4] - 20 traversed[8,7] - 20 traversed[9,5]
   - 20 traversed[9,7] - 20 traversed[9,8] + 50 profitable_route[3,4]
   + 0 profitable_route[4,9] + 0 profitable_route[3,7]
   + 0 profitable_route[4,6] + 0 profitable_route[5,7]
   + 50 profitable_route[8,9] + 50 profitable_route[1,6]
   + 0 profitable_route[2,5] + 0 profitable_route[1,3]
   + 0 profitable_route[1,9] + 0 profitable_route[6,8]
   + 50 profitable_route[4,5] + 0 profitable_route[3,9]
   + 50 profitable_route[5,6] + 0 profitable_route[3,6]
   + 0 profitable_route[2,4] + 50 profitable_route[1,2]
   + 0 profitable_route[1,5] + 0 profitable_route[1,8]
   + 50 profitable_route[7,9] + 0 profitable_route[4,7]
   + 0 profitable_route[3,5] + 0 profitable_route[5,8]
   + 0 profitable_route[1,4] + 50 profitable_route[2,3]
   + 0 profitable_route[2,9] + 0 profitable_route[2,6]
   + 0 profitable_route[6,9] + 50 profitable_route[7,8]
Subject To
 symmetry[1]: traversed[1,2] + traversed[1,6] + traversed[1,7]
   - traversed[2,1] - traversed[6,1] - traversed[7,1] = 0
 symmetry[2]: - traversed[1,2] + traversed[2,3] + traversed[2,7]
   + traversed[2,8] + traversed[2,1] - traversed[3,2] - traversed[7,2]
   - traversed[8,2] = 0
 symmetry[3]: - traversed[2,3] + traversed[3,4] + traversed[3,8]
   + traversed[3,2] - traversed[4,3] - traversed[8,3] = 0
 symmetry[4]: - traversed[3,4] + traversed[4,5] + traversed[4,8]
   + traversed[4,3] - traversed[5,4] - traversed[8,4] = 0
 symmetry[5]: - traversed[4,5] + traversed[5,6] + traversed[5,9]
   + traversed[5,4] - traversed[6,5] - traversed[9,5] = 0
 symmetry[6]: - traversed[1,6] - traversed[5,6] + traversed[6,7]
   + traversed[6,1] + traversed[6,5] - traversed[7,6] = 0
 symmetry[7]: - traversed[1,7] - traversed[2,7] - traversed[6,7]
   + traversed[7,8] + traversed[7,9] + traversed[7,1] + traversed[7,2]
   + traversed[7,6] - traversed[8,7] - traversed[9,7] = 0
 symmetry[8]: - traversed[2,8] - traversed[3,8] - traversed[4,8]
   - traversed[7,8] + traversed[8,9] + traversed[8,2] + traversed[8,3]
   + traversed[8,4] + traversed[8,7] - traversed[9,8] = 0
 symmetry[9]: - traversed[5,9] - traversed[7,9] - traversed[8,9]
   + traversed[9,5] + traversed[9,7] + traversed[9,8] = 0
 R9: traversed[1,2] - run[1,2] >= 0
 R10: traversed[1,6] - run[1,6] >= 0
 R11: traversed[1,7] - run[1,7] >= 0
 R12: traversed[2,1] - run[2,1] >= 0
 R13: traversed[2,3] - run[2,3] >= 0
 R14: traversed[2,7] - run[2,7] >= 0
 R15: traversed[2,8] - run[2,8] >= 0
 R16: traversed[3,2] - run[3,2] >= 0
 R17: traversed[3,4] - run[3,4] >= 0
 R18: traversed[3,8] - run[3,8] >= 0
 R19: traversed[4,3] - run[4,3] >= 0
 R20: traversed[4,5] - run[4,5] >= 0
 R21: traversed[4,8] - run[4,8] >= 0
 R22: traversed[5,4] - run[5,4] >= 0
 R23: traversed[5,6] - run[5,6] >= 0
 R24: traversed[5,9] - run[5,9] >= 0
 R25: traversed[6,1] - run[6,1] >= 0
 R26: traversed[6,5] - run[6,5] >= 0
 R27: traversed[6,7] - run[6,7] >= 0
 R28: traversed[7,1] - run[7,1] >= 0
 R29: traversed[7,2] - run[7,2] >= 0
 R30: traversed[7,6] - run[7,6] >= 0
 R31: traversed[7,8] - run[7,8] >= 0
 R32: traversed[7,9] - run[7,9] >= 0
 R33: traversed[8,2] - run[8,2] >= 0
 R34: traversed[8,3] - run[8,3] >= 0
 R35: traversed[8,4] - run[8,4] >= 0
 R36: traversed[8,7] - run[8,7] >= 0
 R37: traversed[8,9] - run[8,9] >= 0
 R38: traversed[9,5] - run[9,5] >= 0
 R39: traversed[9,7] - run[9,7] >= 0
 R40: traversed[9,8] - run[9,8] >= 0
 R41: - traversed[1,2] + 10 run[1,2] >= 0
 R42: - traversed[1,6] + 10 run[1,6] >= 0
 R43: - traversed[1,7] + 10 run[1,7] >= 0
 R44: - traversed[2,1] + 10 run[2,1] >= 0
 R45: - traversed[2,3] + 10 run[2,3] >= 0
 R46: - traversed[2,7] + 10 run[2,7] >= 0
 R47: - traversed[2,8] + 10 run[2,8] >= 0
 R48: - traversed[3,2] + 10 run[3,2] >= 0
 R49: - traversed[3,4] + 10 run[3,4] >= 0
 R50: - traversed[3,8] + 10 run[3,8] >= 0
 R51: - traversed[4,3] + 10 run[4,3] >= 0
 R52: - traversed[4,5] + 10 run[4,5] >= 0
 R53: - traversed[4,8] + 10 run[4,8] >= 0
 R54: - traversed[5,4] + 10 run[5,4] >= 0
 R55: - traversed[5,6] + 10 run[5,6] >= 0
 R56: - traversed[5,9] + 10 run[5,9] >= 0
 R57: - traversed[6,1] + 10 run[6,1] >= 0
 R58: - traversed[6,5] + 10 run[6,5] >= 0
 R59: - traversed[6,7] + 10 run[6,7] >= 0
 R60: - traversed[7,1] + 10 run[7,1] >= 0
 R61: - traversed[7,2] + 10 run[7,2] >= 0
 R62: - traversed[7,6] + 10 run[7,6] >= 0
 R63: - traversed[7,8] + 10 run[7,8] >= 0
 R64: - traversed[7,9] + 10 run[7,9] >= 0
 R65: - traversed[8,2] + 10 run[8,2] >= 0
 R66: - traversed[8,3] + 10 run[8,3] >= 0
 R67: - traversed[8,4] + 10 run[8,4] >= 0
 R68: - traversed[8,7] + 10 run[8,7] >= 0
 R69: - traversed[8,9] + 10 run[8,9] >= 0
 R70: - traversed[9,5] + 10 run[9,5] >= 0
 R71: - traversed[9,7] + 10 run[9,7] >= 0
 R72: - traversed[9,8] + 10 run[9,8] >= 0
 total_length: 5 traversed[1,2] + 5 traversed[1,6] + 5 traversed[1,7]
   + 5 traversed[2,3] + 5 traversed[2,7] + 5 traversed[2,8]
   + 5 traversed[2,1] + 5 traversed[3,4] + 5 traversed[3,8]
   + 5 traversed[3,2] + 5 traversed[4,5] + 5 traversed[4,8]
   + 5 traversed[4,3] + 5 traversed[5,6] + 5 traversed[5,9]
   + 5 traversed[5,4] + 5 traversed[6,7] + 5 traversed[6,1]
   + 5 traversed[6,5] + 5 traversed[7,8] + 5 traversed[7,9]
   + 5 traversed[7,1] + 5 traversed[7,2] + 5 traversed[7,6]
   + 5 traversed[8,9] + 5 traversed[8,2] + 5 traversed[8,3]
   + 5 traversed[8,4] + 5 traversed[8,7] + 5 traversed[9,5]
   + 5 traversed[9,7] + 5 traversed[9,8] <= 75
 start_node[2]: run[1,2] >= 1
 start_node[6]: run[1,6] >= 1
 start_node[7]: run[1,7] >= 1
 R77: - run[1,2] + profitable_route[1,2] >= 0
 R78: - run[1,6] + profitable_route[1,6] >= 0
 R79: - run[1,7] + profitable_route[1,7] >= 0
 R80: - run[2,3] + profitable_route[2,3] >= 0
 R81: - run[2,7] + profitable_route[2,7] >= 0
 R82: - run[2,8] + profitable_route[2,8] >= 0
 R83: - run[3,4] + profitable_route[3,4] >= 0
 R84: - run[3,8] + profitable_route[3,8] >= 0
 R85: - run[4,5] + profitable_route[4,5] >= 0
 R86: - run[4,8] + profitable_route[4,8] >= 0
 R87: - run[5,6] + profitable_route[5,6] >= 0
 R88: - run[5,9] + profitable_route[5,9] >= 0
 R89: - run[6,7] + profitable_route[6,7] >= 0
 R90: - run[7,8] + profitable_route[7,8] >= 0
 R91: - run[7,9] + profitable_route[7,9] >= 0
 R92: - run[8,9] + profitable_route[8,9] >= 0
 R93: - run[2,1] + profitable_route[1,2] >= 0
 R94: - run[6,1] + profitable_route[1,6] >= 0
 R95: - run[7,1] + profitable_route[1,7] >= 0
 R96: - run[3,2] + profitable_route[2,3] >= 0
 R97: - run[7,2] + profitable_route[2,7] >= 0
 R98: - run[8,2] + profitable_route[2,8] >= 0
 R99: - run[4,3] + profitable_route[3,4] >= 0
 R100: - run[8,3] + profitable_route[3,8] >= 0
 R101: - run[5,4] + profitable_route[4,5] >= 0
 R102: - run[8,4] + profitable_route[4,8] >= 0
 R103: - run[6,5] + profitable_route[5,6] >= 0
 R104: - run[9,5] + profitable_route[5,9] >= 0
 R105: - run[7,6] + profitable_route[6,7] >= 0
 R106: - run[8,7] + profitable_route[7,8] >= 0
 R107: - run[9,7] + profitable_route[7,9] >= 0
 R108: - run[9,8] + profitable_route[8,9] >= 0
 R109: run[1,2] + run[2,1] - profitable_route[1,2] >= 0
 R110: run[1,6] + run[6,1] - profitable_route[1,6] >= 0
 R111: run[1,7] + run[7,1] - profitable_route[1,7] >= 0
 R112: run[2,3] + run[3,2] - profitable_route[2,3] >= 0
 R113: run[2,7] + run[7,2] - profitable_route[2,7] >= 0
 R114: run[2,8] + run[8,2] - profitable_route[2,8] >= 0
 R115: run[3,4] + run[4,3] - profitable_route[3,4] >= 0
 R116: run[3,8] + run[8,3] - profitable_route[3,8] >= 0
 R117: run[4,5] + run[5,4] - profitable_route[4,5] >= 0
 R118: run[4,8] + run[8,4] - profitable_route[4,8] >= 0
 R119: run[5,6] + run[6,5] - profitable_route[5,6] >= 0
 R120: run[5,9] + run[9,5] - profitable_route[5,9] >= 0
 R121: run[6,7] + run[7,6] - profitable_route[6,7] >= 0
 R122: run[7,8] + run[8,7] - profitable_route[7,8] >= 0
 R123: run[7,9] + run[9,7] - profitable_route[7,9] >= 0
 R124: run[8,9] + run[9,8] - profitable_route[8,9] >= 0
Bounds
Binaries
 run[1,2] run[1,6] run[1,7] run[2,3] run[2,7] run[2,8] run[2,1] run[3,4]
 run[3,8] run[3,2] run[4,5] run[4,8] run[4,3] run[5,6] run[5,9] run[5,4]
 run[6,7] run[6,1] run[6,5] run[7,8] run[7,9] run[7,1] run[7,2] run[7,6]
 run[8,9] run[8,2] run[8,3] run[8,4] run[8,7] run[9,5] run[9,7] run[9,8]
 profitable_route[3,4] profitable_route[4,9] profitable_route[3,7]
 profitable_route[4,6] profitable_route[5,7] profitable_route[8,9]
 profitable_route[1,6] profitable_route[2,5] profitable_route[1,3]
 profitable_route[1,9] profitable_route[2,8] profitable_route[6,8]
 profitable_route[4,5] profitable_route[3,9] profitable_route[5,6]
 profitable_route[4,8] profitable_route[3,6] profitable_route[5,9]
 profitable_route[2,4] profitable_route[1,2] profitable_route[2,7]
 profitable_route[1,5] profitable_route[1,8] profitable_route[7,9]
 profitable_route[6,7] profitable_route[4,7] profitable_route[3,5]
 profitable_route[3,8] profitable_route[5,8] profitable_route[1,4]
 profitable_route[2,3] profitable_route[2,9] profitable_route[1,7]
 profitable_route[2,6] profitable_route[6,9] profitable_route[7,8]
Generals
 traversed[1,2] traversed[1,6] traversed[1,7] traversed[2,3] traversed[2,7]
 traversed[2,8] traversed[2,1] traversed[3,4] traversed[3,8] traversed[3,2]
 traversed[4,5] traversed[4,8] traversed[4,3] traversed[5,6] traversed[5,9]
 traversed[5,4] traversed[6,7] traversed[6,1] traversed[6,5] traversed[7,8]
 traversed[7,9] traversed[7,1] traversed[7,2] traversed[7,6] traversed[8,9]
 traversed[8,2] traversed[8,3] traversed[8,4] traversed[8,7] traversed[9,5]
 traversed[9,7] traversed[9,8]
End
