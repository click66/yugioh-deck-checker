#!/usr/bin/env bash
set -e

# Ensure awslocal is installed
if ! command -v awslocal &> /dev/null; then
    echo "Installing awscli-local..."
    pip install awscli-local
fi

echo "Waiting for LocalStack SQS to be ready..."
until awslocal sqs list-queues >/dev/null 2>&1; do
  sleep 1
done

echo "Creating test SQS queue..."
awslocal sqs create-queue --queue-name yugioh-deck-checker-local-consistency --region eu-west-2

echo "Creating test Lambda function..."

# Create a test Lambda function
awslocal lambda create-function \
    --function-name yugioh-deck-checker-local-consistency \
    --runtime python3.11 \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --region eu-west-2 \
    --handler lambda_function.handler \
    --zip-file fileb://lambda_function.zip || echo "Lambda already exists"

# Setup DynamoDB
echo "Creating DynamoDB table for jobs with batch_id GSI..."

awslocal dynamodb create-table \
    --table-name yugioh-deck-checker-local-jobs \
    --attribute-definitions \
        AttributeName=job_id,AttributeType=S \
        AttributeName=batch_id,AttributeType=S \
    --key-schema AttributeName=job_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --global-secondary-indexes '[
        {
            "IndexName": "batch_id-index",
            "KeySchema":[{"AttributeName":"batch_id","KeyType":"HASH"}],
            "Projection":{"ProjectionType":"ALL"}
        }
    ]' \
    || echo "Table already exists"

echo "LocalStack initialization complete."