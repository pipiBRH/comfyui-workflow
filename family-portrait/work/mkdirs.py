import os
for d in ("/content/famjob/uploads", "/content/outputs"):
    os.makedirs(d, exist_ok=True)
print("dirs ok")
