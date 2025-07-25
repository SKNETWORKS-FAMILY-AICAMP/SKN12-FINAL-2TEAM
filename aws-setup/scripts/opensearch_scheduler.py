import boto3
import json
from datetime import datetime
import pytz

opensearch = boto3.client('opensearch')
eventbridge = boto3.client('events')

def lambda_handler(event, context):
    domain_name = 'skn12-knowledge-search'
    action = event.get('action', 'status')  # start, stop, status
    
    try:
        if action == 'start':
            # OpenSearch 도메인 시작 (인스턴스 수 1로 변경)
            response = opensearch.update_domain_config(
                DomainName=domain_name,
                ClusterConfig={
                    'InstanceType': 't3.small.search',
                    'InstanceCount': 1,
                    'DedicatedMasterEnabled': False
                }
            )
            return {'statusCode': 200, 'body': 'OpenSearch 시작됨'}
            
        elif action == 'stop':
            # OpenSearch 도메인 중지 (인스턴스 수 0으로 변경)
            response = opensearch.update_domain_config(
                DomainName=domain_name,
                ClusterConfig={
                    'InstanceType': 't3.small.search',
                    'InstanceCount': 0,
                    'DedicatedMasterEnabled': False
                }
            )
            return {'statusCode': 200, 'body': 'OpenSearch 중지됨'}
            
        else:
            # 현재 상태 확인
            response = opensearch.describe_domain(DomainName=domain_name)
            instance_count = response['DomainStatus']['ClusterConfig']['InstanceCount']
            processing = response['DomainStatus']['Processing']
            
            return {
                'statusCode': 200, 
                'body': f'인스턴스 수: {instance_count}, 처리중: {processing}'
            }
            
    except Exception as e:
        return {'statusCode': 500, 'body': f'오류: {str(e)}'}