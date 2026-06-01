"""LeetCode 进度追踪器 - 数据库模型 v2"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'leetcode.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY,
            leetcode_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            title_cn TEXT,
            difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
            category TEXT,
            priority TEXT CHECK(priority IN ('P0', 'P1', 'P2')),
            tags TEXT,
            url TEXT,
            template_code TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY,
            problem_id INTEGER UNIQUE,
            status TEXT CHECK(status IN ('todo', 'in_progress', 'done', 'review')) DEFAULT 'todo',
            attempts INTEGER DEFAULT 0,
            last_attempt TIMESTAMP,
            solution TEXT,
            time_complexity TEXT,
            space_complexity TEXT,
            my_notes TEXT,
            is_bookmarked BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            id INTEGER PRIMARY KEY,
            date DATE UNIQUE,
            problems_done INTEGER DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 活动日志表 (热力图 + streak)
    try:
        cursor.execute("SELECT COUNT(*) FROM activity_log LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY,
                problem_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems(id)
            )
        """)

    conn.commit()
    conn.close()


def seed_problems():
    problems = [
        (1, 1, 'Two Sum', '两数之和', 'Easy', '哈希', 'P0', '哈希', '/problems/two-sum',
         'def twoSum(nums, target):\n    seen = {}\n    for i, x in enumerate(nums):\n        if target - x in seen:\n            return [seen[target - x], i]\n        seen[x] = i'),
        (2, 15, '3Sum', '三数之和', 'Medium', '双指针', 'P0', '双指针', '/problems/3sum',
         'def threeSum(nums):\n    nums.sort()\n    res = []\n    for i in range(len(nums) - 2):\n        if i > 0 and nums[i] == nums[i-1]: continue\n        l, r = i + 1, len(nums) - 1\n        while l < r:\n            s = nums[i] + nums[l] + nums[r]\n            if s == 0:\n                res.append([nums[i], nums[l], nums[r]])\n                while l < r and nums[l] == nums[l+1]: l += 1\n                while l < r and nums[r] == nums[r-1]: r -= 1\n                l += 1; r -= 1\n            elif s < 0: l += 1\n            else: r -= 1\n    return res'),
        (3, 3, 'Longest Substring Without Repeating Characters', '无重复字符的最长子串', 'Medium', '滑动窗口', 'P0', '滑动窗口', '/problems/longest-substring-without-repeating-characters',
         'def lengthOfLongestSubstring(s):\n    cnt = {}\n    l = 0\n    ans = 0\n    for r in range(len(s)):\n        cnt[s[r]] = cnt.get(s[r], 0) + 1\n        while cnt[s[r]] > 1:\n            cnt[s[l]] -= 1\n            if cnt[s[l]] == 0: del cnt[s[l]]\n            l += 1\n        ans = max(ans, r - l + 1)\n    return ans'),
        (4, 560, 'Subarray Sum Equals K', '和为 K 的子数组', 'Medium', '前缀和', 'P0', '前缀和', '/problems/subarray-sum-equals-k',
         'def subarraySum(nums, k):\n    pre_count = {0: 1}\n    pre_sum = 0\n    ans = 0\n    for x in nums:\n        pre_sum += x\n        ans += pre_count.get(pre_sum - k, 0)\n        pre_count[pre_sum] = pre_count.get(pre_sum, 0) + 1\n    return ans'),
        (5, 53, 'Maximum Subarray', '最大子数组和', 'Medium', 'DP', 'P0', 'DP', '/problems/maximum-subarray',
         'def maxSubArray(nums):\n    dp = nums[0]\n    res = dp\n    for i in range(1, len(nums)):\n        dp = max(nums[i], dp + nums[i])\n        res = max(res, dp)\n    return res'),
        (6, 206, 'Reverse Linked List', '反转链表', 'Easy', '链表', 'P0', '链表', '/problems/reverse-linked-list',
         'def reverseList(head):\n    prev, cur = None, head\n    while cur:\n        nxt = cur.next\n        cur.next = prev\n        prev = cur\n        cur = nxt\n    return prev'),
        (7, 21, 'Merge Two Sorted Lists', '合并两个有序链表', 'Easy', '链表', 'P0', '链表', '/problems/merge-two-sorted-lists',
         'def mergeTwoLists(l1, l2):\n    dummy = ListNode(0)\n    cur = dummy\n    while l1 and l2:\n        if l1.val <= l2.val:\n            cur.next = l1\n            l1 = l1.next\n        else:\n            cur.next = l2\n            l2 = l2.next\n        cur = cur.next\n    cur.next = l1 or l2\n    return dummy.next'),
        (8, 141, 'Linked List Cycle', '环形链表', 'Easy', '链表', 'P0', '快慢指针', '/problems/linked-list-cycle',
         'def hasCycle(head):\n    slow = fast = head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n        if slow == fast: return True\n    return False'),
        (9, 146, 'LRU Cache', 'LRU 缓存', 'Medium', '链表', 'P0', '链表+哈希', '/problems/lru-cache',
         'from collections import OrderedDict\nclass LRUCache:\n    def __init__(self, capacity):\n        self.cache = OrderedDict()\n        self.capacity = capacity\n    def get(self, key):\n        if key not in self.cache: return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n    def put(self, key, value):\n        if key in self.cache: self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)'),
        (10, 104, 'Maximum Depth of Binary Tree', '二叉树的最大深度', 'Easy', '二叉树', 'P0', '递归', '/problems/maximum-depth-of-binary-tree',
         'def maxDepth(root):\n    if not root: return 0\n    return 1 + max(maxDepth(root.left), maxDepth(root.right))'),
        (11, 102, 'Binary Tree Level Order Traversal', '二叉树的层序遍历', 'Medium', '二叉树', 'P0', 'BFS', '/problems/binary-tree-level-order-traversal',
         'from collections import deque\ndef levelOrder(root):\n    if not root: return []\n    q = deque([root])\n    res = []\n    while q:\n        level = []\n        for _ in range(len(q)):\n            node = q.popleft()\n            level.append(node.val)\n            if node.left: q.append(node.left)\n            if node.right: q.append(node.right)\n        res.append(level)\n    return res'),
        (12, 236, 'Lowest Common Ancestor of a Binary Tree', '二叉树的最近公共祖先', 'Medium', '二叉树', 'P0', '递归', '/problems/lowest-common-ancestor-of-a-binary-tree',
         'def lowestCommonAncestor(root, p, q):\n    if not root or root == p or root == q:\n        return root\n    left = lowestCommonAncestor(root.left, p, q)\n    right = lowestCommonAncestor(root.right, p, q)\n    if left and right: return root\n    return left or right'),
        (13, 200, 'Number of Islands', '岛屿数量', 'Medium', '图/网格', 'P0', 'DFS', '/problems/number-of-islands',
         'def numIslands(grid):\n    if not grid: return 0\n    m, n = len(grid), len(grid[0])\n    def dfs(i, j):\n        if i < 0 or i >= m or j < 0 or j >= n or grid[i][j] != "1": return\n        grid[i][j] = "0"\n        for di, dj in [(-1,0),(1,0),(0,-1),(0,1)]:\n            dfs(i+di, j+dj)\n    count = 0\n    for i in range(m):\n        for j in range(n):\n            if grid[i][j] == "1":\n                count += 1\n                dfs(i, j)\n    return count'),
        (14, 46, 'Permutations', '全排列', 'Medium', '回溯', 'P0', '回溯', '/problems/permutations',
         'def permute(nums):\n    res = []\n    def backtrack(path, used):\n        if len(path) == len(nums):\n            res.append(path[:])\n            return\n        for i in range(len(nums)):\n            if used[i]: continue\n            used[i] = True\n            path.append(nums[i])\n            backtrack(path, used)\n            path.pop()\n            used[i] = False\n    backtrack([], [False] * len(nums))\n    return res'),
        (15, 78, 'Subsets', '子集', 'Medium', '回溯', 'P0', '回溯', '/problems/subsets',
         'def subsets(nums):\n    res = []\n    def backtrack(start, path):\n        res.append(path[:])\n        for i in range(start, len(nums)):\n            path.append(nums[i])\n            backtrack(i + 1, path)\n            path.pop()\n    backtrack(0, [])\n    return res'),
        (16, 20, 'Valid Parentheses', '有效的括号', 'Easy', '栈', 'P0', '栈', '/problems/valid-parentheses',
         'def isValid(s):\n    stack = []\n    mapping = {"(": ")", "[": "]", "{": "}"}\n    for c in s:\n        if c in mapping:\n            stack.append(c)\n        elif not stack or mapping[stack.pop()] != c:\n            return False\n    return not stack'),
        (17, 215, 'Kth Largest Element in an Array', '数组中的第K个最大元素', 'Medium', '堆', 'P0', '堆', '/problems/kth-largest-element-in-an-array',
         'import heapq\ndef findKthLargest(nums, k):\n    heap = []\n    for x in nums:\n        heapq.heappush(heap, x)\n        if len(heap) > k:\n            heapq.heappop(heap)\n    return heap[0]'),
        (18, 121, 'Best Time to Buy and Sell Stock', '买卖股票的最佳时机', 'Easy', '贪心', 'P0', '贪心', '/problems/best-time-to-buy-and-sell-stock',
         'def maxProfit(prices):\n    min_price = float("inf")\n    max_profit = 0\n    for price in prices:\n        min_price = min(min_price, price)\n        max_profit = max(max_profit, price - min_price)\n    return max_profit'),
        (19, 70, 'Climbing Stairs', '爬楼梯', 'Easy', 'DP', 'P0', 'DP', '/problems/climbing-stairs',
         'def climbStairs(n):\n    if n <= 2: return n\n    a, b = 1, 2\n    for _ in range(3, n + 1):\n        a, b = b, a + b\n    return b'),
        (20, 198, 'House Robber', '打家劫舍', 'Medium', 'DP', 'P0', 'DP', '/problems/house-robber',
         'def rob(nums):\n    if not nums: return 0\n    if len(nums) == 1: return nums[0]\n    a, b = nums[0], max(nums[0], nums[1])\n    for i in range(2, len(nums)):\n        a, b = b, max(b, a + nums[i])\n    return b'),
        (21, 128, 'Longest Consecutive Sequence', '最长连续序列', 'Medium', '哈希', 'P1', '哈希', '/problems/longest-consecutive-sequence', None),
        (22, 11, 'Container With Most Water', '盛最多水的容器', 'Medium', '双指针', 'P1', '双指针', '/problems/container-with-most-water', None),
        (23, 76, 'Minimum Window Substring', '最小覆盖子串', 'Hard', '滑动窗口', 'P1', '滑动窗口', '/problems/minimum-window-substring', None),
        (24, 142, 'Linked List Cycle II', '环形链表 II', 'Medium', '链表', 'P1', '快慢指针', '/problems/linked-list-cycle-ii', None),
        (25, 25, 'Reverse Nodes in k-Group', 'K 个一组翻转链表', 'Hard', '链表', 'P1', '链表', '/problems/reverse-nodes-in-k-group', None),
        (26, 98, 'Validate Binary Search Tree', '验证二叉搜索树', 'Medium', '二叉树', 'P1', '递归', '/problems/validate-binary-search-tree', None),
        (27, 124, 'Binary Tree Maximum Path Sum', '二叉树中的最大路径和', 'Hard', '二叉树', 'P1', '递归', '/problems/binary-tree-maximum-path-sum', None),
        (28, 199, 'Binary Tree Right Side View', '二叉树的右视图', 'Medium', '二叉树', 'P1', 'BFS', '/problems/binary-tree-right-side-view', None),
        (29, 207, 'Course Schedule', '课程表', 'Medium', '图/网格', 'P1', '拓扑排序', '/problems/course-schedule', None),
        (30, 39, 'Combination Sum', '组合总和', 'Medium', '回溯', 'P1', '回溯', '/problems/combination-sum', None),
        (31, 22, 'Generate Parentheses', '括号生成', 'Medium', '回溯', 'P1', '回溯', '/problems/generate-parentheses', None),
        (32, 33, 'Search in Rotated Sorted Array', '搜索旋转排序数组', 'Medium', '二分', 'P1', '二分', '/problems/search-in-rotated-sorted-array', None),
        (33, 739, 'Daily Temperatures', '每日温度', 'Medium', '栈', 'P1', '单调栈', '/problems/daily-temperatures', None),
        (34, 322, 'Coin Change', '零钱兑换', 'Medium', 'DP', 'P1', 'DP', '/problems/coin-change', None),
        (35, 72, 'Edit Distance', '编辑距离', 'Hard', 'DP', 'P1', 'DP', '/problems/edit-distance', None),
        (36, 42, 'Trapping Rain Water', '接雨水', 'Hard', '双指针', 'P2', '双指针/单调栈', '/problems/trapping-rain-water', None),
        (37, 84, 'Largest Rectangle in Histogram', '柱状图中最大的矩形', 'Hard', '栈', 'P2', '单调栈', '/problems/largest-rectangle-in-histogram', None),
        (38, 295, 'Find Median from Data Stream', '数据流的中位数', 'Hard', '堆', 'P2', '双堆', '/problems/find-median-from-data-stream', None),
        (39, 300, 'Longest Increasing Subsequence', '最长递增子序列', 'Medium', 'DP', 'P2', 'DP+二分', '/problems/longest-increasing-subsequence', None),
        (40, 4, 'Median of Two Sorted Arrays', '寻找两个正序数组的中位数', 'Hard', '二分', 'P2', '二分', '/problems/median-of-two-sorted-arrays', None),
    ]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM problems")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO problems (id, leetcode_id, title, title_cn, difficulty, category, priority, tags, url, template_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, problems)
        cursor.execute("INSERT INTO progress (problem_id, status) SELECT id, 'todo' FROM problems")
        conn.commit()
        print(f"导入 {len(problems)} 道题目")
    conn.close()


