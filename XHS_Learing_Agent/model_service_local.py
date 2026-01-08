# encoding: utf-8
"""
模型服务 - 本地数据测试版本
使用 MockDataProvider 进行本地测试，无需外部API依赖
"""
import sys
import os
from pathlib import Path

# ============================================
# 添加项目根目录到 Python 路径（重要！）
# ============================================
# 获取当前脚本所在目录
current_dir = Path(__file__).parent.absolute()
# 将项目根目录添加到 sys.path
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger

app = Flask(__name__)
CORS(app)

# ============================================
# 导入Agent（使用最可靠的方式）
# ============================================
try:
    from model_service import XHSLearningAgent
except ImportError:
    # 如果包导入失败，尝试直接导入
    try:
        from model_service.learning_agent import XHSLearningAgent
    except ImportError as e:
        logger.error(f"无法导入 XHSLearningAgent: {e}")
        raise

# 导入数据提供者
try:
    from data_providers import MockDataProvider
except ImportError:
    try:
        from data_providers.mock_provider import MockDataProvider
    except ImportError as e:
        logger.error(f"无法导入 MockDataProvider: {e}")
        raise

# 验证导入成功
logger.info("✅ 所有导入成功！")

# ============================================
# 配置部分
# ============================================

# 模型路径（根据实际情况修改）
MODEL_PATH = "/mnt/moark-models/Qwen3-8B"  # 或使用默认路径

# 服务端口
MODEL_SERVICE_PORT = 5002

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO")

# 初始化学习Agent（延迟加载）
_learning_agent = None


