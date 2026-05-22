import hashlib
import secrets
import time
from typing import Dict

from loguru import logger
import requests
from app.config.settings import appConfig

class ShareSignatureUtil:

    @staticmethod
    def build_signature(app_key: str, nonce: str, time_stamp: int, app_secret: str) -> str:
        """
        加签demo 生成signature 工具
        
        Args:
            app_key: 唯一标识
            nonce: 随机字符串，随机生成-需要和接口请求中保持一致
            time_stamp: 当前毫秒级时间戳-例如 2023-08-15 20:31:31 对应时间戳 1692102691696-需要和接口请求中保持一致
            app_secret: 1、获取access_token第一次加签，使用密钥appSecret 2、分享秘钥生成第二次加签，使用access_token
            
        Returns:
            str: 签名
        """
        params = {
            "appKey": app_key,
            "nonce": nonce,
            "timeStamp": time_stamp
        }
        return ShareSignatureUtil.generate_signature(app_secret, params)

    @staticmethod
    def generate_signature(secret_key: str, params: Dict[str, str]) -> str:
        """
        构建签名
        
        Args:
            secret_key: 密钥
            params: 加签参数
            
        Returns:
            str: 签名
        """
        # Step 1: 按键排序参数
        sorted_params = dict(sorted(params.items()))
        
        # Step 2: 拼接排序后的参数
        params_string = "&".join([f"{key}={value}" for key, value in sorted_params.items()])
        
        # Step 3: 将密钥添加到参数字符串
        params_string += secret_key
        
        # Step 4: 使用SHA-256计算签名
        try:
            # 计算SHA-256哈希
            hash_object = hashlib.sha256(params_string.encode('utf-8'))
            # 转换为十六进制字符串
            signature = hash_object.hexdigest()
            return signature
        except Exception as e:
            raise RuntimeError("Failed to generate signature") from e
        
    @staticmethod
    def generate_access_token( nonce: str, time_stamp: int):
        """
            获取 access_token
            :param app_key: 第三方平台唯一标识，官方平台申请
            :param nonce: 32位以内随机数，需要保证和加签使用参数nonce一致
            :param timestamp: 时间戳单位ms，取当前系统时间，需要保证和加密timestamp一致
            :param signature: 签名，可直接复用【生成 sigature 工具】
            :param expires_in: 凭据有效截止时间戳，时间戳单位ms，不超过当前时间24小时
            返回用户指定位置的笔记
        """

        res_json = None
        try:
            signature = ShareSignatureUtil.build_signature(
                app_key=appConfig.XHS_APPKEY,
                nonce=nonce,
                time_stamp=time_stamp,
                app_secret=appConfig.XHS_APPSECRET
            )

            url = "https://edith.xiaohongshu.com/api/sns/v1/ext/access/token"

            payload = {
                "app_key": appConfig.XHS_APPKEY,
                "nonce": nonce,
                "timestamp": time_stamp,
                "signature": signature,
                "expires_in": time_stamp+(3600 * 100) # 有效期为1小时
            }
            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, json=payload)
            res_json = response.json()
            success, access_token = res_json["success"], res_json["data"]["access_token"]
        except Exception as e:
            success = False
            access_token = None
        return success, access_token, res_json
    
    @staticmethod
    def generate_verify_config():
        """
        参考文档：文档：https://agora.xiaohongshu.com/doc/js
        第一步 获取access_token，具体参照【获取 access_token】，第一次加签
        第二步 使用access_token生成js签名signature，第二次加签
        第三步 返回三方前端 appKey、nonce、timestamp、signature，唤起js sdk
        备注：签名生成可直接复用代码示例【生成sigature 工具】，签名生成为非可逆方式，需要保持加签使用的参数和验签参数一致
        
        Args:
            secret_key: 密钥
            params: 加签参数
            
        Returns:
            str: 签名
        """
        nonce = secrets.token_hex(16)
        time_stamp = int(time.time() * 1000)
        try:
            success, access_token, res_json = ShareSignatureUtil.generate_access_token(
                nonce=nonce,
                time_stamp=time_stamp
            )
            if success:
                signature = ShareSignatureUtil.build_signature(
                    app_key=appConfig.XHS_APPKEY,
                    nonce=nonce,
                    time_stamp=time_stamp,
                    app_secret=access_token
                )
                return {
                    "appKey": appConfig.XHS_APPKEY,
                    "nonce": nonce,
                    "timeStamp": time_stamp,
                    "signature": signature
                }
        except Exception as e:
            success = False
            msg = e
            logger.error(f"签名失败: {str(e)}", exc_info=True)

        return None

# if __name__ == '__main__':
#     verify_config = generate_verify_config()
#     print(verify_config)