def get_streak():
    """计算连续打卡天数（任何状态更新都算打卡）"""
    conn = get_db()
    today = datetime.now().date()
    streak = 0
    check_date = today
    while True:
        date_str = check_date.strftime('%Y-%m-%d')
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM progress WHERE date(updated_at) = ? AND status != 'todo'",
            (date_str,)
        ).fetchone()
        if row['cnt'] > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    conn.close()
    return streak


def get_heatmap_data(years=1):
    """获取热力图数据（最近N年）"""
    conn = get_db()
    start = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
    rows = conn.execute("""
        SELECT date(timestamp) as day, COUNT(*) as count
        FROM activity_log
        WHERE timestamp >= ?
        GROUP BY date(timestamp)
    """, (start,)).fetchall()
    conn.close()
    return {row['day']: row['count'] for row in rows}


def get_category_mastery():
    """获取各算法分类的掌握度"""
    conn = get_db()
    rows = conn.execute("""
        SELECT pr.category,
            COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done,
            SUM(CASE WHEN p.status = 'review' THEN 1 ELSE 0 END) as review
        FROM problems pr
        LEFT JOIN progress p ON pr.id = p.problem_id
        GROUP BY pr.category
        ORDER BY pr.category
    """).fetchall()
    conn.close()
    result = []
    for row in rows:
        total = row['total']
        done = row['done'] or 0
        review = row['review'] or 0
        mastery = round((done * 1.0 + review * 0.5) / total * 100) if total > 0 else 0
        result.append({'category': row['category'], 'total': total, 'done': done, 'mastery': mastery})
    return result


