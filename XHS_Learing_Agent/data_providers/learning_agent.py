from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import re
from typing import List, Dict, Optional
from loguru import logger
from config import Config
from model_service.interfaces import DataProvider, NoteInfo


class XHSLearningAgent:
    """小红书学习规划Agent（Jupyter友好版本）"""
    
    def __init__(self, model_name: str = None, data_provider: Optional[DataProvider] = None):
        """
        初始化学习Agent
        :param model_name: 模型路径，如果为None则使用配置文件中的路径
        :param data_provider: 数据提供者，如果为None则使用MockDataProvider
        """
        self.model_name = model_name or Config.MODEL_PATH
        logger.info(f"正在加载模型: {self.model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            logger.info("✅ 模型加载成功")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise
        
        # 数据提供者（可插拔）
        if data_provider is None:
            from data_providers import MockDataProvider
            self.data_provider = MockDataProvider()
            logger.info("📝 使用Mock数据提供者")
        else:
            self.data_provider = data_provider
            logger.info("📝 使用自定义数据提供者")
    
    def get_user_notes(self, user_ids: List[str], max_notes_per_user: int = None) -> List[NoteInfo]:
        """获取指定用户的笔记列表"""
        max_notes = max_notes_per_user or Config.MAX_NOTES_PER_USER
        return self.data_provider.get_user_notes(user_ids, max_notes)
    
    def decompose_goal(self, goal: str, user_notes: List[NoteInfo]) -> Dict:
        """将用户目标拆解成具体步骤（改进版）"""
        # 分析用户笔记的主题分布
        notes_summary = ""
        note_keywords = []
        
        if user_notes:
            notes_summary = "\n用户关注的相关笔记主题：\n"
            for note in user_notes[:10]:
                notes_summary += f"- {note.title}\n"
                # 提取关键词
                note_keywords.extend(note.tags)
                note_keywords.extend(note.title.split())
            
            # 去重
            note_keywords = list(set(note_keywords))
            notes_summary += f"\n相关关键词：{', '.join(note_keywords[:10])}"
        
        prompt = f"""你是一个学习规划助手。用户想要实现以下目标：

目标：{goal}
{notes_summary}

请将这个目标拆解成3-5个具体、可执行的步骤。要求：
1. 每个步骤应该具体明确，可以直接执行
2. 步骤之间要有逻辑顺序（从基础到进阶）
3. 步骤内容应该与目标高度相关（"{goal}"）
4. 如果提供了笔记主题，步骤应该尽量利用这些笔记资源
5. 步骤描述要简洁明了，每个步骤不超过30个字

输出格式为JSON：
{{
    "steps": [
        "步骤1的具体描述（与目标直接相关）",
        "步骤2的具体描述（与目标直接相关）",
        ...
    ]
}}

重要提示：
- 步骤必须围绕目标"{goal}"展开
- 不要偏离主题
- 只输出JSON，不要其他内容。"""
        
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=Config.MAX_NEW_TOKENS,
            temperature=Config.TEMPERATURE
        )
        
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        # 解析步骤
        steps = self._parse_steps_from_response(response, goal)
        
        # 匹配笔记到步骤（使用改进的匹配逻辑）
        matched_notes = self.match_notes_to_steps(steps, user_notes)
        
        return {
            "goal": goal,
            "steps": steps,
            "matched_notes": matched_notes
        }
    
    def _parse_steps_from_response(self, response: str, goal: str) -> List[str]:
        """从模型响应中解析步骤"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                steps = result.get('steps', [])
                if steps:
                    return steps
        except Exception as e:
            logger.warning(f"解析步骤失败: {e}")
        
        # 如果解析失败，尝试从文本中提取
        steps = re.findall(r'\d+[\.、]\s*(.+?)(?=\n|$)', response)
        if steps:
            return steps
        
        # 最后的降级方案
        logger.warning("使用默认步骤生成方案")
        return [
            f"了解{goal}的基础知识",
            f"学习{goal}的核心概念",
            f"实践{goal}的基本操作",
            f"深入掌握{goal}的高级应用"
        ]
    
    def match_notes_to_steps(self, steps: List[str], notes: List[NoteInfo]) -> Dict[str, List[NoteInfo]]:
        """将笔记匹配到各个步骤（改进版）"""
        if not notes:
            return {step: [] for step in steps}
        
        notes = notes[:Config.MAX_NOTES_FOR_MATCHING]
        
        # 先尝试使用模型匹配
        model_matched = self._match_by_model(steps, notes)
        
        # 如果模型匹配结果为空，使用关键词匹配作为后备
        if not any(model_matched.values()):
            logger.info("模型匹配结果为空，使用关键词匹配作为后备")
            return self._match_by_keywords(steps, notes)
        
        return model_matched
    
    def _match_by_keywords(self, steps: List[str], notes: List[NoteInfo]) -> Dict[str, List[NoteInfo]]:
        """使用关键词匹配笔记到步骤"""
        result = {step: [] for step in steps}
        
        # 提取步骤中的关键词
        def extract_keywords(text: str) -> List[str]:
            """提取关键词"""
            keywords = []
            # 提取中文关键词（2-4个字）
            chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            keywords.extend(chinese_words)
            
            # 提取英文关键词
            english_words = re.findall(r'\b[A-Za-z]{3,}\b', text)
            keywords.extend([w.lower() for w in english_words])
            
            return keywords
        
        for step in steps:
            step_keywords = extract_keywords(step)
            step_lower = step.lower()
            
            # 计算每个笔记的相关度分数
            note_scores = []
            for note in notes:
                score = 0
                note_text = f"{note.title} {note.desc} {' '.join(note.tags)}".lower()
                
                # 关键词匹配
                for keyword in step_keywords:
                    if keyword.lower() in note_text:
                        score += 2
                
                # 标题匹配（权重更高）
                for keyword in step_keywords:
                    if keyword.lower() in note.title.lower():
                        score += 3
                
                # 标签匹配
                for keyword in step_keywords:
                    if any(keyword.lower() in tag.lower() for tag in note.tags):
                        score += 2
                
                # 整体文本相似度
                if any(word in step_lower for word in note.title.lower().split()):
                    score += 1
                
                note_scores.append((score, note))
            
            # 按分数排序，选择前N个
            note_scores.sort(reverse=True, key=lambda x: x[0])
            matched = [note for score, note in note_scores[:Config.NOTES_PER_STEP] if score > 0]
            result[step] = matched
        
        return result
    
    def _match_by_model(self, steps: List[str], notes: List[NoteInfo]) -> Dict[str, List[NoteInfo]]:
        """使用模型匹配笔记到步骤"""
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        notes_text = "\n".join([
            f"{i}. {note.title}: {note.desc[:100]}"
            for i, note in enumerate(notes)
        ])
        
        prompt = f"""你是一个智能助手，需要将笔记匹配到对应的学习步骤。

