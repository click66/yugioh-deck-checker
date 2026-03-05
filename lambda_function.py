def handler(event, context):
    return {"statusCode": 200, "body": f"Hello from Local Lambda! Received: {event}"}