def get_learning_agent():
    """获取学习Agent实例（单例模式）"""
    global _learning_agent
    if _learning_agent is None:
        logger.info("正在初始化Agent...")
        
        try:
            # 使用Mock数据提供者（本地测试）
            data_provider = MockDataProvider()
            
            # 初始化Agent（如果支持无参数初始化，否则传入模型路径）
            try:
                # 尝试无参数初始化
                _learning_agent = XHSLearningAgent()
            except TypeError:
                # 如果需要模型路径参数
                _learning_agent = XHSLearningAgent(model_name=MODEL_PATH)
            
            # 如果支持设置数据提供者
            if hasattr(_learning_agent, 'set_data_provider'):
                _learning_agent.set_data_provider(data_provider)
            elif hasattr(_learning_agent, 'data_provider'):
                _learning_agent.data_provider = data_provider
            
            logger.info("✅ Agent初始化完成！")
            logger.info(f"📦 使用 MockDataProvider（本地测试模式）")
            
        except Exception as e:
            logger.error(f"❌ Agent初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    return _learning_agent


@app.route('/api/learning/plan', methods=['POST'])
def generate_learning_plan():
    """
    生成学习规划接口
    请求参数（JSON）:
    {
        "goal": "我想学习ai agent的简单开发",
        "user_ids": ["user_id1", "user_id2", ...],
        "max_users": 5,  # 可选，最多处理几个用户，默认5
        "notes_per_user": 5,  # 可选，每个用户获取几条笔记，默认5
        "debug": false  # 可选，是否返回调试信息
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "msg": "请求体不能为空",
                "data": None
            }), 400
        
        goal = data.get('goal')
        if not goal:
            return jsonify({
                "success": False,
                "msg": "goal 参数不能为空",
                "data": None
            }), 400
        
        user_ids = data.get('user_ids', [])
        if not user_ids:
            return jsonify({
                "success": False,
                "msg": "user_ids 参数不能为空",
                "data": None
            }), 400
        
        max_users = data.get('max_users', 5)
        notes_per_user = data.get('notes_per_user', 5)
        debug = data.get('debug', False)
        
        logger.info(f'收到学习规划请求: goal={goal}, user_ids={len(user_ids)}个用户')
        
        # 限制用户数量
        user_ids = user_ids[:max_users]
        
        # 获取学习Agent
        agent = get_learning_agent()
        
        # 处理请求
        result_text = agent.process(goal, user_ids, debug=debug)
        
        # 获取详细结果（用于JSON返回）
        user_notes = agent.get_user_notes(user_ids, max_notes_per_user=notes_per_user)
        
        # 重新生成结果以获取结构化数据
        result_dict = agent.decompose_goal(goal, user_notes)
        
        # 构建响应
        response_data = {
            "goal": result_dict['goal'],
            "steps": [
                {
                    "step_number": idx + 1,
                    "description": step,
                    "recommended_notes": [
                        {
                            "note_id": note.note_id,
                            "title": note.title,
                            "desc": note.desc[:200] if hasattr(note, 'desc') else "",
                            "tags": note.tags if hasattr(note, 'tags') else [],
                            "liked_count": note.liked_count if hasattr(note, 'liked_count') else 0,
                            "url": f"https://www.xiaohongshu.com/explore/{note.note_id}"
                        }
                        for note in result_dict['matched_notes'].get(step, [])
                    ]
                }
                for idx, step in enumerate(result_dict['steps'])
            ],
            "formatted_output": result_text,
            "statistics": {
                "total_users": len(user_ids),
                "total_notes": len(user_notes),
                "total_steps": len(result_dict['steps']),
                "notes_with_recommendations": sum(
                    1 for step in result_dict['steps']
                    if result_dict['matched_notes'].get(step)
                )
            }
        }
        
        if debug:
            response_data['debug_info'] = {
                "data_provider": "MockDataProvider",
                "user_notes_preview": [
                    {
                        "title": note.title if hasattr(note, 'title') else str(note),
                        "tags": note.tags if hasattr(note, 'tags') else [],
                        "user_id": note.user_id if hasattr(note, 'user_id') else ""
                    }
                    for note in user_notes[:10]
                ]
            }
        
        return jsonify({
            "success": True,
            "msg": "学习规划生成成功",
            "data": response_data
        }), 200
        
    except Exception as e:
        logger.error(f'生成学习规划接口错误: {str(e)}', exc_info=True)
        return jsonify({
            "success": False,
            "msg": f"服务器错误: {str(e)}",
            "data": None
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查Agent是否已初始化
        agent = get_learning_agent()
        
        return jsonify({
            "status": "ok",
            "service": "Model Agent Service (Local Test)",
            "data_provider": "MockDataProvider",
            "model_path": MODEL_PATH,
            "message": "模型服务运行正常（本地测试模式）"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"服务异常: {str(e)}"
        }), 500


# ============================================
# Jupyter中使用方式
# ============================================

def start_service_in_jupyter(host='0.0.0.0', port=5002):
    """
    在Jupyter中启动服务（非阻塞方式）
    使用 threading 在后台运行
    """
    import threading
    
    def run_server():
        logger.info('=' * 60)
        logger.info('启动模型服务API服务器（本地测试版本）')
        logger.info('=' * 60)
        logger.info(f'数据提供者: MockDataProvider')
        logger.info(f'模型路径: {MODEL_PATH}')
        logger.info('学习规划接口: POST /api/learning/plan')
        logger.info('健康检查接口: GET /health')
        logger.info('=' * 60)
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info(f'✅ 服务已在后台启动: http://{host}:{port}')
    return thread


if __name__ == '__main__':
    # 如果直接运行（非Jupyter），使用标准方式启动
    logger.info('=' * 60)
    logger.info('启动模型服务API服务器（本地测试版本）')
    logger.info('=' * 60)
    logger.info(f'数据提供者: MockDataProvider')
    logger.info(f'模型路径: {MODEL_PATH}')
    logger.info('学习规划接口: POST /api/learning/plan')
    logger.info('健康检查接口: GET /health')
    logger.info('=' * 60)
    
    # 预先初始化Agent以验证导入
    try:
        logger.info("\n正在初始化Agent...")
        agent = get_learning_agent()
        logger.info("✅ Agent初始化完成！")
    except Exception as e:
        logger.error(f"❌ Agent初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    app.run(host='0.0.0.0', port=MODEL_SERVICE_PORT, debug=True)