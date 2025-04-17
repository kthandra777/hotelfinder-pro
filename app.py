import subprocess
import sys

def run_streamlit():
    """Run the Streamlit app"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "ui.py"])

if __name__ == "__main__":
    # Only run the Streamlit app
    run_streamlit() 