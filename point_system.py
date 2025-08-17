import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import csv
import ttkbootstrap as tb
import math

# 数据库配置 - 请根据您的实际配置修改
DB_CONFIG = {
    'host': '124.222.211.202',
    'user': 'score',
    'password': 'Jiyu_42206180',
    'database': 'point_system_db'
}


class Database:
    """数据库操作类"""

    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            return True
        except Error as e:
            messagebox.showerror("数据库错误", f"连接数据库失败: {str(e)}")
            return False

    def create_tables(self):
        """创建必要的数据表"""
        if not self.connection:
            return False

        try:
            cursor = self.connection.cursor()

            # 创建用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) UNIQUE,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    role ENUM('user', 'admin', 'superadmin') NOT NULL
                )
            """)

            # 创建记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    operation ENUM('加分', '减分') NOT NULL,
                    score INT NOT NULL,
                    reason VARCHAR(255) NOT NULL,
                    operator VARCHAR(50) NOT NULL,
                    valid TINYINT DEFAULT 1
                )
            """)

            self.connection.commit()
            return True
        except Error as e:
            messagebox.showerror("数据库错误", f"创建表失败: {str(e)}")
            return False

    def execute_query(self, query, params=None, fetch=False):
        """执行SQL查询"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())

            if fetch:
                return cursor.fetchall()
            else:
                self.connection.commit()
                return True
        except Error as e:
            messagebox.showerror("数据库错误", f"查询失败: {str(e)}")
            return False


class LoginWindow(tb.Toplevel):
    """登录窗口"""

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("学分管理系统 - 登录")
        self.geometry("400x300")
        self.resizable(False, False)

        # 设置焦点并捕获关闭事件
        self.focus_set()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # 设置字体
        self.STYLE = tb.Style()
        self.STYLE.configure('TLabel', font=('宋体', 10))
        self.STYLE.configure('TButton', font=('宋体', 10))

        # 创建UI
        self.create_widgets()

        # 绑定回车键
        self.bind('<Return>', lambda e: self.login())

    def create_widgets(self):
        """创建登录界面组件"""
        frame = tb.Frame(self)
        frame.pack(pady=50, padx=30, fill='both', expand=True)

        tb.Label(frame, text="用户名:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.username_entry = tb.Entry(frame, width=25)
        self.username_entry.grid(row=0, column=1, pady=10, padx=5)

        tb.Label(frame, text="密码:", bootstyle="primary").grid(row=1, column=0, pady=10, padx=5, sticky='e')
        self.password_entry = tb.Entry(frame, width=25, show="*")
        self.password_entry.grid(row=1, column=1, pady=10, padx=5)

        login_btn = tb.Button(frame, text="登录", bootstyle="success", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=20, padx=5, sticky='ew')

        # 设置焦点
        self.username_entry.focus_set()

    def login(self):
        """处理登录逻辑"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("输入错误", "用户名和密码不能为空")
            return

        db = Database()
        if not db.connection:
            return

        result = db.execute_query(
            "SELECT student_id, role FROM users WHERE username = %s AND password = %s",
            (username, password),
            fetch=True
        )

        if result:
            student_id, role = result[0]
            self.destroy()
            self.master.show_main_window(username, student_id, role)
        else:
            messagebox.showerror("登录失败", "账号或密码错误")

    def on_close(self):
        """关闭登录窗口时退出程序"""
        self.master.destroy()


