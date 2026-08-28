import os
import pymysql
from datetime import datetime, timezone, timedelta


# ==========================================
# 🇹🇭 Timezone ประเทศไทย UTC+7
# ==========================================

tz_thai = timezone(timedelta(hours=7))


# ==========================================
# CACHE สถานะการ Initialize Database
# ==========================================

_account_db_initialized = False


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    """เชื่อมต่อ MySQL / Aiven และคืนข้อมูลแบบ Tuple"""

    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        autocommit=True,
        charset="utf8mb4",
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )


# ==========================================
# CREATE TABLE / INDEX
# ==========================================

def init_account_db():
    """
    สร้างตารางและ Index หากยังไม่มี

    เรียกตรวจสอบเพียงครั้งเดียวต่อการรัน Server
    """

    global _account_db_initialized

    if _account_db_initialized:
        return

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            # ==========================================
            # CREATE TABLE
            # ==========================================

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    category VARCHAR(100) DEFAULT 'ทั่วไป',
                    scope VARCHAR(50) DEFAULT 'personal',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_cleared INT DEFAULT 0,

                    INDEX idx_scope_created (
                        scope,
                        created_at
                    ),

                    INDEX idx_scope_type_created (
                        scope,
                        type,
                        created_at
                    ),

                    INDEX idx_scope_cleared_created (
                        scope,
                        is_cleared,
                        created_at
                    )
                )
            """)

            # ==========================================
            # ตรวจสอบ / เพิ่ม Index สำหรับ Database เดิม
            # ==========================================

            required_indexes = [
                (
                    "idx_scope_created",
                    """
                    CREATE INDEX idx_scope_created
                    ON transactions (scope, created_at)
                    """
                ),
                (
                    "idx_scope_type_created",
                    """
                    CREATE INDEX idx_scope_type_created
                    ON transactions (scope, type, created_at)
                    """
                ),
                (
                    "idx_scope_cleared_created",
                    """
                    CREATE INDEX idx_scope_cleared_created
                    ON transactions (scope, is_cleared, created_at)
                    """
                ),
            ]

            for index_name, create_sql in required_indexes:

                cursor.execute("""
                    SELECT COUNT(*)
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                    AND table_name = 'transactions'
                    AND index_name = %s
                """, (index_name,))

                index_exists = cursor.fetchone()[0]

                if not index_exists:
                    cursor.execute(create_sql)

        _account_db_initialized = True

    finally:
        conn.close()


# ==========================================
# ADD TRANSACTION
# ==========================================

def add_transaction(
    title: str,
    trans_type: str,
    amount: float,
    category: str,
    scope: str = "personal"
):
    """เพิ่มรายการรายรับ / รายจ่าย"""

    init_account_db()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            now_thai = datetime.now(
                tz_thai
            ).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO transactions (
                    title,
                    type,
                    amount,
                    category,
                    scope,
                    created_at,
                    is_cleared
                )
                VALUES (%s, %s, %s, %s, %s, %s, 0)
            """, (
                title,
                trans_type,
                amount,
                category,
                scope,
                now_thai
            ))

    finally:
        conn.close()


# ==========================================
# DELETE TRANSACTION
# ==========================================

def delete_transaction(trans_id: int):
    """ลบรายการ"""

    init_account_db()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                DELETE FROM transactions
                WHERE id = %s
            """, (trans_id,))

    finally:
        conn.close()


# ==========================================
# UPDATE TRANSACTION
# ==========================================

def update_transaction(
    trans_id: int,
    title: str,
    trans_type: str,
    amount: float,
    category: str,
    scope: str = "personal"
):
    """แก้ไขรายการ"""

    init_account_db()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                UPDATE transactions
                SET
                    title = %s,
                    type = %s,
                    amount = %s,
                    category = %s,
                    scope = %s
                WHERE id = %s
            """, (
                title,
                trans_type,
                amount,
                category,
                scope,
                trans_id
            ))

    finally:
        conn.close()


