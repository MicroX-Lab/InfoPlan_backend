# encoding: utf-8
"""
LLM 服务抽象层 - 通过 vLLM OpenAI 兼容 API 调用沐曦 GPU 上的模型

模型分配:
- Qwen3-8B (port 8000): 摘要生成、目标拆解 (heavy)
- Qwen3-4B (port 8001): 标签生成、笔记匹配 (light)
- Qwen3-VL-8B (port 8002): OCR 截图识别 (vision)
"""
from flask import current_app
from loguru import logger
from openai import OpenAI


class LLMService:
    """统一本地模型调用层"""

    def __init__(self):
        self._heavy_client = None
        self._light_client = None
        self._vision_client = None

    def _get_heavy_client(self) -> OpenAI:
        if self._heavy_client is None:
            base = current_app.config["MUXI_API_BASE"]
            port = current_app.config["LLM_HEAVY_PORT"]
            self._heavy_client = OpenAI(base_url=f"{base}:{port}/v1", api_key="dummy")
        return self._heavy_client

    def _get_light_client(self) -> OpenAI:
        if self._light_client is None:
            base = current_app.config["MUXI_API_BASE"]
            port = current_app.config["LLM_LIGHT_PORT"]
            self._light_client = OpenAI(base_url=f"{base}:{port}/v1", api_key="dummy")
        return self._light_client

    def _get_vision_client(self) -> OpenAI:
        if self._vision_client is None:
            base = current_app.config["MUXI_API_BASE"]
            port = current_app.config["LLM_VISION_PORT"]
            self._vision_client = OpenAI(base_url=f"{base}:{port}/v1", api_key="dummy")
        return self._vision_client

    def _call(self, client: OpenAI, model: str, messages: list, **kwargs) -> str | None:
        """统一调用封装"""
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败 [{model}]: {e}")
            return None

    def summarize_note(self, title: str, desc: str, tags: list[str] | None = None) -> str | None:
        """Qwen3-8B 生成笔记摘要"""
        tags_str = ", ".join(tags) if tags else ""
        prompt = (
            f"请用 2-3 句话总结以下小红书笔记的核心内容：\n\n"
            f"标题：{title}\n"
            f"内容：{desc}\n"
        )
        if tags_str:
            prompt += f"标签：{tags_str}\n"
        prompt += "\n请直接给出摘要，不要加任何前缀。"

        return self._call(
            self._get_heavy_client(),
            "Qwen3-8B",
            [{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.7,
        )

    def generate_tags(self, notes_info: list[dict]) -> list[str]:
        """Qwen3-4B 根据博主笔记自动生成分类标签"""
        notes_text = "\n".join(
            f"- {n.get('title', '')}：{n.get('desc', '')[:100]}" for n in notes_info[:10]
        )
        prompt = (
            f"根据以下小红书笔记列表，生成 3-5 个分类标签（用逗号分隔）：\n\n"
            f"{notes_text}\n\n"
            f"请只输出标签，用逗号分隔，不要加任何解释。"
        )
        result = self._call(
            self._get_light_client(),
            "Qwen3-4B",
            [{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5,
        )
        if result:
            return [t.strip() for t in result.split(",") if t.strip()]
        return []

    def decompose_goal(self, goal: str, user_notes_context: str = "") -> dict | None:
        """Qwen3-8B 目标拆解为计划步骤"""
        prompt = (
            f"你是一个学习规划助手。请将以下学习目标拆解为具体的学习步骤。\n\n"
            f"目标：{goal}\n\n"
        )
        if user_notes_context:
            prompt += f"用户已收藏的相关笔记：\n{user_notes_context}\n\n"
        prompt += (
            "请以 JSON 格式返回，包含 steps 数组，每个 step 有 title, description, time_estimate 字段。\n"
            '示例：{"steps": [{"title": "...", "description": "...", "time_estimate": "2天"}]}'
        )

        result = self._call(
            self._get_heavy_client(),
            "Qwen3-8B",
            [{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )
        if result:
            import json
            try:
                # 尝试从回复中提取 JSON
                start = result.find("{")
                end = result.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(result[start:end])
            except json.JSONDecodeError:
                logger.warning(f"解析目标拆解结果失败: {result[:200]}")
        return None

    def match_notes_to_steps(self, steps: list[dict], notes: list[dict]) -> dict:
        """Qwen3-4B 将笔记匹配到对应学习步骤"""
        steps_text = "\n".join(
            f"步骤{i+1}: {s.get('title', '')}" for i, s in enumerate(steps)
        )
        notes_text = "\n".join(
            f"笔记{i+1}[{n.get('note_id', '')}]: {n.get('title', '')} - {n.get('desc', '')[:80]}"
            for i, n in enumerate(notes[:30])
        )
        prompt = (
            f"请将以下笔记匹配到最相关的学习步骤。\n\n"
            f"学习步骤：\n{steps_text}\n\n"
            f"笔记列表：\n{notes_text}\n\n"
            f'请以 JSON 格式返回匹配结果：{{"matches": {{"步骤编号": ["笔记note_id", ...]}}}}'
        )

        result = self._call(
            self._get_light_client(),
            "Qwen3-4B",
            [{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        if result:
            import json
            try:
                start = result.find("{")
                end = result.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(result[start:end])
            except json.JSONDecodeError:
                logger.warning(f"解析笔记匹配结果失败: {result[:200]}")
        return {"matches": {}}

    def ocr_follow_list(self, image_base64: str) -> list[str]:
        """Qwen3-VL-8B 识别关注列表截图，返回博主昵称列表"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "这是一张小红书关注列表的截图。请识别出所有博主的昵称，"
                            "每行一个昵称，不要加任何序号或其他文字。"
                        ),
                    },
                ],
            }
        ]
        result = self._call(
            self._get_vision_client(),
            "Qwen3-VL-8B-Instruct",
            messages,
            max_tokens=512,
            temperature=0.1,
        )
        if result:
            return [line.strip() for line in result.strip().split("\n") if line.strip()]
        return []

    def check_health(self) -> dict:
        """检查各模型服务连通性"""
        status = {}
        for name, getter in [
            ("heavy_qwen3_8b", self._get_heavy_client),
            ("light_qwen3_4b", self._get_light_client),
            ("vision_qwen3_vl", self._get_vision_client),
        ]:
            try:
                client = getter()
                client.models.list()
                status[name] = "ok"
            except Exception as e:
                status[name] = f"error: {str(e)}"
        return status


# 全局单例
llm_service = LLMService()
