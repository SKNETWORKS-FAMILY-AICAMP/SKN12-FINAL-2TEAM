from fastapi import APIRouter, Request, Body
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.crawler.common.crawler_serialize import (
    CrawlerExecuteRequest, CrawlerStatusRequest, CrawlerHealthRequest,
    CrawlerStopRequest, CrawlerDataRequest
)
from template.crawler.common.crawler_protocol import CrawlerProtocol
from service.core.logger import Logger
from datetime import datetime

router = APIRouter()

crawler_protocol = CrawlerProtocol()

def setup_crawler_protocol_callbacks():
    """Crawler protocol 콜백 설정"""
    crawler_template = TemplateContext.get_template(TemplateType.CRAWLER)
    crawler_protocol.on_crawler_execute_req_callback = getattr(crawler_template, "on_crawler_execute_req", None)
    crawler_protocol.on_crawler_status_req_callback = getattr(crawler_template, "on_crawler_status_req", None)
    crawler_protocol.on_crawler_health_req_callback = getattr(crawler_template, "on_crawler_health_req", None)
    crawler_protocol.on_crawler_stop_req_callback = getattr(crawler_template, "on_crawler_stop_req", None)
    crawler_protocol.on_crawler_data_req_callback = getattr(crawler_template, "on_crawler_data_req", None)

@router.post("/execute")
async def execute_crawler(request: CrawlerExecuteRequest, req: Request):
    """
    크롤러 작업 실행 엔드포인트
    - AWS Lambda에서 주기적으로 호출
    - 분산락을 사용하여 중복 실행 방지
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        crawler_protocol.crawler_execute_req_controller
    )

@router.post("/status")
async def crawler_status(request: CrawlerStatusRequest, req: Request):
    """
    크롤러 상태 조회 엔드포인트
    - 실행 중인 작업 목록 조회
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        crawler_protocol.crawler_status_req_controller
    )

@router.post("/health")
async def crawler_health(request: CrawlerHealthRequest, req: Request):
    """
    크롤러 헬스체크 엔드포인트
    - 크롤러 서비스 상태 확인
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        crawler_protocol.crawler_health_req_controller
    )

@router.post("/stop")
async def stop_crawler(request: CrawlerStopRequest, req: Request):
    """
    크롤러 작업 중단 엔드포인트
    - 실행 중인 작업 강제 중단
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        crawler_protocol.crawler_stop_req_controller
    )

@router.post("/data")
async def crawler_data(request: CrawlerDataRequest, req: Request):
    """
    크롤러 데이터 조회 엔드포인트
    - 크롤링된 데이터 조회
    """
    ip = req.headers.get("X-Forwarded-For")
    if not ip:
        ip = req.client.host
    else:
        ip = ip.split(", ")[0]
    return await TemplateService.run_administrator(
        req.method,
        req.url.path,
        ip,
        request.model_dump_json(),
        crawler_protocol.crawler_data_req_controller
    )