# ==========================================
# BUILD SQL CONDITION
# ==========================================

def build_account_conditions(
    selected_scope: str = "all",
    start_date: str = None,
    end_date: str = None,
):
    """
    สร้าง WHERE condition

    ใช้ created_at โดยตรง
    ไม่ใช้ DATE(created_at)
    เพื่อให้ Database ใช้ Index ได้ดีขึ้น
    """

    conditions = []
    params = []

    # ==========================================
    # PERSONAL
    # ==========================================

    if selected_scope == "personal":

        conditions.append("scope = %s")
        params.append("personal")

    # ==========================================
    # WORK
    # ==========================================

    elif selected_scope == "work":

        conditions.append("scope = %s")
        params.append("work")

        conditions.append(
            "(is_cleared IS NULL OR is_cleared = 0)"
        )

    # ==========================================
    # ALL
    # ==========================================

    else:

        conditions.append(
            "(is_cleared IS NULL OR is_cleared = 0)"
        )

    # ==========================================
    # START DATE
    # ==========================================

    if start_date:

        conditions.append(
            "created_at >= %s"
        )

        params.append(
            f"{start_date} 00:00:00"
        )

    # ==========================================
    # END DATE
    # ==========================================

    if end_date:

        conditions.append(
            "created_at < DATE_ADD(%s, INTERVAL 1 DAY)"
        )

        params.append(end_date)

    where_clause = ""

    if conditions:

        where_clause = (
            " WHERE " +
            " AND ".join(conditions)
        )

    return where_clause, params


# ==========================================
# GET ACCOUNT SUMMARY
# ==========================================

def get_account_summary(
    selected_scope: str = "all",
    start_date: str = None,
    end_date: str = None
):
    """
    ดึงข้อมูลสรุปรายรับ-รายจ่าย

    ลดจำนวน Query:
    1. Summary Income + Expense
    2. Transaction History
    3. Expense Chart
    4. Work Current Income เฉพาะหน้า Work
    """

    init_account_db()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            # ==========================================
            # BUILD WHERE
            # ==========================================

            where_clause, params = build_account_conditions(
                selected_scope,
                start_date,
                end_date
            )

            # ==========================================
            # 1. สรุปรายรับ + รายจ่าย
            # ==========================================

            summary_sql = f"""
                SELECT
                    IFNULL(
                        SUM(
                            CASE
                                WHEN type = 'income'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,

                    IFNULL(
                        SUM(
                            CASE
                                WHEN type = 'expense'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions
                {where_clause}
            """

            cursor.execute(
                summary_sql,
                params
            )

            summary_row = cursor.fetchone()

            income = float(
                summary_row[0] or 0
            )

            expense = float(
                summary_row[1] or 0
            )

            # ==========================================
            # 2. ประวัติรายการ
            # ==========================================

            transaction_sql = f"""
                SELECT
                    id,
                    title,
                    type,
                    amount,
                    category,
                    created_at,
                    scope
                FROM transactions
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT 20
            """

            cursor.execute(
                transaction_sql,
                params
            )

            rows = cursor.fetchall()

            # ==========================================
            # 3. กราฟรายจ่าย
            # ==========================================

            if where_clause:
                chart_where_clause = (
                    where_clause +
                    " AND type = %s"
                )
            else:
                chart_where_clause = (
                    " WHERE type = %s"
                )

            chart_sql = f"""
                SELECT
                    category,
                    SUM(amount)
                FROM transactions
                {chart_where_clause}
                GROUP BY category
                ORDER BY SUM(amount) DESC
            """

            cursor.execute(
                chart_sql,
                params + ["expense"]
            )

            cat_rows = cursor.fetchall()

            # ==========================================
            # 4. Work Current Income
            # เรียกเฉพาะหน้า Work
            # ==========================================

            work_current_income = None

            if selected_scope == "work":

                cursor.execute("""
                    SELECT
                        IFNULL(SUM(amount), 0)
                    FROM transactions
                    WHERE type = 'income'
                    AND scope = 'work'
                    AND (is_cleared IS NULL OR is_cleared = 0)
                    AND title NOT LIKE 'สรุปยอดจบงาน%'
                """)

                work_result = cursor.fetchone()

                work_current_income = float(
                    work_result[0] or 0
                )

            # ==========================================
            # RETURN
            # ==========================================

            return {
                "income": income,
                "expense": expense,
                "balance": income - expense,

                "transactions": rows,

                "chart_labels": [
                    row[0]
                    for row in cat_rows
                ],

                "chart_data": [
                    float(row[1])
                    for row in cat_rows
                ],

                "selected_scope": selected_scope,

                # ใช้เพื่อลดการเปิด DB Connection เพิ่ม
                "work_current_income": work_current_income
            }

    finally:
        conn.close()


