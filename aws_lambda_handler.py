import json
import boto3
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Your_Table_Name_Here') # Change to your actual table name

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        # Format data for DynamoDB (it prefers Decimals over Floats)
        item = {
            'user_id': body['user_id'],
            'timestamp': body['timestamp'],
            'appliance': body['appliance'],
            'watts': Decimal(str(body['watts'])),
            'units': Decimal(str(body.get('units', 0))),
            'bill': Decimal(str(body['bill']))
        }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Success!'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
