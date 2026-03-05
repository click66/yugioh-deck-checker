# Yu-Gi-Oh! Deck Checker

## API implementation

Simple version 1 will feature the ability to deploy and run simple deck consistency checks.

- FastAPI API with endpoints to register and query jobs
- Redis storage for short term storage of jobs and results (job ID, status, results)
- AWS Lambda function containing consistency code (triggered by POST API endpoint)

Steps:

1. POST API creates job ID, stores required data in Redis, triggers Lambda
2. Lambda runs, writes results to Redis store when done
3. GET API queries for Redis job status, returns results when done

Deployment to Lambda: https://medium.com/@kaliarch/deploying-python-fastapi-on-aws-lambda-a-practical-guide-66c9df217cdc