# ==========================================
# GET WORK CURRENT INCOME
# ==========================================

def get_work_income_summary():
    """
    ดึงยอดรายรับงานของรอบปัจจุบัน

    คงฟังก์ชันนี้ไว้เพื่อรองรับส่วนอื่นของระบบ
    """

    init_account_db()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    IFNULL(SUM(amount), 0)
                FROM transactions
                WHERE type = 'income'
                AND scope = 'work'
                AND (is_cleared IS NULL OR is_cleared = 0)
                AND title NOT LIKE 'สรุปยอดจบงาน%'
            """)

            result = cursor.fetchone()

            return float(
                result[0] or 0
            )

    finally:
        conn.close()


# ==========================================
# CLEAR WORK INCOME
# ==========================================

def clear_work_income():
    """
    เคลียร์เฉพาะรายรับของ Work

    - รายการเดิมถูกตั้ง is_cleared = 1
    - สร้างรายการสรุปยอดจบงานใหม่
    - Personal จะไม่ถูกกระทบ
    """

    init_account_db()

    conn = get_db_connection()

    try:
        # ปิด autocommit เฉพาะขั้นตอนนี้
        conn.begin()

        with conn.cursor() as cursor:

            # ==========================================
            # 1. คำนวณรายรับ Work รอบปัจจุบัน
            # ==========================================

            cursor.execute("""
                SELECT IFNULL(SUM(amount), 0)
                FROM transactions
                WHERE type = %s
                AND scope = %s
                AND (is_cleared IS NULL OR is_cleared = 0)
                AND title NOT LIKE %s
            """, (
                "income",
                "work",
                "สรุปยอดจบงาน%"
            ))

            result = cursor.fetchone()

            total_income = float(
                result[0] or 0
            )

            # ==========================================
            # 2. ถ้ามียอด ให้เคลียร์
            # ==========================================

            if total_income > 0:

                cursor.execute("""
                    UPDATE transactions
                    SET is_cleared = 1
                    WHERE type = %s
                    AND scope = %s
                    AND (is_cleared IS NULL OR is_cleared = 0)
                    AND title NOT LIKE %s
                """, (
                    "income",
                    "work",
                    "สรุปยอดจบงาน%"
                ))

                # ==========================================
                # 3. บันทึกสรุปยอด
                # ==========================================

                now_thai = datetime.now(
                    tz_thai
                ).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                summary_title = (
                    f"สรุปยอดจบงาน / "
                    f"เคลียร์ยอดรายรับ "
                    f"(รวม ฿{total_income:,.2f})"
                )

                cursor.execute("""
                    INSERT INTO transactions (
                        title,
                        type,
                        amount,
                        category,
                        scope,
                        created_at,
                        is_cleared
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        0
                    )
                """, (
                    summary_title,
                    "income",
                    total_income,
                    "ขายสินค้า",
                    "work",
                    now_thai
                ))

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()