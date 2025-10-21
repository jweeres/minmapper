import subprocess
import argparse

try:
    subprocess.call(["python3", "mip_const_penalty.py"])
except:
    print("Couldn't find a feasible solution in time limit for mip_lb")

try:
    subprocess.call(["python3", "mip_model_rem_aggressive.py"])
except:
    print("Couldn't find a feasible solution in time limit for mip_model_rem_aggressive")

try:
    subprocess.call(["python3", "mip_model.py"])
except:
    print("Couldn't find a feasible solution in time limit for mip_model")

try:
    subprocess.call(["python3", "mip_model_with_branching.py"])
except:
    print("Couldn't find a feasible solution in time limit for mip_model_with_branching")

try:
    subprocess.call(["python3", "mip_lb.py"])
except:
    print("Couldn't find a feasible solution in time limit for mip_lb")

# try:
#     subprocess.call(["python3", "mip_const_penalty.py"])
# except:
#     print("Couldn't find a feasible solution in time limit for mip_lb")

