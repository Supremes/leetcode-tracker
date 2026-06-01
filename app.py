"""LeetCode 进度追踪器 - Flask 应用 v2"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from database import (
    get_db, init_db, seed_problems,
    get_streak, get_heatmap_data, get_category_mastery,
    get_recommendations, get_progress_prediction
)
from ai_analysis import analyze_problem, generate_weekly_report
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

AUTH_USER='admin'
AUTH_PASS='leetcode2026'

def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASS

def authenticate():
    return Response('需要登录', 401, {'WWW-Authenticate': 'Basic realm="LeetCode Tracker"'})

@app.before_request
def before_request():
    if request.path.startswith('/static/') or request.path.startswith('/api/'):
        return
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()


@app.route('/')
def index():
    db = get_db()
    stats = {}
    row = db.execute('''
        SELECT COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done,
            SUM(CASE WHEN p.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN p.status = 'review' THEN 1 ELSE 0 END) as review
        FROM progress p
    ''').fetchone()
    stats['total'] = row['total']
    stats['done'] = row['done'] or 0
    stats['in_progress'] = row['in_progress'] or 0
    stats['review'] = row['review'] or 0
    stats['todo'] = stats['total'] - stats['done'] - stats['in_progress'] - stats['review']
    stats['progress_percent'] = round(stats['done'] / stats['total'] * 100 if stats['total'] > 0 else 0)

    difficulty_stats = db.execute('''
        SELECT pr.difficulty, COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
        GROUP BY pr.difficulty
    ''').fetchall()
    stats['by_difficulty'] = {r['difficulty']: {'total': r['total'], 'done': r['done'] or 0} for r in difficulty_stats}

    priority_stats = db.execute('''
        SELECT pr.priority, COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
        GROUP BY pr.priority
    ''').fetchall()
    stats['by_priority'] = {r['priority']: {'total': r['total'], 'done': r['done'] or 0} for r in priority_stats}

    stats['streak'] = get_streak()
    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_done = db.execute("SELECT COUNT(*) as count FROM progress WHERE status = 'done' AND updated_at >= ?", (week_start.strftime('%Y-%m-%d'),)).fetchone()
    stats['week_done'] = week_done['count'] or 0

    recent_done = db.execute('''
        SELECT pr.leetcode_id, pr.title_cn, pr.difficulty, pr.category, p.updated_at
        FROM progress p JOIN problems pr ON p.problem_id = pr.id
        WHERE p.status = 'done' ORDER BY p.updated_at DESC LIMIT 5
    ''').fetchall()

    next_problem = db.execute('''
        SELECT pr.id, pr.leetcode_id, pr.title_cn, pr.difficulty, pr.category
        FROM problems pr JOIN progress p ON pr.id = p.problem_id
        WHERE p.status = 'todo' AND pr.priority = 'P0' ORDER BY pr.id LIMIT 1
    ''').fetchone()
    db.close()

    return render_template('index.html', active_page='dashboard',
        stats=stats, recent_done=recent_done, next_problem=next_problem,
        heatmap_data=json.dumps(get_heatmap_data(1)),
        category_mastery=json.dumps(get_category_mastery()),
        recommendations=get_recommendations(5),
        prediction=get_progress_prediction())


@app.route('/problems')
def problems():
    db = get_db()
    difficulty = request.args.get('difficulty', '')
    category = request.args.get('category', '')
    priority = request.args.get('priority', '')
    status = request.args.get('status', '')
    bookmarked = request.args.get('bookmarked', '')

    query = '''SELECT pr.*, p.status, p.attempts, p.is_bookmarked
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id WHERE 1=1'''
    params = []
    if difficulty:
        query += ' AND pr.difficulty = ?'; params.append(difficulty)
    if category:
        query += ' AND pr.category = ?'; params.append(category)
    if priority:
        query += ' AND pr.priority = ?'; params.append(priority)
    if status:
        query += ' AND p.status = ?'; params.append(status)
    if bookmarked:
        query += ' AND p.is_bookmarked = 1'
    query += ' ORDER BY pr.priority, pr.id'

    problems_list = db.execute(query, params).fetchall()
    categories = [r['category'] for r in db.execute('SELECT DISTINCT category FROM problems ORDER BY category').fetchall()]
    db.close()

    return render_template('problems.html', active_page='problems',
        problems=problems_list, categories=categories,
        difficulties=['Easy', 'Medium', 'Hard'], priorities=['P0', 'P1', 'P2'],
        statuses=['todo', 'in_progress', 'done', 'review'],
        current_filters={'difficulty': difficulty, 'category': category, 'priority': priority, 'status': status, 'bookmarked': bookmarked})


@app.route('/problem/<int:problem_id>')
def problem_detail(problem_id):
    db = get_db()
    problem = db.execute('''
        SELECT pr.*, p.status, p.attempts, p.solution, p.time_complexity,
               p.space_complexity, p.my_notes, p.is_bookmarked, p.ai_analysis
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
        WHERE pr.id = ?
    ''', (problem_id,)).fetchone()
    if not problem:
        db.close()
        return redirect(url_for('problems'))
    db.close()
    return render_template('problem_detail.html', active_page='problems', problem=problem)


@app.route('/roadmap')
def roadmap():
    db = get_db()
    categories = db.execute('''
        SELECT pr.category, COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
        GROUP BY pr.category ORDER BY CASE pr.category
            WHEN '哈希' THEN 1 WHEN '双指针' THEN 2 WHEN '滑动窗口' THEN 3
            WHEN '前缀和' THEN 4 WHEN '链表' THEN 5 WHEN '二叉树' THEN 6
            WHEN '图/网格' THEN 7 WHEN '回溯' THEN 8 WHEN '二分' THEN 9
            WHEN '栈' THEN 10 WHEN '堆' THEN 11 WHEN '贪心' THEN 12
            WHEN 'DP' THEN 13 ELSE 14 END
    ''').fetchall()
    details = {
        '哈希': {'trigger': '"两个数和为 X"、"找重复/计数"', 'structure': 'dict / set', 'mnemonic': '配对找数 → 哈希'},
        '双指针': {'trigger': '有序数组找配对、原地操作', 'structure': '两个指针', 'mnemonic': '有序/原地 → 双指针'},
        '滑动窗口': {'trigger': '"连续子数组/子串"满足某条件', 'structure': '双指针 + 计数器', 'mnemonic': '连续子串 → 滑动窗口'},
        '前缀和': {'trigger': '区间和、子数组和为 K', 'structure': '数组 + 哈希', 'mnemonic': '区间和 → 前缀和'},
        '链表': {'trigger': '题目给 ListNode', 'structure': '指针 + 虚拟头节点', 'mnemonic': '链表题 → dummy + 快慢指针'},
        '二叉树': {'trigger': '题目给 TreeNode', 'structure': '递归 / BFS 队列', 'mnemonic': '二叉树 → 递归三问'},
        '图/网格': {'trigger': '二维矩阵 BFS/DFS、拓扑', 'structure': '队列 + visited', 'mnemonic': '网格题 → BFS/DFS'},
        '回溯': {'trigger': '"所有方案/排列/组合"', 'structure': '递归 + 状态恢复', 'mnemonic': '所有方案 → 回溯'},
        '二分': {'trigger': '有序数组找位置、"最小的最大"', 'structure': '左右指针', 'mnemonic': '有序/单调 → 二分'},
        '栈': {'trigger': '括号匹配、"下一个更大元素"', 'structure': 'stack / 单调栈', 'mnemonic': '括号匹配 → 栈'},
        '堆': {'trigger': '"Top K"、动态中位数', 'structure': 'heapq', 'mnemonic': 'Top K → 堆'},
        '贪心': {'trigger': '"最少次数/最远距离"', 'structure': '一次遍历', 'mnemonic': '最少次数 → 贪心'},
        'DP': {'trigger': '"最值/方案数"且无法贪心', 'structure': '一维/二维数组', 'mnemonic': '最值方案数 → DP'},
    }
    roadmap_data = []
    for cat in categories:
        d = details.get(cat['category'], {})
        roadmap_data.append({'category': cat['category'], 'total': cat['total'], 'done': cat['done'] or 0,
            'trigger': d.get('trigger',''), 'structure': d.get('structure',''), 'mnemonic': d.get('mnemonic','')})
    db.close()
    return render_template('roadmap.html', active_page='roadmap', categories=roadmap_data)


@app.route('/plan')
def plan():
    db = get_db()
    weeks = [
        {'week':1,'theme':'手感恢复','topics':['哈希','双指针','滑动窗口','栈'],'target':'10-12','mindset':'把语法和 IDE 找回来'},
        {'week':2,'theme':'结构题','topics':['链表','二叉树','图/网格'],'target':'10-12','mindset':'递归和指针的肌肉记忆'},
        {'week':3,'theme':'搜索类','topics':['二分','回溯','堆','贪心'],'target':'8-10','mindset':'学会"分类后选模板"'},
        {'week':4,'theme':'动态规划','topics':['DP'],'target':'8-10','mindset':'不慌，DP 也是套路'},
    ]
    for week in weeks:
        ph = ','.join(['?' for _ in week['topics']])
        pl = db.execute(f'''SELECT pr.id, pr.leetcode_id, pr.title_cn, pr.difficulty, pr.category, p.status
            FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
            WHERE pr.category IN ({ph}) ORDER BY pr.priority, pr.id''', week['topics']).fetchall()
        week['problems'] = pl
        week['done'] = sum(1 for p in pl if p['status'] == 'done')
        week['total'] = len(pl)
        week['progress'] = round(week['done'] / week['total'] * 100 if week['total'] > 0 else 0)
    db.close()
    return render_template('plan.html', active_page='plan', weeks=weeks)


@app.route('/templates')
def templates_page():
    db = get_db()
    tl = db.execute('''
        SELECT pr.category, pr.leetcode_id, pr.title_cn, pr.template_code
        FROM problems pr WHERE pr.template_code IS NOT NULL
        ORDER BY CASE pr.category
            WHEN '哈希' THEN 1 WHEN '双指针' THEN 2 WHEN '滑动窗口' THEN 3
            WHEN '前缀和' THEN 4 WHEN '链表' THEN 5 WHEN '二叉树' THEN 6
            WHEN '图/网格' THEN 7 WHEN '回溯' THEN 8 WHEN '二分' THEN 9
            WHEN '栈' THEN 10 WHEN '堆' THEN 11 WHEN '贪心' THEN 12
            WHEN 'DP' THEN 13 ELSE 14 END, pr.id
    ''').fetchall()
    tbc = {}
    for t in tl:
        tbc.setdefault(t['category'], []).append(t)
    db.close()
    return render_template('templates.html', active_page='templates', templates_by_category=tbc)


# ── API ──

@app.route('/api/update_status', methods=['POST'])
def update_status():
    d = request.json
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ex = db.execute('SELECT id FROM progress WHERE problem_id = ?', (d['problem_id'],)).fetchone()
    if ex:
        db.execute("UPDATE progress SET status = ?, updated_at = ? WHERE problem_id = ?", (d['status'], now, d['problem_id']))
    else:
        db.execute("INSERT INTO progress (problem_id, status, updated_at) VALUES (?, ?, ?)", (d['problem_id'], d['status'], now))
    # 记录状态变更到 activity_log（所有状态都记录）
    db.execute("INSERT INTO activity_log (problem_id, action, timestamp) VALUES (?, ?, ?)", (d['problem_id'], d['status'], now))
    db.commit(); db.close()
    return jsonify({'success': True})


@app.route('/api/update_notes', methods=['POST'])
def update_notes():
    d = request.json
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ex = db.execute('SELECT id FROM progress WHERE problem_id = ?', (d['problem_id'],)).fetchone()
    if ex:
        db.execute("UPDATE progress SET my_notes = ?, updated_at = ? WHERE problem_id = ?", (d['notes'], now, d['problem_id']))
    else:
        db.execute("INSERT INTO progress (problem_id, my_notes, updated_at) VALUES (?, ?, ?)", (d['problem_id'], d['notes'], now))
    db.commit(); db.close()
    return jsonify({'success': True})


@app.route('/api/toggle_bookmark', methods=['POST'])
def toggle_bookmark():
    d = request.json
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ex = db.execute('SELECT id, is_bookmarked FROM progress WHERE problem_id = ?', (d['problem_id'],)).fetchone()
    if ex:
        ns = 0 if ex['is_bookmarked'] else 1
        db.execute("UPDATE progress SET is_bookmarked = ?, updated_at = ? WHERE problem_id = ?", (ns, now, d['problem_id']))
    else:
        ns = 1
        db.execute("INSERT INTO progress (problem_id, is_bookmarked, updated_at) VALUES (?, 1, ?)", (d['problem_id'], now))
    db.commit(); db.close()
    return jsonify({'success': True, 'bookmarked': bool(ns)})


@app.route('/api/ai_analyze', methods=['POST'])
def api_ai_analyze():
    d = request.json
    db = get_db()
    problem = db.execute('''
        SELECT pr.id, pr.title, pr.title_cn, pr.difficulty, pr.category, pr.template_code, p.solution, p.ai_analysis
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id WHERE pr.id = ?
    ''', (d['problem_id'],)).fetchone()

    if not problem:
        db.close()
        return jsonify({'error': '题目不存在'}), 404

    # 如果已有缓存且没传 user_code，直接返回
    if problem['ai_analysis'] and not d.get('user_code'):
        db.close()
        return jsonify({'success': True, 'analysis': problem['ai_analysis'], 'cached': True})

    code = d.get('user_code') or problem['solution'] or ''
    result = analyze_problem(problem['title'], problem['title_cn'], problem['difficulty'],
        problem['category'], problem['template_code'], code or None)

    if result.get('success') and not d.get('user_code'):
        # 持久化到数据库
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ex = db.execute('SELECT id FROM progress WHERE problem_id = ?', (d['problem_id'],)).fetchone()
        if ex:
            db.execute("UPDATE progress SET ai_analysis = ?, updated_at = ? WHERE problem_id = ?", (result['analysis'], now, d['problem_id']))
        else:
            db.execute("INSERT INTO progress (problem_id, ai_analysis, updated_at) VALUES (?, ?, ?)", (d['problem_id'], result['analysis'], now))
        db.commit()

    db.close()
    return jsonify(result)


@app.route('/api/weekly_report')
def api_weekly_report():
    db = get_db()
    week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
    wp = db.execute('''SELECT pr.title_cn, pr.difficulty, pr.category
        FROM progress p JOIN problems pr ON p.problem_id = pr.id
        WHERE p.status = 'done' AND p.updated_at >= ? ORDER BY p.updated_at DESC''', (week_start,)).fetchall()
    total = db.execute("SELECT COUNT(*) as cnt FROM problems").fetchone()['cnt']
    done = db.execute("SELECT COUNT(*) as cnt FROM progress WHERE status = 'done'").fetchone()['cnt']
    weak = db.execute('''SELECT pr.category, COUNT(*) as total,
        SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done
        FROM problems pr LEFT JOIN progress p ON pr.id = p.problem_id
        WHERE pr.priority = 'P0' GROUP BY pr.category
        HAVING done < total ORDER BY CAST(done AS FLOAT) / total ASC LIMIT 3''').fetchall()
    db.close()
    cm = get_category_mastery()
    sd = {'week_done': len(wp), 'total_done': done, 'total_problems': total,
        'progress_percent': round(done / total * 100 if total > 0 else 0),
        'streak': get_streak(), 'week_problems': [dict(p) for p in wp],
        'category_mastery': cm, 'weak_categories': [r['category'] for r in weak]}
    report = generate_weekly_report(sd)
    return jsonify({'success': True, 'report': report, 'stats': sd})


@app.route('/api/heatmap')
def api_heatmap():
    return jsonify(get_heatmap_data(1))

@app.route('/api/mastery')
def api_mastery():
    return jsonify(get_category_mastery())

@app.route('/api/recommendations')
def api_recommendations():
    return jsonify(get_recommendations(request.args.get('limit', 5, type=int)))

@app.route('/api/prediction')
def api_prediction():
    return jsonify(get_progress_prediction())


if __name__ == '__main__':
    init_db()
    seed_problems()
    app.config['TIMEOUT'] = 180
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
