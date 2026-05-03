import json
import boto3
from decimal import Decimal

# Helper to handle float values for DynamoDB
def float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    return obj

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Your_Table_Name') 

def lambda_handler(event, context):
    try:
        body = event
        if 'body' in event:
            body = json.loads(event['body'])
        
        # Convert data for DynamoDB storage
        item = float_to_decimal(body)
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Data saved to Cloud successfully!')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
