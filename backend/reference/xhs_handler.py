# api/endpoints/users.py
import logging
import os
from pathlib import Path
import shutil
import tarfile
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.db.entity.standard_sensitive_word import StandardSensitiveWord
from app.models.image_handler.article_segment import ArticleSegmentModel, CompressRequest
from app.models.xhs_task.content_req import ContentReqModel
from app.services import sensitive_word_service
from app.utils.config_manager import ConfigManager
from app.utils.html_segment import HtmlSegment
from app.utils.playwright_screenshot import PlaywrightScreenshot
from app.config.settings import appConfig
from app.models.xhs_handler.xhs_note_request import XhsKeyworldSearchRequest, XhsLongTailWordUpdateRequest, XhsNoteDetailRequest
from app.utils.xhs_utils.data_util import handle_note_info
from app.utils.xhs_utils.xhs_apis import XHS_Apis
from app.utils.xhs_utils.share_signature_util import ShareSignatureUtil
from app.services.sensitive_word_service import SensitiveWordService

logger = logging.getLogger(__name__)

router = APIRouter()

config_manager = ConfigManager()

xhs_apis = XHS_Apis()

@router.post("/api/xhs/note_detail")
async def spider_note(request: XhsNoteDetailRequest):
        """
        爬取一个笔记的信息
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        cookies_str = request.cookies_str
        if cookies_str is None or cookies_str == "":
            cookies_str = appConfig.XHS_COOKIES
        try:
            success, msg, note_info = xhs_apis.get_note_info(request.note_url, cookies_str, request.proxies)
            if success and note_info is not None:
                note_info = note_info['data']['items'][0]
                note_info['url'] = request.note_url
                note_info = handle_note_info(note_info)
        except Exception as e:
            success = False
            msg = e
        logger.info(f'爬取笔记信息 {request.note_url}: {success}, msg: {msg}')
        return JSONResponse(content={
            "status": "success", 
            "data": note_info,
            "msg": msg
        })

@router.get("/api/xhs/share_verify_config")
async def share_verify_config():
     verify_config = ShareSignatureUtil.generate_verify_config()
     return JSONResponse(content={
            "status": "success", 
            "data": verify_config,
            "msg": ""
        })

@router.post("/api/xhs/sensitive_word/replace")
async def sensitive_word_replace(contentReq:ContentReqModel):
    sensitive_word_service = await SensitiveWordService.initialize()
    safe_content = sensitive_word_service.replace_sensitive_word(contentReq.sensitive_content)

    return JSONResponse(content={
        "status": "success", 
        "data": safe_content,
        "msg": ""
    })

@router.post("/api/xhs/keyword-search")
async def spider_note(request: XhsKeyworldSearchRequest):
        """
        获取搜索关键词的长尾词
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        cookies_str = request.cookies_str
        result = []
        if cookies_str is None or cookies_str == "":
            cookies_str = appConfig.XHS_COOKIES
        try:
            success, msg, res_json = xhs_apis.get_search_keyword(request.keyword, cookies_str, request.proxies)
            if success and res_json is not None:
                sug_items = res_json['data']['sug_items']
                for sug_item in sug_items:
                    result.append(sug_item['text'])
        except Exception as e:
            success = False
            msg = e
        logger.info(f'获取关键词的长尾词成功，关键词： {request.keyword}: {success}, msg: {msg}')
        return JSONResponse(content={
            "status": "success", 
            "data": result,
            "msg": msg
        })

@router.post("/api/xhs/long-tail-word")
async def spider_note(request: List[XhsLongTailWordUpdateRequest]):
        """
        获取搜索关键词的长尾词
        :param note_url:
        :param cookies_str:
        :return:
        """
        note_info = None
        cookies_str = request.cookies_str
        result = []
        if cookies_str is None or cookies_str == "":
            cookies_str = appConfig.XHS_COOKIES
        try:
            success, msg, res_json = xhs_apis.get_search_keyword(request.keyword, cookies_str, request.proxies)
            if success and res_json is not None:
                sug_items = res_json['data']['sug_items']
                for sug_item in sug_items:
                    result.append(sug_item['text'])
        except Exception as e:
            success = False
            msg = e
        logger.info(f'获取关键词的长尾词成功，关键词： {request.keyword}: {success}, msg: {msg}')
        return JSONResponse(content={
            "status": "success", 
            "data": result,
            "msg": msg
        })