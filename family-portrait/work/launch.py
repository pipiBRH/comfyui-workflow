import subprocess, os
STAGES = os.environ.get("FAM_STAGES", "")
p = subprocess.Popen(["python3", "-u", "/content/famjob/family_pipeline.py", *STAGES.split()],
                     stdout=open("/content/family.log", "a"), stderr=subprocess.STDOUT, start_new_session=True)
print("started family pipeline pid", p.pid, "stages:", STAGES)