def get_recommendations(limit=5):
    """智能推荐下一题"""
    conn = get_db()

    weak_categories = conn.execute("""
        SELECT pr.category,
            COUNT(*) as total,
            SUM(CASE WHEN p.status = 'done' THEN 1 ELSE 0 END) as done
        FROM problems pr
        LEFT JOIN progress p ON pr.id = p.problem_id
        WHERE pr.priority = 'P0'
        GROUP BY pr.category
        HAVING done < total
        ORDER BY CAST(done AS FLOAT) / total ASC
        LIMIT 3
    """).fetchall()

    weak_cats = [row['category'] for row in weak_categories]
    recommendations = []

    p0_todo = conn.execute("""
        SELECT pr.id, pr.leetcode_id, pr.title_cn, pr.title, pr.difficulty, pr.category, pr.priority
        FROM problems pr
        JOIN progress p ON pr.id = p.problem_id
        WHERE p.status = 'todo' AND pr.priority = 'P0'
        ORDER BY pr.id LIMIT ?
    """, (limit,)).fetchall()
    recommendations.extend([dict(r) for r in p0_todo])

    if len(recommendations) < limit and weak_cats:
        placeholders = ','.join(['?' for _ in weak_cats])
        remaining = limit - len(recommendations)
        existing_ids = [r['id'] for r in recommendations]
        id_placeholders = ','.join(['?' for _ in existing_ids]) if existing_ids else '0'
        p1_weak = conn.execute(f"""
            SELECT pr.id, pr.leetcode_id, pr.title_cn, pr.title, pr.difficulty, pr.category, pr.priority
            FROM problems pr JOIN progress p ON pr.id = p.problem_id
            WHERE p.status = 'todo' AND pr.priority = 'P1' AND pr.category IN ({placeholders})
            AND pr.id NOT IN ({id_placeholders})
            ORDER BY pr.id LIMIT ?
        """, weak_cats + existing_ids + [remaining]).fetchall()
        recommendations.extend([dict(r) for r in p1_weak])

    if len(recommendations) < limit:
        remaining = limit - len(recommendations)
        existing_ids = [r['id'] for r in recommendations]
        id_placeholders = ','.join(['?' for _ in existing_ids]) if existing_ids else '0'
        review_items = conn.execute(f"""
            SELECT pr.id, pr.leetcode_id, pr.title_cn, pr.title, pr.difficulty, pr.category, pr.priority
            FROM problems pr JOIN progress p ON pr.id = p.problem_id
            WHERE p.status = 'review' AND pr.id NOT IN ({id_placeholders})
            ORDER BY p.updated_at ASC LIMIT ?
        """, existing_ids + [remaining]).fetchall()
        recommendations.extend([dict(r) for r in review_items])

    for r in recommendations:
        if r['priority'] == 'P0' and r.get('category') in weak_cats:
            r['reason'] = f"P0 必刷 + {r['category']}薄弱"
        elif r['priority'] == 'P0':
            r['reason'] = "P0 必刷题"
        elif r.get('category') in weak_cats:
            r['reason'] = f"{r['category']}薄弱，加强训练"
        else:
            r['reason'] = "需要复习巩固"

    conn.close()
    return recommendations[:limit]


