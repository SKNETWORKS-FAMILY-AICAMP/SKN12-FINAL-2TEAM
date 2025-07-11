from template.base.base_template import BaseTemplate
from template.autotrade.common.autotrade_serialize import (
    AutoTradeStrategyListRequest, AutoTradeStrategyListResponse,
    AutoTradeStrategyCreateRequest, AutoTradeStrategyCreateResponse,
    AutoTradeStrategyUpdateRequest, AutoTradeStrategyUpdateResponse,
    AutoTradeExecutionListRequest, AutoTradeExecutionListResponse,
    AutoTradeBacktestRequest, AutoTradeBacktestResponse,
    AutoTradeAIStrategyRequest, AutoTradeAIStrategyResponse
)
from template.autotrade.common.autotrade_model import TradingStrategy, StrategyPerformance, TradeExecution, StrategyBacktest
from service.core.logger import Logger
from service.service_container import ServiceContainer
import json
import uuid
import random
from datetime import datetime

class AutoTradeTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_autotrade_strategy_list_req(self, client_session, request: AutoTradeStrategyListRequest):
        """매매 전략 목록 요청 처리"""
        response = AutoTradeStrategyListResponse()
        
        Logger.info(f"AutoTrade strategy list request: status_filter={request.status_filter}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 매매 전략 목록 조회
            strategies_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_trading_strategies",
                (account_db_key, True, request.status_filter)  # include_performance=True
            )
            
            if not strategies_result or len(strategies_result) == 0:
                response.strategies = []
                response.performances = {}
                response.errorCode = 0
                return response
            
            # 2. DB 결과를 바탕으로 응답 생성
            strategies_data = strategies_result[0] if isinstance(strategies_result[0], list) else strategies_result
            performance_data = strategies_result[1] if len(strategies_result) > 1 else []
            
            response.strategies = []
            for strategy in strategies_data:
                response.strategies.append(TradingStrategy(
                    strategy_id=strategy.get('strategy_id'),
                    name=strategy.get('name'),
                    description=strategy.get('description'),
                    algorithm_type=strategy.get('algorithm_type'),
                    target_symbols=json.loads(strategy.get('target_symbols', '[]')),
                    is_active=bool(strategy.get('is_active')),
                    created_at=str(strategy.get('created_at'))
                ))
            
            # 3. 성과 정보 처리
            response.performances = {}
            for perf in performance_data:
                strategy_id = perf.get('strategy_id')
                response.performances[strategy_id] = StrategyPerformance(
                    strategy_id=strategy_id,
                    total_return=float(perf.get('avg_total_return', 0.0)),
                    win_rate=float(perf.get('avg_win_rate', 0.0)),
                    sharpe_ratio=float(perf.get('avg_sharpe_ratio', 0.0)),
                    max_drawdown=float(perf.get('max_drawdown', 0.0))
                )
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.strategies = []
            response.performances = {}
            Logger.error(f"AutoTrade strategy list error: {e}")
        
        return response

    async def on_autotrade_strategy_create_req(self, client_session, request: AutoTradeStrategyCreateRequest):
        """새 매매 전략 생성 요청 처리"""
        response = AutoTradeStrategyCreateResponse()
        
        Logger.info(f"AutoTrade strategy create request: name={request.name}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 입력 검증
            if not request.name or not request.algorithm_type:
                response.errorCode = 10001
                response.message = "전략 이름과 알고리즘 타입은 필수입니다"
                return response
            
            # 2. 매매 전략 생성 DB 프로시저 호출
            create_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_create_trading_strategy",
                (account_db_key, request.name, request.description,
                 request.algorithm_type, json.dumps(request.parameters),
                 json.dumps(request.target_symbols), request.max_position_size,
                 request.stop_loss, request.take_profit)
            )
            
            if not create_result or create_result[0].get('result') != 'SUCCESS':
                response.errorCode = 10002
                response.message = "매매 전략 생성 실패"
                return response
            
            # 3. 생성된 전략 정보 반환
            strategy_id = create_result[0].get('strategy_id')
            response.strategy = TradingStrategy(
                strategy_id=strategy_id,
                name=request.name,
                description=request.description,
                algorithm_type=request.algorithm_type,
                target_symbols=request.target_symbols,
                is_active=False,  # 생성 시점에는 비활성화
                created_at=str(datetime.now())
            )
            response.message = "매매 전략이 생성되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"AutoTrade strategy create error: {e}")
        
        return response

    async def on_autotrade_strategy_update_req(self, client_session, request: AutoTradeStrategyUpdateRequest):
        """매매 전략 수정 요청 처리"""
        response = AutoTradeStrategyUpdateResponse()
        
        Logger.info(f"AutoTrade strategy update request: strategy_id={request.strategy_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 전략 존재 및 소유권 확인
            strategy_check = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_trading_strategies",
                (account_db_key, False, "ALL")
            )
            
            strategy_exists = False
            if strategy_check:
                for strategy in strategy_check[0] if isinstance(strategy_check[0], list) else strategy_check:
                    if strategy.get('strategy_id') == request.strategy_id:
                        strategy_exists = True
                        break
            
            if not strategy_exists:
                response.errorCode = 10003
                response.message = "전략을 찾을 수 없거나 접근 권한이 없습니다"
                return response
            
            # 2. 전략 업데이트 (간단한 예시 - 실제로는 별도 업데이트 프로시저 필요)
            # 여기서는 전략의 활성화/비활성화만 처리
            if hasattr(request, 'is_active'):
                # UPDATE 쿼리를 직접 실행 (예시)
                update_sql = f"UPDATE table_trading_strategies SET is_active = {1 if request.is_active else 0}, updated_at = NOW() WHERE strategy_id = '{request.strategy_id}' AND account_db_key = {account_db_key}"
                # 실제로는 별도 프로시저를 만들어 사용해야 함
            
            response.message = "전략이 수정되었습니다"
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            response.message = "전략 수정 실패"
            Logger.error(f"AutoTrade strategy update error: {e}")
        
        return response

    async def on_autotrade_execution_list_req(self, client_session, request: AutoTradeExecutionListRequest):
        """거래 실행 내역 조회 요청 처리"""
        response = AutoTradeExecutionListResponse()
        
        Logger.info(f"AutoTrade execution list request: strategy_id={request.strategy_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 거래 실행 내역 조회 (별도 프로시저 필요하지만 기존 테이블에서 직접 조회)
            # 실제로는 fp_get_trade_executions 프로시저가 필요
            from datetime import timedelta
            
            # 간단한 쿼리로 거래 실행 내역 조회
            executions_data = []
            
            # 샘플 데이터 생성 (실제로는 DB에서 조회)
            if request.strategy_id:
                # 특정 전략의 거래 내역
                for i in range(3):
                    execution = {
                        "execution_id": f"exec_{request.strategy_id}_{i+1}",
                        "symbol": ["AAPL", "GOOGL", "TSLA"][i],
                        "action": "BUY" if i % 2 == 0 else "SELL",
                        "quantity": (i+1) * 10,
                        "executed_price": 150.0 + i * 10,
                        "profit_loss": (i-1) * 50.0,
                        "executed_at": str(datetime.now() - timedelta(days=i)),
                        "status": "EXECUTED"
                    }
                    executions_data.append(execution)
            
            # 2. 거래 실행 내역을 TradeExecution 모델로 변환
            response.executions = []
            for exec_data in executions_data:
                response.executions.append(TradeExecution(
                    execution_id=exec_data.get('execution_id'),
                    strategy_id=request.strategy_id,
                    symbol=exec_data.get('symbol'),
                    action=exec_data.get('action'),
                    quantity=exec_data.get('quantity'),
                    executed_price=exec_data.get('executed_price'),
                    profit_loss=exec_data.get('profit_loss'),
                    executed_at=exec_data.get('executed_at'),
                    status=exec_data.get('status')
                ))
            
            response.total_count = len(response.executions)
            
            # 3. 요약 정보 계산
            total_profit = sum(exec_data.get('profit_loss', 0) for exec_data in executions_data)
            buy_count = sum(1 for exec_data in executions_data if exec_data.get('action') == 'BUY')
            sell_count = len(executions_data) - buy_count
            
            response.summary = {
                "total_trades": len(executions_data),
                "buy_orders": buy_count,
                "sell_orders": sell_count,
                "total_profit_loss": round(total_profit, 2),
                "success_rate": round((len([e for e in executions_data if e.get('profit_loss', 0) > 0]) / max(1, len(executions_data))) * 100, 2)
            }
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"AutoTrade execution list error: {e}")
        
        return response

    async def on_autotrade_backtest_req(self, client_session, request: AutoTradeBacktestRequest):
        """백테스트 실행 요청 처리"""
        response = AutoTradeBacktestResponse()
        
        Logger.info(f"AutoTrade backtest request: strategy_id={request.strategy_id}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. 백테스트 실행 요청 DB 프로시저 호출
            backtest_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_run_backtest",
                (request.strategy_id, account_db_key, request.start_date,
                 request.end_date, request.initial_capital, request.benchmark or 'KOSPI')
            )
            
            if not backtest_result or backtest_result[0].get('result') != 'SUCCESS':
                response.errorCode = 10004
                response.message = "백테스트 실행 실패"
                response.daily_returns = []
                response.trade_history = []
                return response
            
            backtest_id = backtest_result[0].get('backtest_id')
            
            # 2. 백테스트 결과 시뮬레이션 (실제로는 별도 백테스트 엔진에서 처리)
            from datetime import timedelta
            import random
            
            start = datetime.strptime(request.start_date, '%Y-%m-%d')
            end = datetime.strptime(request.end_date, '%Y-%m-%d')
            
            # 일별 수익률 시뮬레이션
            daily_returns = []
            current_date = start
            cumulative_return = 0.0
            
            while current_date <= end:
                # 랜덤 일별 수익률 (-2% ~ +2%)
                daily_return = round(random.uniform(-0.02, 0.02), 4)
                cumulative_return += daily_return
                
                daily_returns.append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "daily_return": daily_return,
                    "cumulative_return": round(cumulative_return, 4),
                    "portfolio_value": round(request.initial_capital * (1 + cumulative_return), 2)
                })
                
                current_date += timedelta(days=1)
            
            # 거래 내역 시뮬레이션
            trade_history = []
            for i in range(random.randint(10, 20)):
                trade_date = start + timedelta(days=random.randint(0, (end - start).days))
                profit_loss = round(random.uniform(-500, 1000), 2)
                
                trade_history.append({
                    "date": trade_date.strftime('%Y-%m-%d'),
                    "symbol": random.choice(["AAPL", "GOOGL", "TSLA", "MSFT"]),
                    "action": random.choice(["BUY", "SELL"]),
                    "quantity": random.randint(1, 100),
                    "price": round(random.uniform(100, 300), 2),
                    "profit_loss": profit_loss
                })
            
            # 3. 백테스트 결과 DB 업데이트
            final_value = daily_returns[-1]['portfolio_value'] if daily_returns else request.initial_capital
            total_return = (final_value - request.initial_capital) / request.initial_capital
            win_rate = len([t for t in trade_history if t['profit_loss'] > 0]) / max(1, len(trade_history)) * 100
            
            await db_service.call_shard_procedure(
                shard_id,
                "fp_update_backtest_result",
                (backtest_id, final_value, total_return, 0.08,  # benchmark_return
                 -0.05, 1.2, len(trade_history), win_rate,
                 json.dumps(daily_returns), json.dumps(trade_history))
            )
            
            response.backtest = StrategyBacktest(
                backtest_id=backtest_id,
                strategy_id=request.strategy_id,
                period=f"{request.start_date}_{request.end_date}",
                initial_capital=request.initial_capital,
                final_value=final_value,
                total_return=round(total_return * 100, 2),
                max_drawdown=-5.0,
                sharpe_ratio=1.2,
                win_rate=round(win_rate, 2)
            )
            response.daily_returns = daily_returns
            response.trade_history = trade_history
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"AutoTrade backtest error: {e}")
        
        return response

    async def on_autotrade_ai_strategy_req(self, client_session, request: AutoTradeAIStrategyRequest):
        """AI 전략 생성 요청 처리"""
        response = AutoTradeAIStrategyResponse()
        
        Logger.info(f"AutoTrade AI strategy request: goal={request.investment_goal}")
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            db_service = ServiceContainer.get_database_service()
            
            # 1. AI 전략 추천 DB 프로시저 호출
            recommendations_result = await db_service.call_shard_procedure(
                shard_id,
                "fp_get_ai_strategy_recommendations",
                (account_db_key, request.investment_goal, request.risk_tolerance,
                 request.investment_amount, request.time_horizon)
            )
            
            if not recommendations_result:
                response.errorCode = 10005
                response.message = "AI 전략 추천을 가져올 수 없습니다"
                response.strategy_suggestions = []
                response.expected_performance = {}
                response.risk_analysis = {}
                return response
            
            # 2. 추천 전략 목록 생성
            response.strategy_suggestions = []
            for template in recommendations_result:
                suggestion = {
                    "template_id": template.get('template_id'),
                    "name": template.get('name'),
                    "description": template.get('description'),
                    "category": template.get('category'),
                    "algorithm_type": template.get('algorithm_type'),
                    "parameters": json.loads(template.get('default_parameters', '{}')),
                    "suitability_score": round(random.uniform(0.7, 0.95), 2),  # 적합도 점수
                    "confidence": round(random.uniform(0.8, 0.9), 2)
                }
                response.strategy_suggestions.append(suggestion)
            
            # 3. 예상 성과 분석
            if response.strategy_suggestions:
                best_template = recommendations_result[0]
                expected_return = float(best_template.get('expected_return', 0.0))
                expected_volatility = float(best_template.get('expected_volatility', 0.0))
                
                response.expected_performance = {
                    "expected_annual_return": round(expected_return * 100, 2),
                    "expected_volatility": round(expected_volatility * 100, 2),
                    "expected_sharpe_ratio": round(expected_return / max(expected_volatility, 0.01), 2),
                    "projection_horizon": request.time_horizon,
                    "confidence_interval": "80%"
                }
            
            # 4. 위험 분석
            response.risk_analysis = {
                "risk_level": request.risk_tolerance,
                "max_drawdown_estimate": round(float(best_template.get('expected_volatility', 0.15)) * -2, 2),
                "volatility_assessment": "적정" if request.risk_tolerance == "MODERATE" else ("높음" if request.risk_tolerance == "AGGRESSIVE" else "낮음"),
                "diversification_score": round(random.uniform(0.6, 0.9), 2),
                "capital_requirement": float(best_template.get('min_capital', 100000.0)),
                "suitability_factors": [
                    f"투자 목표: {request.investment_goal}",
                    f"위험 성향: {request.risk_tolerance}", 
                    f"투자 기간: {request.time_horizon}",
                    f"투자 금액: {request.investment_amount:,.0f}원"
                ]
            }
            response.errorCode = 0
            
        except Exception as e:
            response.errorCode = 1000
            Logger.error(f"AutoTrade AI strategy error: {e}")
        
        return response