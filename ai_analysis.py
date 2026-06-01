"""LeetCode AI 分析模块 - 使用 OpenAI 兼容 API"""
import os
import json
import requests

# 从环境变量读取 API 配置
API_KEY = os.environ.get('LLM_API_KEY', '')
API_BASE = os.environ.get('LLM_API_BASE', 'https://token-plan-sgp.xiaomimimo.com/v1')
MODEL = os.environ.get('LLM_MODEL', 'mimo-v2.5-pro')


def analyze_problem(problem_title, problem_title_cn, difficulty, category, template_code=None, user_code=None):
    """AI 分析题目：解题思路、复杂度、代码审查"""
    if not API_KEY:
        return {'error': '未配置 LLM API Key，请设置环境变量 LLM_API_KEY'}

    prompt = f"""你是一位资深算法面试官和 LeetCode 导师。请分析以下算法题目：

**题目：** {problem_title_cn}（{problem_title}）
**难度：** {difficulty}
**算法分类：** {category}
"""

    if template_code:
        prompt += f"\n**参考模板代码：**\n```python\n{template_code}\n```\n"

    if user_code:
        prompt += f"\n**用户提交的代码：**\n```python\n{user_code}\n```\n"
        prompt += """
请按以下格式输出分析：

## 🔍 题目解析
简要说明题目要求和关键约束。

## 💡 解题思路
1. 核心思路是什么？用一句话概括
2. 为什么选择这个算法/数据结构？
3. 关键步骤分解

## ⏱️ 复杂度分析
- 时间复杂度：O(?) 并解释原因
- 空间复杂度：O(?) 并解释原因

## 🔧 代码审查
对用户代码进行审查：
- 有没有 bug 或边界情况遗漏？
- 有没有可以优化的地方？
- 代码风格建议

## 📝 同类题推荐
推荐 2-3 道类似题目来巩固这个知识点。
"""
    else:
        prompt += """
请按以下格式输出分析：

## 🔍 题目解析
简要说明题目要求和关键约束。

## 💡 解题思路
1. 核心思路是什么？用一句话概括
2. 为什么选择这个算法/数据结构？
3. 关键步骤分解
4. 常见陷阱和边界情况

## ⏱️ 复杂度分析
- 时间复杂度：O(?) 并解释原因
- 空间复杂度：O(?) 并解释原因

## 📝 面试技巧
面试中如何跟面试官沟通这道题？

## 📝 同类题推荐
推荐 2-3 道类似题目来巩固这个知识点。
"""

    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.7
            },
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        content = data['choices'][0]['message']['content']
        return {'success': True, 'analysis': content}
    except requests.exceptions.Timeout:
        return {'error': 'AI 分析超时，请稍后重试'}
    except requests.exceptions.RequestException as e:
        return {'error': f'API 请求失败: {str(e)}'}
    except (KeyError, IndexError) as e:
        return {'error': f'API 响应解析失败: {str(e)}'}


def generate_weekly_report(stats_data):
    """生成每周刷题报告（纯文本，适配飞书）"""
    if not API_KEY:
        return _fallback_weekly_report(stats_data)

    prompt = f"""你是一位 LeetCode 刷题教练。请根据以下本周数据生成一份简洁的中文周报。

要求：
- 不要使用任何 markdown 语法（不要 #、**、- 等符号）
- 用纯文本格式，用换行分隔段落
- 可以用 emoji 增加表现力
- 控制在 300 字以内
- 语气亲切但专业

数据：
- 本周完成：{stats_data['week_done']} 道
- 累计完成：{stats_data['total_done']}/{stats_data['total_problems']}（{stats_data['progress_percent']}%）
- 连续天数：{stats_data['streak']} 天
- 本周题目：{', '.join(f"[{p['difficulty']}] {p['title_cn']}" for p in stats_data['week_problems']) or '无'}
- 薄弱分类：{', '.join(stats_data['weak_categories']) or '无'}

请生成周报："""
    try:
        resp = requests.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.8
            },
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']
    except Exception:
        return _fallback_weekly_report(stats_data)


def _fallback_weekly_report(stats_data):
    """无 API 时的兜底报告（纯文本）"""
    lines = [
        f"📊 LeetCode 周报",
        f"",
        f"本周完成 {stats_data['week_done']} 道题",
        f"累计进度: {stats_data['total_done']}/{stats_data['total_problems']}（{stats_data['progress_percent']}%）",
        f"连续刷题: {stats_data['streak']} 天",
    ]
    if stats_data['week_problems']:
        lines.append("")
        lines.append("本周题目:")
        for p in stats_data['week_problems']:
            lines.append(f"  ✅ [{p['difficulty']}] {p['title_cn']}（{p['category']}）")
    if stats_data['weak_categories']:
        lines.append(f"\n⚠️ 薄弱方向: {', '.join(stats_data['weak_categories'])}")
    lines.append(f"\n💪 继续保持，坚持就是胜利！")
    return '\n'.join(lines)