def get_progress_prediction():
    """预测完成进度"""
    conn = get_db()
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    recent_done = conn.execute(
        "SELECT COUNT(*) as cnt FROM activity_log WHERE action = 'solved' AND timestamp >= ?",
        (thirty_days_ago,)
    ).fetchone()
    total = conn.execute("SELECT COUNT(*) as cnt FROM problems").fetchone()['cnt']
    done = conn.execute("SELECT COUNT(*) as cnt FROM progress WHERE status = 'done'").fetchone()['cnt']
    remaining = total - done
    solved_30d = recent_done['cnt'] or 0
    daily_rate = solved_30d / 30 if solved_30d > 0 else 0
    weekly_rate = daily_rate * 7
    days_to_finish = round(remaining / daily_rate) if daily_rate > 0 else None
    weeks_to_finish = round(remaining / weekly_rate, 1) if weekly_rate > 0 else None
    target_date = (datetime.now() + timedelta(days=days_to_finish)).strftime('%Y-%m-%d') if days_to_finish else None
    conn.close()
    return {
        'total': total, 'done': done, 'remaining': remaining,
        'solved_30d': solved_30d, 'daily_rate': round(daily_rate, 2),
        'weekly_rate': round(weekly_rate, 1), 'days_to_finish': days_to_finish,
        'weeks_to_finish': weeks_to_finish, 'target_date': target_date
    }


if __name__ == '__main__':
    init_db()
    seed_problems()
    print("数据库初始化完成！")