class MainWindow(tb.Window):
    """主窗口"""

    def __init__(self):
        super().__init__(themename="litera")
        self.title("学分管理系统")
        self.geometry("1000x600")
        self.withdraw()  # 初始隐藏主窗口

        # 显示登录窗口
        self.login_window = LoginWindow(self)

    def show_main_window(self, username, student_id, role):
        """显示主界面"""
        self.deiconify()  # 显示主窗口
        self.title(f"学分管理系统 - 当前用户: {username} ({role})")

        self.username = username
        self.student_id = student_id
        self.role = role

        # 创建菜单栏
        self.create_menu()

        # 创建主框架
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 初始显示查询界面
        # 根据角色显示不同的查询选项
        if self.role == 'superadmin':
            self.show_query_frame()
        else :
            self.query_my_records()

    def create_menu(self):
        """创建菜单栏"""
        menu_bar = tb.Menu(self)

        # 操作菜单
        action_menu = tb.Menu(menu_bar, tearoff=0)

        # 根据角色显示不同的操作菜单
        if self.role in ['admin', 'superadmin']:
            action_menu.add_command(label="添加记录", command=self.show_add_frame)
            action_menu.add_command(label="撤销记录", command=self.show_revoke_frame)

        action_menu.add_command(label="查看排行", command=self.show_ranking)
        action_menu.add_separator()
        action_menu.add_command(label="退出系统", command=self.quit)
        menu_bar.add_cascade(label="操作", menu=action_menu)

        # 查询菜单
        query_menu = tb.Menu(menu_bar, tearoff=0)

        # 根据角色显示不同的查询选项
        if self.role == 'superadmin':
            query_menu.add_command(label="查询所有记录", command=self.show_query_frame)
            query_menu.add_command(label="查询我的操作记录", command=self.query_my_operations)
            query_menu.add_command(label="查询我的记录", command=self.query_my_records)
        elif self.role == 'admin':
            query_menu.add_command(label="查询我的操作记录", command=self.query_my_operations)
            query_menu.add_command(label="查询我的学分记录", command=self.query_my_records)
        else:  # user
            query_menu.add_command(label="查询我的学分记录", command=self.query_my_records)

        menu_bar.add_cascade(label="查询", menu=query_menu)

        # 用户管理菜单（仅超级管理员）
        if self.role == 'superadmin':
            user_menu = tb.Menu(menu_bar, tearoff=0)
            user_menu.add_command(label="添加用户", command=self.show_add_user_frame)
            user_menu.add_command(label="批量添加用户", command=self.show_batch_add_user_frame)
            user_menu.add_command(label="编辑用户", command=self.show_edit_user_frame)
            menu_bar.add_cascade(label="用户管理", menu=user_menu)

        # 系统菜单
        system_menu = tb.Menu(menu_bar, tearoff=0)
        system_menu.add_command(label="更改密码", command=self.show_change_password_frame)
        system_menu.add_command(label="登出", command=self.logout)
        menu_bar.add_cascade(label="系统", menu=system_menu)

        self.config(menu=menu_bar)

    def show_add_frame(self):
        """显示添加记录界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        tb.Label(frame, text="学号:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.student_id_entry = tb.Entry(frame, width=25)
        self.student_id_entry.grid(row=0, column=1, pady=10, padx=5)

        tb.Label(frame, text="操作:", bootstyle="primary").grid(row=1, column=0, pady=10, padx=5, sticky='e')
        self.operation_var = tk.StringVar()
        operation_combo = tb.Combobox(frame, textvariable=self.operation_var, width=22)
        operation_combo['values'] = ('加分', '减分')
        operation_combo.current(0)
        operation_combo.grid(row=1, column=1, pady=10, padx=5)

        tb.Label(frame, text="分数:", bootstyle="primary").grid(row=2, column=0, pady=10, padx=5, sticky='e')
        self.score_entry = tb.Entry(frame, width=25)
        self.score_entry.grid(row=2, column=1, pady=10, padx=5)

        tb.Label(frame, text="原因:", bootstyle="primary").grid(row=3, column=0, pady=10, padx=5, sticky='e')
        self.reason_var = tk.StringVar()
        reason_combo = tb.Combobox(frame, textvariable=self.reason_var, width=22)
        reason_combo['values'] = ('课堂表现', '作业完成', '考试加分', '违规扣分', '其他')
        reason_combo.grid(row=3, column=1, pady=10, padx=5)

        # 自定义原因输入框
        tb.Label(frame, text="自定义原因:", bootstyle="primary").grid(row=4, column=0, pady=10, padx=5, sticky='e')
        self.custom_reason_entry = tb.Entry(frame, width=25)
        self.custom_reason_entry.grid(row=4, column=1, pady=10, padx=5)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        submit_btn = tb.Button(btn_frame, text="提交", bootstyle="success", command=self.submit_record)
        submit_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def submit_record(self):
        """提交记录到数据库"""
        student_id = self.student_id_entry.get()
        operation = self.operation_var.get()
        score = self.score_entry.get()
        reason = self.custom_reason_entry.get() if self.custom_reason_entry.get() else self.reason_var.get()

        if not all([student_id, operation, score, reason]):
            messagebox.showwarning("输入错误", "所有字段都必须填写")
            return

        try:
            score = int(score)
        except ValueError:
            messagebox.showwarning("输入错误", "分数必须是整数")
            return

        db = Database()
        if not db.connection:
            return

        # 插入记录
        query = """
            INSERT INTO records (student_id, operation, score, reason, operator, valid)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        if db.execute_query(query, (student_id, operation, score, reason, self.username)):
            messagebox.showinfo("成功", "记录添加成功")
            self.show_query_frame()

    def show_revoke_frame(self):
        """显示撤销记录界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        tb.Label(frame, text="记录ID:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.record_id_entry = tb.Entry(frame, width=25)
        self.record_id_entry.grid(row=0, column=1, pady=10, padx=5)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=20)

        submit_btn = tb.Button(btn_frame, text="提交", bootstyle="warning", command=self.revoke_record)
        submit_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def revoke_record(self):
        """撤销记录"""
        record_id = self.record_id_entry.get()

        if not record_id:
            messagebox.showwarning("输入错误", "记录ID不能为空")
            return

        db = Database()
        if not db.connection:
            return

        # 检查记录是否存在
        result = db.execute_query(
            "SELECT * FROM records WHERE id = %s",
            (record_id,),
            fetch=True
        )

        if not result:
            messagebox.showerror("错误", "找不到指定的记录ID")
            return

        record = result[0]
        operator = record[5]

        # 检查权限：普通用户不能撤销，管理员只能撤销自己的记录
        if self.role == 'user':
            messagebox.showerror("权限不足", "普通用户不能撤销记录")
            return
        elif self.role == 'admin' and operator != self.username:
            messagebox.showerror("权限不足", "只能撤销自己添加的记录")
            return

        # 更新记录状态
        if db.execute_query(
                "UPDATE records SET valid = 0 WHERE id = %s",
                (record_id,)
        ):
            messagebox.showinfo("成功", "记录已撤销")
            self.show_query_frame()

    def show_query_frame(self):
        """显示查询界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ("id", "student_id", "operation", "score", "reason", "operator", "valid")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        # 设置列标题
        self.tree.heading("id", text="ID")
        self.tree.heading("student_id", text="学号")
        self.tree.heading("operation", text="操作")
        self.tree.heading("score", text="分数")
        self.tree.heading("reason", text="原因")
        self.tree.heading("operator", text="操作者")
        self.tree.heading("valid", text="有效状态")

        # 设置列宽
        self.tree.column("id", width=50)
        self.tree.column("student_id", width=100)
        self.tree.column("operation", width=80)
        self.tree.column("score", width=80)
        self.tree.column("reason", width=200)
        self.tree.column("operator", width=100)
        self.tree.column("valid", width=80)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 加载数据
        self.load_records()

    def load_records(self, query_type="all"):
        """加载记录数据"""
        self.tree.delete(*self.tree.get_children())

        db = Database()
        if not db.connection:
            return

        if query_type == "my":
            query = "SELECT * FROM records WHERE student_id = %s"
            params = (self.student_id,)
        elif query_type == "my_operations":
            query = "SELECT * FROM records WHERE operator = %s"
            params = (self.username,)
        else:  # all
            query = "SELECT * FROM records"
            params = None

        records = db.execute_query(query, params, fetch=True)

        if records:
            for record in records:
                valid_text = "有效" if record[6] == 1 else "已撤销"
                self.tree.insert("", "end", values=(
                    record[0], record[1], record[2], record[3],
                    record[4], record[5], valid_text
                ))

    def query_my_records(self):
        """查询当前用户的学分记录"""
        self.show_query_frame()
        self.load_records("my")

    def query_my_operations(self):
        """查询当前用户的操作记录"""
        self.show_query_frame()
        self.load_records("my_operations")

    def show_ranking(self):
        """显示排行榜"""
        db = Database()
        if not db.connection:
            return

        # 计算每个学生的总分
        query = """
            SELECT student_id, 
                   SUM(CASE WHEN operation='加分' THEN score ELSE -score END) AS total
            FROM records
            WHERE valid = 1
            GROUP BY student_id
            ORDER BY total DESC
        """
        results = db.execute_query(query, fetch=True)

        if not results:
            messagebox.showinfo("排行榜", "没有可用的记录")
            return

        # 创建新窗口显示排行榜
        rank_window = tb.Toplevel(self)
        rank_window.title("学分排行榜")
        rank_window.geometry("400x500")

        frame = tb.Frame(rank_window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建表格
        columns = ("rank", "student_id", "score")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        tree.heading("rank", text="排名")
        tree.heading("student_id", text="学号")
        tree.heading("score", text="总分")

        tree.column("rank", width=50)
        tree.column("student_id", width=150)
        tree.column("score", width=100)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 填充数据
        for rank, (student_id, total) in enumerate(results, 1):
            tree.insert("", "end", values=(rank, student_id, total))

    def show_add_user_frame(self):
        """显示添加用户界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        tb.Label(frame, text="学号:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.new_student_id_entry = tb.Entry(frame, width=25)
        self.new_student_id_entry.grid(row=0, column=1, pady=10, padx=5)

        tb.Label(frame, text="用户名:", bootstyle="primary").grid(row=1, column=0, pady=10, padx=5, sticky='e')
        self.new_username_entry = tb.Entry(frame, width=25)
        self.new_username_entry.grid(row=1, column=1, pady=10, padx=5)

        tb.Label(frame, text="密码:", bootstyle="primary").grid(row=2, column=0, pady=10, padx=5, sticky='e')
        self.new_password_entry = tb.Entry(frame, width=25, show="*")
        self.new_password_entry.grid(row=2, column=1, pady=10, padx=5)

        tb.Label(frame, text="角色:", bootstyle="primary").grid(row=3, column=0, pady=10, padx=5, sticky='e')
        self.new_role_var = tk.StringVar()
        role_combo = tb.Combobox(frame, textvariable=self.new_role_var, width=22)
        role_combo['values'] = ('user', 'admin', 'superadmin')
        role_combo.current(0)
        role_combo.grid(row=3, column=1, pady=10, padx=5)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        submit_btn = tb.Button(btn_frame, text="添加用户", bootstyle="success", command=self.add_user)
        submit_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def add_user(self):
        """添加新用户"""
        student_id = self.new_student_id_entry.get()
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        role = self.new_role_var.get()

        if not all([student_id, username, password, role]):
            messagebox.showwarning("输入错误", "所有字段都必须填写")
            return

        db = Database()
        if not db.connection:
            return

        # 检查用户名是否已存在
        result = db.execute_query(
            "SELECT id FROM users WHERE username = %s",
            (username,),
            fetch=True
        )

        if result:
            messagebox.showerror("错误", "用户名已存在")
            return

        # 检查学号是否已存在
        result = db.execute_query(
            "SELECT id FROM users WHERE student_id = %s",
            (student_id,),
            fetch=True
        )

        if result:
            messagebox.showerror("错误", "学号已存在")
            return

        # 插入新用户
        query = """
            INSERT INTO users (student_id, username, password, role)
            VALUES (%s, %s, %s, %s)
        """
        if db.execute_query(query, (student_id, username, password, role)):
            messagebox.showinfo("成功", "用户添加成功")
            self.show_query_frame()

    def show_batch_add_user_frame(self):
        """显示批量添加用户界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        # 输入框
        input_frame = tb.Frame(frame)
        input_frame.pack(fill='x', pady=10)

        tb.Label(input_frame, text="学号规则:", bootstyle="primary").grid(row=0, column=0, padx=5, sticky='e')
        self.student_id_pattern = tb.Entry(input_frame, width=30)
        self.student_id_pattern.grid(row=0, column=1, padx=5)
        self.student_id_pattern.insert(0, r"STU\d{3}")

        tb.Label(input_frame, text="用户名规则:", bootstyle="primary").grid(row=1, column=0, padx=5, sticky='e')
        self.username_pattern = tb.Entry(input_frame, width=30)
        self.username_pattern.grid(row=1, column=1, padx=5)
        self.username_pattern.insert(0, r"user\d{2}")

        tb.Label(input_frame, text="角色:", bootstyle="primary").grid(row=2, column=0, padx=5, sticky='e')
        self.batch_role_var = tk.StringVar()
        role_combo = tb.Combobox(input_frame, textvariable=self.batch_role_var, width=27)
        role_combo['values'] = ('user', 'admin', 'superadmin')
        role_combo.current(0)
        role_combo.grid(row=2, column=1, padx=5)

        tb.Label(input_frame, text="密码规则:", bootstyle="primary").grid(row=3, column=0, padx=5, sticky='e')
        self.password_pattern = tb.Entry(input_frame, width=30)
        self.password_pattern.grid(row=3, column=1, padx=5)
        self.password_pattern.insert(0, r"Passw0rd!\d{2}")

        tb.Label(input_frame, text="生成数量:", bootstyle="primary").grid(row=4, column=0, padx=5, sticky='e')
        self.user_count = tb.Entry(input_frame, width=30)
        self.user_count.grid(row=4, column=1, padx=5)
        self.user_count.insert(0, "5")

        # 按钮
        btn_frame = tb.Frame(frame)
        btn_frame.pack(pady=20)

        generate_btn = tb.Button(btn_frame, text="生成用户", bootstyle="success", command=self.generate_users)
        generate_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def generate_users(self):
        """批量生成用户"""
        try:
            count = int(self.user_count.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("输入错误", "生成数量必须是正整数")
            return

        student_id_pattern = self.student_id_pattern.get()
        username_pattern = self.username_pattern.get()
        password_pattern = self.password_pattern.get()
        role = self.batch_role_var.get()

        # 生成用户数据
        users = []
        for i in range(1, count + 1):
            # 使用更安全的方式替换数字
            student_id = student_id_pattern.replace("{i}", str(i).zfill(math.floor(math.log10(count + 1)) + 1))
            username = username_pattern.replace("{i}", str(i).zfill(math.floor(math.log10(count + 1)) + 1))
            password = password_pattern.replace("{i}", str(i).zfill(math.floor(math.log10(count + 1)) + 1))
            users.append((student_id, username, password, role))

            # 保存到数据库
            db = Database()
            if not db.connection:
                return

        query = """
            INSERT INTO users (student_id, username, password, role)
            VALUES (%s, %s, %s, %s)
        """

        success_count = 0
        for user in users:
            try:
                if db.execute_query(query, user):
                    success_count += 1
            except:
                continue  # 跳过重复的用户

        # 导出为CSV
        with open('generated_users.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['学号', '用户名', '密码', '角色'])
            writer.writerows(users)

        messagebox.showinfo("完成", f"成功生成 {success_count}/{count} 个用户\n已导出到 generated_users.csv")
        self.show_query_frame()

    def show_edit_user_frame(self):
        """显示编辑用户界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        # 用户选择框
        tb.Label(frame, text="选择用户:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.user_var = tk.StringVar()
        user_combo = tb.Combobox(frame, textvariable=self.user_var, width=25)
        user_combo.grid(row=0, column=1, pady=10, padx=5)

        # 加载用户列表
        db = Database()
        if db.connection:
            users = db.execute_query("SELECT username FROM users", fetch=True)
            if users:
                user_combo['values'] = [user[0] for user in users]
                if users:
                    user_combo.current(0)

        # 用户信息表单
        tb.Label(frame, text="学号:", bootstyle="primary").grid(row=1, column=0, pady=10, padx=5, sticky='e')
        self.edit_student_id_var = tk.StringVar()
        self.edit_student_id_entry = tb.Entry(frame, textvariable=self.edit_student_id_var, width=25)
        self.edit_student_id_entry.grid(row=1, column=1, pady=10, padx=5)

        tb.Label(frame, text="用户名:", bootstyle="primary").grid(row=2, column=0, pady=10, padx=5, sticky='e')
        self.edit_username_var = tk.StringVar()
        self.edit_username_entry = tb.Entry(frame, textvariable=self.edit_username_var, width=25)
        self.edit_username_entry.grid(row=2, column=1, pady=10, padx=5)

        tb.Label(frame, text="角色:", bootstyle="primary").grid(row=3, column=0, pady=10, padx=5, sticky='e')
        self.edit_role_var = tk.StringVar()
        role_combo = tb.Combobox(frame, textvariable=self.edit_role_var, width=22)
        role_combo['values'] = ('user', 'admin', 'superadmin')
        role_combo.grid(row=3, column=1, pady=10, padx=5)

        # 加载按钮
        load_btn = tb.Button(frame, text="加载用户信息", bootstyle="info", command=self.load_user_info)
        load_btn.grid(row=4, column=0, columnspan=2, pady=10)

        # 按钮组
        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        update_btn = tb.Button(btn_frame, text="更新", bootstyle="success", command=self.update_user)
        update_btn.pack(side='left', padx=10)

        delete_btn = tb.Button(btn_frame, text="删除", bootstyle="danger", command=self.delete_user)
        delete_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def load_user_info(self):
        """加载选择的用户信息"""
        username = self.user_var.get()
        if not username:
            messagebox.showwarning("选择错误", "请选择一个用户")
            return

        db = Database()
        if not db.connection:
            return

        result = db.execute_query(
            "SELECT student_id, username, role FROM users WHERE username = %s",
            (username,),
            fetch=True
        )

        if result:
            student_id, username, role = result[0]
            self.edit_student_id_var.set(student_id)
            self.edit_username_var.set(username)
            self.edit_role_var.set(role)
        else:
            messagebox.showerror("错误", "无法加载用户信息")

    def update_user(self):
        """更新用户信息"""
        username = self.user_var.get()
        new_student_id = self.edit_student_id_var.get()
        new_username = self.edit_username_var.get()
        new_role = self.edit_role_var.get()

        if not all([username, new_student_id, new_username, new_role]):
            messagebox.showwarning("输入错误", "所有字段都必须填写")
            return

        db = Database()
        if not db.connection:
            return

        # 检查用户名是否已存在（排除当前用户）
        result = db.execute_query(
            "SELECT id FROM users WHERE username = %s AND username != %s",
            (new_username, username),
            fetch=True
        )

        if result:
            messagebox.showerror("错误", "用户名已存在")
            return

        # 检查学号是否已存在（排除当前用户）
        result = db.execute_query(
            "SELECT id FROM users WHERE student_id = %s AND username != %s",
            (new_student_id, username),
            fetch=True
        )

        if result:
            messagebox.showerror("错误", "学号已存在")
            return

        # 更新用户信息
        query = """
            UPDATE users 
            SET student_id = %s, username = %s, role = %s 
            WHERE username = %s
        """
        if db.execute_query(query, (new_student_id, new_username, new_role, username)):
            messagebox.showinfo("成功", "用户信息已更新")
            self.show_query_frame()

    def delete_user(self):
        """删除用户"""
        username = self.user_var.get()
        if not username:
            messagebox.showwarning("选择错误", "请选择一个用户")
            return

        if messagebox.askyesno("确认", f"确定要删除用户 {username} 吗？"):
            db = Database()
            if not db.connection:
                return

            if db.execute_query("DELETE FROM users WHERE username = %s", (username,)):
                messagebox.showinfo("成功", "用户已删除")
                self.show_query_frame()

    def show_change_password_frame(self):
        """显示更改密码界面"""
        self.clear_main_frame()

        frame = tb.Frame(self.main_frame)
        frame.pack(pady=20, padx=20, fill='both', expand=True)

        tb.Label(frame, text="当前密码:", bootstyle="primary").grid(row=0, column=0, pady=10, padx=5, sticky='e')
        self.current_password_entry = tb.Entry(frame, width=25, show="*")
        self.current_password_entry.grid(row=0, column=1, pady=10, padx=5)

        tb.Label(frame, text="新密码:", bootstyle="primary").grid(row=1, column=0, pady=10, padx=5, sticky='e')
        self.new_password_entry = tb.Entry(frame, width=25, show="*")
        self.new_password_entry.grid(row=1, column=1, pady=10, padx=5)

        tb.Label(frame, text="确认新密码:", bootstyle="primary").grid(row=2, column=0, pady=10, padx=5, sticky='e')
        self.confirm_password_entry = tb.Entry(frame, width=25, show="*")
        self.confirm_password_entry.grid(row=2, column=1, pady=10, padx=5)

        btn_frame = tb.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        submit_btn = tb.Button(btn_frame, text="更改密码", bootstyle="success", command=self.change_password)
        submit_btn.pack(side='left', padx=10)

        cancel_btn = tb.Button(btn_frame, text="取消", bootstyle="secondary", command=self.show_query_frame)
        cancel_btn.pack(side='left', padx=10)

    def change_password(self):
        """更改当前用户密码"""
        current_password = self.current_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not all([current_password, new_password, confirm_password]):
            messagebox.showwarning("输入错误", "所有字段都必须填写")
            return

        if new_password != confirm_password:
            messagebox.showerror("错误", "新密码和确认密码不匹配")
            return

        db = Database()
        if not db.connection:
            return

        # 验证当前密码
        result = db.execute_query(
            "SELECT id FROM users WHERE username = %s AND password = %s",
            (self.username, current_password),
            fetch=True
        )

        if not result:
            messagebox.showerror("错误", "当前密码不正确")
            return

        # 更新密码
        if db.execute_query(
                "UPDATE users SET password = %s WHERE username = %s",
                (new_password, self.username)
        ):
            messagebox.showinfo("成功", "密码已更新")
            self.show_query_frame()

    def logout(self):
        """登出系统"""
        self.destroy()
        # 重新启动应用程序
        MainWindow()

    def clear_main_frame(self):
        """清除主框架内容"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    # 创建主窗口
    app = MainWindow()
    app.mainloop()