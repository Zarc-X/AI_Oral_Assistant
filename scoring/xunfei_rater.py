"""
讯飞星火语音评测模块
实现与讯飞开放平台ISE接口的WebSocket通信
"""
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import logging
import threading
from typing import Dict, Optional
from .config import XUNFEI_CONFIG

# 尝试导入 _thread，用于兼容 WebSocketApp 的 run_forever 调用
try:
    import _thread as thread
except ImportError:
    import _thread as thread

logger = logging.getLogger(__name__)

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

class XunfeiRater:
    """讯飞语音评测器"""

    def __init__(self):
        self.appid = XUNFEI_CONFIG["APPID"]
        self.api_secret = XUNFEI_CONFIG["APISecret"]
        self.api_key = XUNFEI_CONFIG["APIKey"]
        self.host_url = XUNFEI_CONFIG["HostUrl"]
        self.result = None
        self.error_msg = None
        
    def create_url(self):
        """生成鉴权url"""
        url = self.host_url
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + "ise-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/open-ise" + " HTTP/1.1"
        
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"hmac-sha256\", headers=\"host date request-line\", signature=\"%s\"" % (
            self.api_key, signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "ise-api.xfyun.cn"
        }
        url = url + '?' + urlencode(v)
        return url

    def score(self, audio_path: str, text: str) -> Optional[Dict]:
        """
        调用讯飞接口进行评分
        
        Args:
            audio_path: 音频文件路径
            text: 评测文本
            
        Returns:
            评分结果字典 (解析后的JSON)
        """
        self.result = None
        self.error_msg = None
        self.audio_path = audio_path
        self.text = text
        
        websocket.enableTrace(False)
        wsUrl = self.create_url()
        ws = websocket.WebSocketApp(wsUrl, 
                                    on_message=self.on_message, 
                                    on_error=self.on_error, 
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        
        # 阻塞直到完成
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        
        if self.error_msg:
            logger.error(f"讯飞评分出错: {self.error_msg}")
            return None
            
        return self.result

    def on_message(self, ws, message):
        try:
            code = json.loads(message)["code"]
            sid = json.loads(message)["sid"]
            if code != 0:
                self.error_msg = json.loads(message)["message"]
                logger.error(f"Xunfei Error: {self.error_msg} Code: {code}")
                ws.close()
                return

            data = json.loads(message)["data"]
            status = data["status"]
            
            if status == 2:
                # 最终结果
                xml_result = base64.b64decode(data["data"]).decode("utf8")
                
                # 记录原始XML以便调试
                logger.info(f"讯飞评分原始XML: {xml_result}")

                # 这里简单处理，实际可能需要解析XML提取分数
                # 为了简化，我们假设返回的是我们处理好的字典或者后续需要解析XML
                # 为了简化，我们假设返回的是我们处理好的字典或者后续需要解析XML
                # 讯飞返回默认是XML，如果需要JSON需要在business参数中设置cmd='json' (部分旧接口不支持)
                # ISE v2 如果ent=en_vip返回通常包含read_sentence结构的XML
                
                # 这里我们暂且保存原始XML，实际使用需要用xml.etree.ElementTree解析
                self.result = {"raw_xml": xml_result}
                
                # 尝试做简单的解析提取总分
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(xml_result)
                    
                    # 1. 优先检查是否被拒绝 (is_rejected="true")
                    # 常见的节点如 <rec_paper> 或 <read_chapter> 都可能带有此属性
                    is_rejected = False
                    for node in root.iter():
                        if node.attrib.get('is_rejected') == 'true':
                            is_rejected = True
                            reject_type = node.attrib.get('reject_type', 'unknown')
                            except_info = node.attrib.get('except_info', 'unknown')
                            logger.error(f"【严重错误】讯飞评分被拒绝! Reject Type: {reject_type}, Except Info: {except_info}")
                            if str(except_info) == "28673":
                                logger.error("错误码 28673 说明：检测到静音或纯噪音，未检测到有效语音。请检查麦克风是否正常工作！")
                            elif str(except_info) == "28676":
                                logger.error("错误码 28676 说明：语音与文本/题目不匹配或匹配度过低。原因可能是：1. 录音不清晰/噪音过大 2. 声音太小导致只识别到只言片语 3. 说的是中文而非英文")
                            self.error_msg = f"Audio Rejected: No valid speech detected (Error {except_info})"
                            # 即使被拒绝，后续可能还是会提取到 0 分，但至少日志里有了明确警告
                            break
                            
                    # 2. 查找包含 total_score 属性的节点 (read_chapter 或 read_sentence)
                    score_node = None
                    for node in root.iter():
                        if 'total_score' in node.attrib:
                            score_node = node
                            break

                    if score_node is not None:
                        # 讯飞是5分制，我们需要转换成0-4分或保留
                        score_val = float(score_node.attrib.get('total_score', 0))
                        self.result['total_score'] = score_val
                        # 转换到0-4分制 (5分 -> 4分)
                        self.result['converted_score'] = (score_val / 5.0) * 4.0
                        
                        # 提取更多细节 (如果存在)
                        for attr in ['accuracy_score', 'fluency_score', 'integrity_score', 'standard_score']:
                            if attr in score_node.attrib:
                                self.result[attr] = float(score_node.attrib[attr])
                except Exception as e:
                    logger.warning(f"XML解析失败: {e}")
                
                ws.close()

        except Exception as e:
            logger.error(f"接收消息处理异常: {e}")
            self.error_msg = str(e)
            ws.close()

    def on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")
        self.error_msg = str(error)

    def on_close(self, ws, *args):
        logger.info("WebSocket Closed")

    def on_open(self, ws):
        def run(*args):
            frameSize = 1280  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            
            status = STATUS_FIRST_FRAME
            
            with open(self.audio_path, "rb") as fp:
                # 如果是 WAV 文件，跳过 44 字节的文件头
                if self.audio_path.endswith('.wav'):
                    try:
                        header = fp.read(44)
                        logger.info("已跳过 WAV 文件头 (44 bytes)")
                    except Exception as e:
                        logger.warning(f"跳过文件头失败: {e}")
                        fp.seek(0)
                
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    
                    # 第一帧处理
                    if status == STATUS_FIRST_FRAME:
                        # 如果是topic模式，需要处理文本格式
                        text_payload = self.text
                        if XUNFEI_CONFIG["Category"] == "topic":
                            # 确保文本符合[topic] 1. xxx 格式
                            if not text_payload.strip().startswith("[topic]"):
                                # 假设传入的是题目本身，自动添加前缀
                                # 移除可能存在的 "1. " 前缀以避免重复
                                clean_title = text_payload.strip()
                                if clean_title.startswith("1."):
                                    clean_title = clean_title[2:].strip()
                                text_payload = f"[topic]\n1. {clean_title}"
                        elif XUNFEI_CONFIG["Category"] == "read_chapter":
                            # 关键修改：如果是read_chapter模式用于模拟自由说
                            # 我们需要在文本前自动加上ASR识别出的内容(或者至少不强制它必须是题目)
                            # 但目前 self.text 仅仅是题目。
                            # 临时方案：如果发现文本很短（像题目），我们假设用户说了很多
                            # 注意：真正的解决方案需要先ASR转文字，然后把转出来的文字作为标准答案给讯飞
                            pass

                        logger.info(f"发送给讯飞的评测文本({XUNFEI_CONFIG['Category']}): {text_payload}")

                        d = {
                            "common": {"app_id": self.appid},
                            "business": {
                                "category": XUNFEI_CONFIG["Category"],
                                "sub": XUNFEI_CONFIG["Sub"],
                                "ent": XUNFEI_CONFIG["Ent"],
                                "cmd": "ssb",
                                "auf": "audio/L16;rate=16000",
                                "aue": "raw",
                                "text": text_payload,
                                "ttp_skip": True,
                                "aus": 1,
                            },
                            "data": {
                                "status": 0,
                                "data": str(base64.b64encode(buf), 'utf-8'),
                            }
                        }
                        d = json.dumps(d)
                        ws.send(d)
                        status = STATUS_CONTINUE_FRAME
                        
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {
                            "business": {
                                "cmd": "auw",
                                "aus": 2,
                            },
                            "data": {
                                "status": 1,
                                "data": str(base64.b64encode(buf), 'utf-8'),
                            }
                        }
                        ws.send(json.dumps(d))
                        
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {
                            "business": {
                                "cmd": "auw",
                                "aus": 4,
                            },
                            "data": {
                                "status": 2,
                                "data": str(base64.b64encode(buf), 'utf-8'),
                            }
                        }
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        break
                        
                    time.sleep(intervel)
                    
            logger.info("音频发送完毕")
            
        thread.start_new_thread(run, ())
