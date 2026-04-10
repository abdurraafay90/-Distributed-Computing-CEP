import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize DynamoDB resource
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def create_tasks_table():
    try:
        print("Attempting to create 'CS432_Tasks' table...")
        table = dynamodb.create_table(
            TableName='CS432_Tasks',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'task_timestamp', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'task_timestamp', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("Table status:", table.table_status)
        print("Waiting for table to be active...")
        table.meta.client.get_waiter('table_exists').wait(TableName='CS432_Tasks')
        print("Table 'CS432_Tasks' created successfully!")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("Table 'CS432_Tasks' already exists.")
        else:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_tasks_table()
