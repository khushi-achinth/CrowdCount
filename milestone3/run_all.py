import subprocess, sys

subprocess.Popen([sys.executable, "backend/app.py"])
subprocess.Popen([sys.executable, "detectors/entrance_detector.py"])
subprocess.Popen([sys.executable, "detectors/retail_detector.py"])
subprocess.Popen([sys.executable, "detectors/foodcourt_detector.py"])
