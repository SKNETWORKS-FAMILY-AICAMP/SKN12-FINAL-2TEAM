import asyncio
import aioboto3
import time
import random
from typing import Dict, Any, Optional, BinaryIO
from dataclasses import dataclass
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from botocore.config import Config
from service.core.logger import Logger
from .storage_client import IStorageClient

@dataclass
class S3Metrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_upload_time: float = 0.0
    total_download_time: float = 0.0
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    last_operation_time: Optional[float] = None
    connection_failures: int = 0
    credential_errors: int = 0

class S3StorageClient(IStorageClient):
    """AWS S3 Storage 클라이언트 - Session 재사용 패턴"""
    
    def __init__(self, config, session=None, s3_client=None):
        self.config = config
        # 디버깅을 위한 로깅
        from service.core.logger import Logger
        Logger.debug(f"S3Client config type: {type(config)}")
        Logger.debug(f"S3Client config: {config}")
        # Pool에서 전달받은 session과 client 사용
        self._session = session
        self._s3_client = s3_client
        self.metrics = S3Metrics()
        self._connection_healthy = True
        self._last_health_check = 0
        self._max_retries = 3
        self._retry_delay_base = 1.0
    
    async def _get_client(self):
        """S3 클라이언트 가져오기 (Pool에서 전달받은 client 사용)"""
        if self._s3_client is None:
            raise RuntimeError("S3 client not initialized by pool")
        # AsyncExitStack으로 관리되는 클라이언트는 직접 사용 가능
        return self._s3_client
    
    async def upload_file(self, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 업로드 (향상된 에러 처리 및 메트릭)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                s3_client = await self._get_client()
                
                # 메타데이터 설정
                extra_args = kwargs.get('extra_args', {})
                
                # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
                await s3_client.upload_file(
                    Filename=file_path,
                    Bucket=bucket,
                    Key=key,
                    ExtraArgs=extra_args
                )
                
                # 성공 메트릭 기록
                upload_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_upload_time += upload_time
                
                # 파일 크기 계산 (가능한 경우)
                try:
                    import os
                    file_size = os.path.getsize(file_path)
                    self.metrics.bytes_uploaded += file_size
                except:
                    pass
                
                self._connection_healthy = True
                Logger.info(f"S3 upload success: s3://{bucket}/{key} ({upload_time:.3f}s)")
                return {
                    "success": True,
                    "bucket": bucket,
                    "key": key,
                    "file_path": file_path,
                    "upload_time": upload_time,
                    "attempt": attempt + 1
                }
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                Logger.warn(f"S3 upload client error (attempt {attempt + 1}/{self._max_retries}): {error_code} - {e}")
                
                if error_code in ['NoSuchBucket', 'AccessDenied', 'InvalidBucketName']:
                    # 재시도해도 해결되지 않는 오류들
                    break
                    
            except EndpointConnectionError as e:
                self._connection_healthy = False
                Logger.warn(f"S3 connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"S3 upload error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"S3 upload failed after {self._max_retries} attempts: s3://{bucket}/{key} (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Upload failed after {self._max_retries} attempts",
            "bucket": bucket,
            "key": key,
            "total_time": total_time,
            "attempts": self._max_retries
        }
            
    
    async def upload_file_obj(self, bucket: str, key: str, file_obj: BinaryIO, **kwargs) -> Dict[str, Any]:
        """파일 객체 업로드"""
        try:
            s3_client = await self._get_client()
            
            extra_args = kwargs.get('extra_args', {})
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            await s3_client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=bucket,
                Key=key,
                ExtraArgs=extra_args
            )
            
            Logger.info(f"S3 upload_fileobj success: s3://{bucket}/{key}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key
            }
            
        except Exception as e:
            Logger.error(f"S3 upload_fileobj failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(self, bucket: str, key: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """파일 다운로드"""
        try:
            s3_client = await self._get_client()
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            await s3_client.download_file(
                Bucket=bucket,
                Key=key,
                Filename=file_path
            )
            
            Logger.info(f"S3 download success: s3://{bucket}/{key} -> {file_path}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key,
                "file_path": file_path
            }
            
        except Exception as e:
            Logger.error(f"S3 download failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file_obj(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 객체로 다운로드"""
        try:
            s3_client = await self._get_client()
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            response = await s3_client.get_object(Bucket=bucket, Key=key)
            content = await response['Body'].read()
            
            Logger.info(f"S3 get_object success: s3://{bucket}/{key}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key,
                "content": content,
                "metadata": response.get('Metadata', {})
            }
            
        except Exception as e:
            Logger.error(f"S3 get_object failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_file(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 삭제"""
        try:
            s3_client = await self._get_client()
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            await s3_client.delete_object(Bucket=bucket, Key=key)
            
            Logger.info(f"S3 delete success: s3://{bucket}/{key}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key
            }
            
        except Exception as e:
            Logger.error(f"S3 delete failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_files(self, bucket: str, prefix: str = "", **kwargs) -> Dict[str, Any]:
        """파일 목록 조회"""
        try:
            s3_client = await self._get_client()
            
            list_kwargs = {
                'Bucket': bucket,
                'Prefix': prefix
            }
            
            # 페이지네이션 지원
            max_keys = kwargs.get('max_keys', 1000)
            if max_keys:
                list_kwargs['MaxKeys'] = max_keys
            
            continuation_token = kwargs.get('continuation_token')
            if continuation_token:
                list_kwargs['ContinuationToken'] = continuation_token
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            response = await s3_client.list_objects_v2(**list_kwargs)
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag']
                    })
            
            Logger.info(f"S3 list success: s3://{bucket}/{prefix} - {len(files)} files")
            return {
                "success": True,
                "bucket": bucket,
                "prefix": prefix,
                "files": files,
                "is_truncated": response.get('IsTruncated', False),
                "next_continuation_token": response.get('NextContinuationToken')
            }
            
        except Exception as e:
            Logger.error(f"S3 list failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_file_info(self, bucket: str, key: str, **kwargs) -> Dict[str, Any]:
        """파일 정보 조회"""
        try:
            s3_client = await self._get_client()
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            response = await s3_client.head_object(Bucket=bucket, Key=key)
            
            Logger.info(f"S3 head_object success: s3://{bucket}/{key}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key,
                "size": response.get('ContentLength'),
                "last_modified": response.get('LastModified').isoformat() if response.get('LastModified') else None,
                "etag": response.get('ETag'),
                "content_type": response.get('ContentType'),
                "metadata": response.get('Metadata', {})
            }
            
        except Exception as e:
            Logger.error(f"S3 head_object failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # === 모니터링 및 관리 메소드들 ===
    
    async def health_check(self) -> Dict[str, Any]:
        """S3 연결 상태 확인"""
        start_time = time.time()
        
        try:
            s3_client = await self._get_client()
            
            # 간단한 list_buckets 호출로 연결 확인
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            await s3_client.list_buckets()
            
            response_time = time.time() - start_time
            self._connection_healthy = True
            self._last_health_check = time.time()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "connection_healthy": self._connection_healthy,
                "region": self.config.region_name,
                "metrics": self.get_metrics()
            }
            
        except NoCredentialsError as e:
            return {
                "healthy": False,
                "error": f"Credentials error: {e}",
                "error_type": "credentials",
                "connection_healthy": False,
                "metrics": self.get_metrics()
            }
        except EndpointConnectionError as e:
            self._connection_healthy = False
            return {
                "healthy": False,
                "error": f"Connection error: {e}",
                "error_type": "connection",
                "connection_healthy": False,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            self._connection_healthy = False
            return {
                "healthy": False,
                "error": str(e),
                "error_type": "unknown",
                "connection_healthy": False,
                "metrics": self.get_metrics()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """S3 클라이언트 메트릭 조회"""
        avg_upload_time = 0.0
        avg_download_time = 0.0
        success_rate = 0.0
        
        if self.metrics.successful_operations > 0:
            if self.metrics.total_upload_time > 0:
                # 업로드 시간은 업로드 작업에만 기반
                upload_operations = max(1, self.metrics.successful_operations // 2)  # 추정
                avg_upload_time = self.metrics.total_upload_time / upload_operations
            
            if self.metrics.total_download_time > 0:
                download_operations = max(1, self.metrics.successful_operations // 2)  # 추정
                avg_download_time = self.metrics.total_download_time / download_operations
        
        if self.metrics.total_operations > 0:
            success_rate = self.metrics.successful_operations / self.metrics.total_operations
        
        return {
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": success_rate,
            "average_upload_time": avg_upload_time,
            "average_download_time": avg_download_time,
            "bytes_uploaded": self.metrics.bytes_uploaded,
            "bytes_downloaded": self.metrics.bytes_downloaded,
            "connection_failures": self.metrics.connection_failures,
            "credential_errors": self.metrics.credential_errors,
            "last_operation_time": self.metrics.last_operation_time,
            "connection_healthy": self._connection_healthy,
            "last_health_check": self._last_health_check
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = S3Metrics()
        Logger.info("S3 client metrics reset")
    
    
    async def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600, **kwargs) -> Dict[str, Any]:
        """사전 서명된 URL 생성"""
        try:
            s3_client = await self._get_client()
            
            method = kwargs.get('method', 'get_object')
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            url = await s3_client.generate_presigned_url(
                ClientMethod=method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            
            Logger.info(f"S3 presigned URL generated: s3://{bucket}/{key}")
            return {
                "success": True,
                "bucket": bucket,
                "key": key,
                "url": url,
                "expiration": expiration
            }
            
        except Exception as e:
            Logger.error(f"S3 generate_presigned_url failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def copy_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 복사"""
        try:
            s3_client = await self._get_client()
            
            copy_source = {
                'Bucket': source_bucket,
                'Key': source_key
            }
            
            # AsyncExitStack으로 관리되는 클라이언트는 직접 사용
            await s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            
            Logger.info(f"S3 copy success: s3://{source_bucket}/{source_key} -> s3://{dest_bucket}/{dest_key}")
            return {
                "success": True,
                "source_bucket": source_bucket,
                "source_key": source_key,
                "dest_bucket": dest_bucket,
                "dest_key": dest_key
            }
            
        except Exception as e:
            Logger.error(f"S3 copy failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def move_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str, **kwargs) -> Dict[str, Any]:
        """파일 이동"""
        try:
            # 복사 후 삭제
            copy_result = await self.copy_file(source_bucket, source_key, dest_bucket, dest_key, **kwargs)
            if not copy_result["success"]:
                return copy_result
            
            delete_result = await self.delete_file(source_bucket, source_key)
            if not delete_result["success"]:
                Logger.warn(f"S3 move: copy succeeded but delete failed: {delete_result['error']}")
                return delete_result
            
            Logger.info(f"S3 move success: s3://{source_bucket}/{source_key} -> s3://{dest_bucket}/{dest_key}")
            return {
                "success": True,
                "source_bucket": source_bucket,
                "source_key": source_key,
                "dest_bucket": dest_bucket,
                "dest_key": dest_key
            }
            
        except Exception as e:
            Logger.error(f"S3 move failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """클라이언트 종료 - Pool에서 관리하므로 개별 클라이언트는 정리하지 않음"""
        # Pool에서 session과 client를 관리하므로 개별 클라이언트에서는 정리하지 않음
        Logger.debug("S3 Storage client close called (managed by pool)")