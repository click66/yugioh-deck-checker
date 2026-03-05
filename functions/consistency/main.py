# functions/consistency/main.py

def lambda_handler(event, context):
    job_id = event.get("job_id")
    print(f"Hello from app! Processing job {job_id}")
    # Your long-running job logic here
    return {"status": "started", "job_id": job_id}


# Optional: keep a CLI entrypoint if you want to run locally
def main():
    print("Hello from app!")

if __name__ == "__main__":
    main()