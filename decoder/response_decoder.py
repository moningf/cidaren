"""响应解码器 — 根据 jv 字段自动分发解密策略.

对应 JS respVerify (app.js:4436):
  jv="1"  → 截断前32字符 + Base64
  jv="2_*" → 噪音剥除 + Base64
  jv="3_*" → 噪音剥除 + 分块重排 + Base64
"""
import json
from typing import Any, Dict

from decoder.ds_base64 import ds_decode
from decoder.noise_configs import (
    V2_NOISE_CONFIGS,
    V3_BLOCK_CONFIGS,
    remove_noise_chars,
    reorder_blocks,
)
from web.logging import app_log as decoder_log

_CALL_COUNT = 0


def _preview(s: str, n: int = 80) -> str:
    """截取字符串预览."""
    return (s[:n] + "...") if len(s) > n else s


def _decode_result_keys(result: Any) -> str:
    """提取解码结果的顶层 keys 摘要."""
    if isinstance(result, dict):
        keys = list(result.keys())[:12]
        return f"dict keys={keys}"
    if isinstance(result, list):
        return f"list len={len(result)}, first_type={type(result[0]).__name__ if result else 'empty'}"
    return f"{type(result).__name__}: {_preview(str(result), 60)}"


def _v1_decrypt(data: str) -> Any:
    """jv=1: 截断前 32 字符 + Base64 解码 + JSON 解析."""
    truncated = data[32:]
    decoded = ds_decode(truncated)
    decoder_log("v1", f"input={len(data)}chars, truncated={len(truncated)}chars, decoded={len(decoded)}chars")
    return json.loads(decoded)


def _v2_decrypt(data: str, jv: str) -> Any:
    """jv=2_XXXX: 噪音剥除 + Base64 解码 + JSON 解析."""
    config = V2_NOISE_CONFIGS[jv]
    decoder_log("v2", f"jv={jv} input={len(data)}chars, noise_rules={config}")
    cleaned = remove_noise_chars(data, config)
    decoder_log("v2", f"  noise_removed={len(data) - len(cleaned)}chars, cleaned_preview={_preview(cleaned, 50)}")
    decoded = ds_decode(cleaned)
    decoder_log("v2", f"  decoded={len(decoded)}chars")
    result = json.loads(decoded)
    decoder_log("v2", f"  result {_decode_result_keys(result)}")
    return result


def _v3_decrypt(data: str, jv: str) -> Any:
    """jv=3_XXXX: 噪音剥除 + 分块重排 + Base64 解码 + JSON 解析."""
    config = V3_BLOCK_CONFIGS[jv]
    decoder_log("v3", f"jv={jv} input={len(data)}chars, noise_rules={config['updateChars']}, average={config['average']}, locations={config['locations']}")
    cleaned = remove_noise_chars(data, config["updateChars"])
    decoder_log("v3", f"  noise_removed={len(data) - len(cleaned)}chars, cleaned_len={len(cleaned)}")
    reordered = reorder_blocks(cleaned, config)
    decoder_log("v3", f"  reordered_len={len(reordered)}, preview={_preview(reordered, 50)}")
    decoded = ds_decode(reordered)
    decoder_log("v3", f"  decoded={len(decoded)}chars")
    result = json.loads(decoded)
    decoder_log("v3", f"  result {_decode_result_keys(result)}")
    return result


class ResponseDecoder:
    """HTTP 响应解码器，自动识别 jv 并分发解密."""

    @staticmethod
    def _log(tag: str, msg: str) -> None:
        """写入统一日志文件."""
        decoder_log(tag, msg)

    def decode(self, response_text: str) -> Dict[str, Any]:
        """解码 HTTP 响应文本，自动处理 jv 层."""
        global _CALL_COUNT
        _CALL_COUNT += 1
        call_id = _CALL_COUNT

        # 先尝试直接解析 JSON
        try:
            resp = json.loads(response_text)
        except json.JSONDecodeError:
            # 不是 JSON，尝试 DS Base64 解码
            self._log("RAW", f"#{call_id} 非 JSON 响应, len={len(response_text)}, preview={_preview(response_text, 80)}")
            try:
                decoded = ds_decode(response_text)
                result = json.loads(decoded)
                self._log("RAW", f"#{call_id} DS decode OK, {_decode_result_keys(result)}")
                return result
            except Exception as exc:
                self._log("ERR", f"#{call_id} DS decode 失败: {exc}, raw_body={_preview(response_text, 200)}")
                raise

        jv = resp.get("jv")
        data = resp.get("data")
        jv_type = f"jv={jv}" if jv else "plain"

        self._log("DEC", f"#{call_id} 解密类型={jv_type}, data_type={type(data).__name__}, "
                    f"resp_keys={list(resp.keys())[:10]}, code={resp.get('code')}")

        if jv and isinstance(data, str):
            try:
                decrypted = self._decode_jv_data(jv, data)
                resp["data"] = decrypted
                self._log("DEC", f"#{call_id} 解密成功, {_decode_result_keys(decrypted)}")
            except Exception as exc:
                self._log("ERR", f"#{call_id} 解密失败 jv={jv}: {exc}, data_head={_preview(data, 120)}, raw_body={_preview(response_text, 300)}")
                raise
        else:
            self._log("DEC", f"#{call_id} 无需解密 (jv={jv}, is_str={isinstance(data, str)})")

        return resp

    def _decode_jv_data(self, jv: str, data: str) -> Any:
        """根据 jv 值分发解密 data 字段."""
        jv_str = str(jv)
        self._log("DEC", f"分发解密 jv={jv_str}, data_len={len(data)}, preview={_preview(data, 60)}")

        if jv_str == "1":
            return _v1_decrypt(data)

        if jv_str.startswith("2_"):
            if jv_str not in V2_NOISE_CONFIGS:
                self._log("ERR", f"未知 v2 配置 jv={jv_str}, 已知={list(V2_NOISE_CONFIGS.keys())}, data_preview={_preview(data, 100)}")
                raise ValueError(f"未知的 v2 配置: {jv_str}")
            return _v2_decrypt(data, jv_str)

        if jv_str.startswith("3_"):
            if jv_str not in V3_BLOCK_CONFIGS:
                self._log("ERR", f"未知 v3 配置 jv={jv_str}, 已知={list(V3_BLOCK_CONFIGS.keys())}, data_preview={_preview(data, 100)}")
                raise ValueError(f"未知的 v3 配置: {jv_str}")
            return _v3_decrypt(data, jv_str)

        # 未知 jv，尝试直接 DS Base64 解码
        self._log("FALLBACK", f"未知 jv={jv_str}, 尝试直接 DS Base64 解码, data_preview={_preview(data, 60)}")
        return json.loads(ds_decode(data))
