from datetime import datetime, timedelta
from .base_scheduler import ScheduleJob, ScheduleType
from service.core.logger import Logger
from service.service_container import ServiceContainer

class TableScheduler:
    """Time-partitioned Table 자동 생성 스케줄러"""
    
    @staticmethod
    async def create_daily_tables():
        """매일 새로운 테이블 생성 (예: user_log_20240714)"""
        try:
            Logger.info("일일 테이블 생성 작업 시작")
            
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                Logger.error("데이터베이스 서비스를 찾을 수 없음")
                return
            
            today = datetime.now().strftime('%Y%m%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
            
            # 생성할 테이블 목록
            tables_to_create = [
                f"user_log_{tomorrow}",
                f"game_event_{tomorrow}",
                f"transaction_log_{tomorrow}",
                f"chat_log_{tomorrow}"
            ]
            
            success_count = 0
            
            for table_name in tables_to_create:
                try:
                    # 테이블 존재 확인
                    check_query = f"""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = '{table_name}'
                    """
                    
                    result = await db_service.call_global_read_query(check_query)
                    
                    if result and len(result) > 0 and result[0].get('count', 0) > 0:
                        Logger.info(f"테이블이 이미 존재함: {table_name}")
                        continue
                    
                    # 테이블 생성
                    await TableScheduler._create_table(db_service, table_name)
                    success_count += 1
                    
                except Exception as e:
                    Logger.error(f"테이블 생성 실패: {table_name} - {e}")
            
            Logger.info(f"일일 테이블 생성 완료: {success_count}/{len(tables_to_create)}")
            
        except Exception as e:
            Logger.error(f"일일 테이블 생성 작업 실패: {e}")
    
    @staticmethod
    async def _create_table(db_service, table_name: str):
        """특정 테이블 생성"""
        
        if table_name.startswith('user_log_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
                  `account_db_key` bigint unsigned NOT NULL,
                  `action_type` varchar(50) NOT NULL,
                  `action_data` json DEFAULT NULL,
                  `ip_address` varchar(45) DEFAULT NULL,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  KEY `idx_account_db_key` (`account_db_key`),
                  KEY `idx_action_type` (`action_type`),
                  KEY `idx_created_at` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='사용자 행동 로그 테이블'
            """
            
        elif table_name.startswith('game_event_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
                  `account_db_key` bigint unsigned NOT NULL,
                  `event_type` varchar(50) NOT NULL,
                  `event_data` json DEFAULT NULL,
                  `game_session_id` varchar(100) DEFAULT NULL,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  KEY `idx_account_db_key` (`account_db_key`),
                  KEY `idx_event_type` (`event_type`),
                  KEY `idx_game_session` (`game_session_id`),
                  KEY `idx_created_at` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='게임 이벤트 로그 테이블'
            """
            
        elif table_name.startswith('transaction_log_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
                  `account_db_key` bigint unsigned NOT NULL,
                  `transaction_type` varchar(50) NOT NULL,
                  `amount` decimal(15,2) DEFAULT NULL,
                  `currency_type` varchar(10) DEFAULT NULL,
                  `transaction_data` json DEFAULT NULL,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  KEY `idx_account_db_key` (`account_db_key`),
                  KEY `idx_transaction_type` (`transaction_type`),
                  KEY `idx_created_at` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='거래 로그 테이블'
            """
            
        elif table_name.startswith('chat_log_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
                  `account_db_key` bigint unsigned NOT NULL,
                  `channel_type` varchar(20) NOT NULL,
                  `channel_id` varchar(100) DEFAULT NULL,
                  `message` text NOT NULL,
                  `message_type` varchar(20) DEFAULT 'text',
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  KEY `idx_account_db_key` (`account_db_key`),
                  KEY `idx_channel` (`channel_type`, `channel_id`),
                  KEY `idx_created_at` (`created_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='채팅 로그 테이블'
            """
        else:
            Logger.error(f"알 수 없는 테이블 타입: {table_name}")
            return
        
        await db_service.call_global_procedure_update(create_sql)
        Logger.info(f"테이블 생성 성공: {table_name}")
    
    @staticmethod
    async def cleanup_old_tables():
        """오래된 테이블 정리 (30일 이상)"""
        try:
            Logger.info("오래된 테이블 정리 작업 시작")
            
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                Logger.error("데이터베이스 서비스를 찾을 수 없음")
                return
            
            # 30일 전 날짜
            cleanup_date = datetime.now() - timedelta(days=30)
            cleanup_suffix = cleanup_date.strftime('%Y%m%d')
            
            # 정리할 테이블 패턴
            table_patterns = [
                'user_log_',
                'game_event_',
                'transaction_log_',
                'chat_log_'
            ]
            
            cleanup_count = 0
            
            for pattern in table_patterns:
                old_table_name = f"{pattern}{cleanup_suffix}"
                
                try:
                    # 테이블 존재 확인
                    check_query = f"""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = '{old_table_name}'
                    """
                    
                    result = await db_service.call_global_read_query(check_query)
                    
                    if result and len(result) > 0 and result[0].get('count', 0) > 0:
                        # 테이블 삭제
                        drop_sql = f"DROP TABLE `{old_table_name}`"
                        await db_service.call_global_procedure_update(drop_sql)
                        
                        Logger.info(f"오래된 테이블 삭제: {old_table_name}")
                        cleanup_count += 1
                    
                except Exception as e:
                    Logger.error(f"테이블 삭제 실패: {old_table_name} - {e}")
            
            Logger.info(f"오래된 테이블 정리 완료: {cleanup_count}개 삭제")
            
        except Exception as e:
            Logger.error(f"오래된 테이블 정리 작업 실패: {e}")
    
    @staticmethod
    async def create_monthly_summary_tables():
        """월말 요약 테이블 생성"""
        try:
            Logger.info("월말 요약 테이블 생성 작업 시작")
            
            db_service = ServiceContainer.get_database_service()
            if not db_service:
                Logger.error("데이터베이스 서비스를 찾을 수 없음")
                return
            
            now = datetime.now()
            month_suffix = now.strftime('%Y%m')
            
            # 요약 테이블 목록
            summary_tables = [
                f"user_monthly_summary_{month_suffix}",
                f"game_monthly_stats_{month_suffix}",
                f"transaction_monthly_report_{month_suffix}"
            ]
            
            for table_name in summary_tables:
                try:
                    await TableScheduler._create_summary_table(db_service, table_name)
                    
                except Exception as e:
                    Logger.error(f"요약 테이블 생성 실패: {table_name} - {e}")
            
            Logger.info("월말 요약 테이블 생성 완료")
            
        except Exception as e:
            Logger.error(f"월말 요약 테이블 생성 작업 실패: {e}")
    
    @staticmethod
    async def _create_summary_table(db_service, table_name: str):
        """요약 테이블 생성"""
        
        if table_name.startswith('user_monthly_summary_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `account_db_key` bigint unsigned NOT NULL,
                  `login_count` int DEFAULT 0,
                  `total_playtime` int DEFAULT 0,
                  `last_login` datetime DEFAULT NULL,
                  `level` int DEFAULT 1,
                  `exp` bigint DEFAULT 0,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`account_db_key`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='사용자 월별 요약 테이블'
            """
            
        elif table_name.startswith('game_monthly_stats_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `stat_type` varchar(50) NOT NULL,
                  `stat_value` bigint DEFAULT 0,
                  `stat_date` date NOT NULL,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uk_stat_date` (`stat_type`, `stat_date`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='게임 월별 통계 테이블'
            """
            
        elif table_name.startswith('transaction_monthly_report_'):
            create_sql = f"""
                CREATE TABLE `{table_name}` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `transaction_type` varchar(50) NOT NULL,
                  `total_amount` decimal(15,2) DEFAULT 0,
                  `transaction_count` int DEFAULT 0,
                  `report_date` date NOT NULL,
                  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uk_report_date` (`transaction_type`, `report_date`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='거래 월별 리포트 테이블'
            """
        else:
            Logger.error(f"알 수 없는 요약 테이블 타입: {table_name}")
            return
        
        await db_service.call_global_procedure_update(create_sql)
        Logger.info(f"요약 테이블 생성 성공: {table_name}")
    
    @staticmethod
    def create_scheduler_jobs() -> list[ScheduleJob]:
        """테이블 관련 스케줄러 작업들 생성"""
        jobs = []
        
        # 1. 매일 오전 2시에 새 테이블 생성
        daily_table_job = ScheduleJob(
            job_id="daily_table_creation",
            name="일일 테이블 생성",
            schedule_type=ScheduleType.DAILY,
            schedule_value="02:00",  # 오전 2시
            callback=TableScheduler.create_daily_tables,
            use_distributed_lock=True,
            lock_key="scheduler:create_daily_tables",
            lock_ttl=1800  # 30분
        )
        jobs.append(daily_table_job)
        
        # 2. 매일 오전 3시에 오래된 테이블 정리
        cleanup_job = ScheduleJob(
            job_id="cleanup_old_tables",
            name="오래된 테이블 정리",
            schedule_type=ScheduleType.DAILY,
            schedule_value="03:00",  # 오전 3시
            callback=TableScheduler.cleanup_old_tables,
            use_distributed_lock=True,
            lock_key="scheduler:cleanup_tables",
            lock_ttl=1800  # 30분
        )
        jobs.append(cleanup_job)
        
        # 3. 매월 1일 오전 4시에 월별 요약 테이블 생성
        # 실제로는 cron 표현식이나 더 정교한 스케줄링 필요
        # 여기서는 간단히 매일 체크해서 월 초에만 실행하도록 구현
        monthly_summary_job = ScheduleJob(
            job_id="monthly_summary_tables",
            name="월별 요약 테이블 생성",
            schedule_type=ScheduleType.DAILY,
            schedule_value="04:00",  # 오전 4시
            callback=TableScheduler._monthly_summary_wrapper,
            use_distributed_lock=True,
            lock_key="scheduler:monthly_summary",
            lock_ttl=3600  # 1시간
        )
        jobs.append(monthly_summary_job)
        
        return jobs
    
    @staticmethod
    async def _monthly_summary_wrapper():
        """월별 요약 작업 래퍼 (매월 1일에만 실행)"""
        now = datetime.now()
        
        # 매월 1일에만 실행
        if now.day == 1:
            await TableScheduler.create_monthly_summary_tables()
        else:
            Logger.debug("월별 요약 테이블 생성 스킵 (매월 1일이 아님)")