import sys
from redis_manager import redis_client

def check_job_status(job_id):
    exit_code = redis_client.get(f"{job_id}:exitcode")
    stdout = redis_client.get(f"{job_id}:stdout")
    stderr = redis_client.get(f"{job_id}:stderr")
    model = redis_client.get(f"{job_id}:model")
    exec_lock = redis_client.exists(f"{job_id}:execlock")
    
    print(f"Job ID: {job_id}")
    print(f"Exit Code: {exit_code}")
    print(f"Execution Lock: {'Yes' if exec_lock else 'No'}")
    print(f"Model: {model}")
    
    if exit_code is not None:
        if int(exit_code) == 0:
            print("Status: FINISHED")
        else:
            print(f"Status: FAILED (exit code: {exit_code})")
            print(f"Error: {stderr}")
    elif exec_lock:
        print("Status: RUNNING (locked)")
    else:
        print("Status: UNKNOWN")
    
    if stdout:
        print("\nStandard Output (partial):")
        print(stdout[:500] + "..." if len(stdout) > 500 else stdout)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python redis_utils.py <job_id>")
        sys.exit(1)
    
    check_job_status(sys.argv[1])