学习步骤：
{steps_text}

可用笔记（格式：索引. 标题: 描述）：
{notes_text}

请为每个步骤推荐最相关的{Config.NOTES_PER_STEP}条笔记。输出格式为JSON：
{{
    "步骤1": [笔记索引列表],
    "步骤2": [笔记索引列表],
    ...
}}

注意：
1. 索引从0开始
2. 每个步骤推荐{Config.NOTES_PER_STEP}条笔记
3. 如果某个步骤没有相关笔记，可以返回空列表[]
4. 只输出JSON，不要其他内容。"""
        
        messages = [{"role": "user", "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512,
            temperature=0.3
        )
        
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        return self._parse_matching_result(response, steps, notes)
    
    def _parse_matching_result(self, response: str, steps: List[str], notes: List[NoteInfo]) -> Dict[str, List[NoteInfo]]:
        """解析笔记匹配结果"""
        result = {step: [] for step in steps}
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                match_result = json.loads(json_match.group())
                for step_idx, step in enumerate(steps, 1):
                    step_key = f"步骤{step_idx}"
                    if step_key in match_result:
                        note_indices = match_result[step_key]
                        if isinstance(note_indices, list):
                            result[step] = [
                                notes[i] for i in note_indices 
                                if isinstance(i, int) and 0 <= i < len(notes)
                            ]
        except Exception as e:
            logger.warning(f"解析匹配结果失败: {e}")
        
        return result
    
    def format_output(self, result: Dict) -> str:
        """格式化输出结果"""
        output = f"📚 学习目标：{result['goal']}\n\n"
        output += "=" * 50 + "\n\n"
        
        for idx, step in enumerate(result['steps'], 1):
            output += f"📌 步骤 {idx}：{step}\n\n"
            
            matched_notes = result['matched_notes'].get(step, [])
            if matched_notes:
                output += "   相关笔记推荐：\n"
                for note in matched_notes:
                    output += f"   • {note.title}\n"
                    if note.desc:
                        output += f"     简介：{note.desc[:100]}...\n"
                    output += f"     链接：https://www.xiaohongshu.com/explore/{note.note_id}\n"
                    output += "\n"
            else:
                output += "   （暂无相关笔记推荐）\n"
            
            output += "\n" + "-" * 50 + "\n\n"
        
        return output
    
    def process(self, goal: str, user_ids: List[str], debug: bool = False) -> str:
        """
        处理用户请求的主函数
        :param goal: 用户目标
        :param user_ids: 用户关注的user_id列表
        :param debug: 是否启用调试模式
        :return: 格式化的学习计划
        """
        logger.info(f"开始处理目标: {goal}")
        logger.info(f"关注用户数: {len(user_ids)}")
        
        # 获取用户笔记
        user_notes = self.get_user_notes(user_ids)
        logger.info(f"获取到 {len(user_notes)} 条笔记")
        
        if debug:
            print("\n" + "=" * 60)
            print("📝 调试信息：获取到的笔记")
            print("=" * 60)
            print(f"总共获取到 {len(user_notes)} 条笔记\n")
            
            # 显示前10条笔记
            for i, note in enumerate(user_notes[:10], 1):
                print(f"{i}. {note.title}")
                print(f"   标签: {', '.join(note.tags) if note.tags else '无'}")
                print(f"   描述: {note.desc[:80]}...")
                print()
            
            if len(user_notes) > 10:
                print(f"... 还有 {len(user_notes) - 10} 条笔记未显示\n")
        
        # 拆解目标
        if debug:
            print("=" * 60)
            print("🔍 正在拆解学习目标...")
            print("=" * 60)
        
        result = self.decompose_goal(goal, user_notes)
        
        if debug:
            print("\n" + "=" * 60)
            print("📋 生成的步骤及匹配情况")
            print("=" * 60)
            for i, step in enumerate(result['steps'], 1):
                print(f"\n步骤 {i}: {step}")
                matched = result['matched_notes'].get(step, [])
                print(f"  匹配到 {len(matched)} 条笔记")
                if matched:
                    for j, note in enumerate(matched, 1):
                        print(f"    {j}. {note.title}")
                        print(f"       标签: {', '.join(note.tags) if note.tags else '无'}")
                else:
                    print("    （无匹配笔记）")
            print("\n" + "=" * 60 + "\n")
        
        # 格式化输出
        return self.format_output(result)