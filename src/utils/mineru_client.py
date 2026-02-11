import requests
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinueruClient:
    """Minueru 文件解析客户端

    用于与 Minueru 文件解析服务进行交互，支持 PDF 文件解析。
    """

    DEFAULT_BASE_URL = "http://localhost:8008/file_parse"
    DEFAULT_PARAMS = {
        'return_middle_json': 'false',
        'return_model_output': 'false',
        'return_md': 'true',
        'return_images': 'true',
        'end_page_id': '99999',
        'parse_method': 'auto',
        'start_page_id': '0',
        'lang_list': 'en',
        'output_dir': './output',
        'server_url': 'string',
        'return_content_list': 'false',
        'backend': 'pipeline',
        'table_enable': 'true',
        'response_format_zip': 'false',
        'formula_enable': 'true'
    }

    def __init__(self, base_url: Optional[str] = None, timeout: int = 60*6) -> None:
        """初始化 Minueru 客户端

        Args:
            base_url: Minueru 服务的基础 URL，如果为 None 则使用默认值
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        self.headers = {'accept': 'application/json'}

    def _prepare_files(self, local_files: List[Union[str, Path]]) -> List[tuple]:
        """准备要上传的文件

        Args:
            local_files: 本地文件路径列表

        Returns:
            准备好的文件元组列表

        Raises:
            FileNotFoundError: 如果文件不存在
            ValueError: 如果文件列表为空
        """
        if not local_files:
            raise ValueError("文件列表不能为空")

        files = []
        for file_path in local_files:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            if not file_path.is_file():
                raise ValueError(f"不是有效的文件: {file_path}")

            # 自动检测 MIME 类型
            mime_type = self._detect_mime_type(file_path)
            files.append(
                ('files', (file_path.name, open(file_path, 'rb'), mime_type))
            )

        return files

    def _detect_mime_type(self, file_path: Path) -> str:
        """根据文件扩展名检测 MIME 类型

        Args:
            file_path: 文件路径

        Returns:
            MIME 类型字符串
        """
        suffix = file_path.suffix.lower()
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.html': 'text/html',
            '.htm': 'text/html',
        }
        return mime_map.get(suffix, 'application/octet-stream')

    def _close_files(self, files: List[tuple]) -> None:
        """关闭所有打开的文件

        Args:
            files: 文件元组列表
        """
        for file_tuple in files:
            try:
                # 文件结构: ('files', (filename, file_obj, mime_type))
                file_obj = file_tuple[1][1]
                if not file_obj.closed:
                    file_obj.close()
            except Exception as e:
                logger.warning(f"关闭文件时出错: {e}")

    def parse(self, local_files: List[Union[str, Path]]) -> Optional[Dict[str, Any]]:
        """解析文件

        Args:
            local_files: 要解析的本地文件路径列表

        Returns:
            解析结果字典，如果失败则返回 None
        """
        files = []
        try:
            # 准备文件
            files = self._prepare_files(local_files)

            # 发送请求
            logger.info(f"正在解析 {len(files)} 个文件...")
            response = requests.post(
                self.base_url,
                files=files,
                data=self.DEFAULT_PARAMS,
                headers=self.headers,
                timeout=self.timeout
            )

            logger.info(f"状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info("文件解析成功")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失败: {e}")
                    logger.debug(f"原始响应: {response.text[:500]}...")
                    return None
            else:
                logger.error(f"请求失败: {response.status_code}")
                logger.error(f"错误信息: {response.text[:500]}...")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"请求超时 (timeout={self.timeout}s)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"连接失败，请检查服务是否运行在: {self.base_url}")
            return None
        except FileNotFoundError as e:
            logger.error(f"文件错误: {e}")
            return None
        except Exception as e:
            logger.error(f"发生异常: {e}", exc_info=True)
            return None
        finally:
            # 确保关闭所有文件
            self._close_files(files)

    def parse_single(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """解析单个文件（便捷方法）

        Args:
            file_path: 单个文件路径

        Returns:
            解析结果字典，如果失败则返回 None
        """
        return self.parse([file_path])

    def test_connection(self) -> bool:
        """测试与服务的连接

        Returns:
            连接是否成功
        """
        try:
            response = requests.get(self.base_url.replace('/file_parse', ''), timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"连接测试失败: {e}")
            return False
