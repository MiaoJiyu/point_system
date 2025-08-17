import mysql.connector

if __name__ == "__main__":
    # 创建初始数据库结构（仅需运行一次）
    def initialize_database():
        try:
            conn = mysql.connector.connect(
                host='124.222.211.202',
                user='score',
                password='Jiyu_42206180'
            )
            cursor = conn.cursor()

            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS point_system_db")
            cursor.execute("USE point_system_db")

            # 创建用户表（增加student_id字段）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(50) NOT NULL,
                    role ENUM('user', 'point_admin', 'super_admin') NOT NULL DEFAULT 'user',
                    student_id VARCHAR(20)
                )
            """)

            # 创建操作记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    operation_type ENUM('加分', '减分') NOT NULL,
                    points INT NOT NULL,
                    reason VARCHAR(100) NOT NULL,
                    operator VARCHAR(50) NOT NULL,
                    valid TINYINT DEFAULT 1,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 添加测试用户
            cursor.execute("""
                INSERT IGNORE INTO users (username, password, role, student_id) 
                VALUES 
                ('Jiyu', 'Jiyu_42206180', 'superadmin', NULL)
            """)

            # 添加测试记录
            #cursor.execute("""
                # INSERT IGNORE INTO operations
                # (student_id, operation_type, points, reason, operator, valid)
                # VALUES
                # ('S2023001', '加分', 5, '课堂表现', 'pointadmin', 1),
                # ('S2023002', '加分', 3, '作业优秀', 'pointadmin', 1),
                # ('S2023001', '减分', 2, '迟到', 'pointadmin', 0),
                # ('S2023003', '加分', 10, '竞赛获奖', 'admin', 1)
            # """)

            conn.commit()
            cursor.close()
            conn.close()
            print("数据库初始化完成")
        except mysql.connector.Error as err:
            print(f"数据库初始化失败: {err}")


    # 初始化数据库（第一次运行时取消注释）
    initialize_database()