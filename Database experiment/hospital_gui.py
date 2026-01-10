import sys
import pyodbc
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFormLayout,
    QGroupBox, QMessageBox, QSpinBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QDesktopWidget
)
#PyQt5 库自带的界面开发组件，包含许多封装好的类
#QtWidgets 是做按钮、表格这些界面元素的，
#QtCore 是控制日期、对齐这些属性的，
#QtGui 是做字体、背景图这些美化的，直接调用这些组件能快速做界面，不用自己从零写。
#还有设置按钮，标签，设置背景图片等其他功能封装。

# 数据库连接
#用pyodbc库连接SQL Server，配置了驱动、服务器、数据库名，用Windows身份验证
#主窗口初始化时调用self.db = get_db()，如果连接失败会弹窗提示，且所有表操作按钮会禁用。
def get_db():
    try:
        conn_str = (
            r'DRIVER={ODBC Driver 17 for SQL Server};'
            r'SERVER=.\MYSQL;'
            r'DATABASE=hospital;'
            r'Trusted_Connection=yes;'
        )
        conn = pyodbc.connect(conn_str)#发起连接
        return conn
    except Exception as e:
        QMessageBox.critical(None, "数据库连接失败", f"错误：{str(e)}")
        return None

# 子窗口类展示单表功能显示+多表关联查询处理+增删改查
class TableWin(QMainWindow):
    # 窗口界面与控件设置
    def __init__(self, table_name, db_conn):
        super().__init__()#super调用父类，让子窗口拥有QMainWindow的所有基础功能
        self.t_name = table_name  #把打开子窗口时传入的 表名存为实例变量
        self.db = db_conn  #数据库连接
        self.cur = self.db.cursor() if self.db else None  #游标,类似数据库通道
        #多表关联配置
        #在TableWin类的join_config字典里配置了关联SQL和表头，
        #加载数据时load_all()判断表名是否在join_config里，是的话就执行关联查询。
        #关联查询模板
        self.join_config = {
            "医生表": (# 查doctor表+department表，通过部门编号dpno关联
                "SELECT d.dno, d.dname, d.duty, d.dsex, d.dage, d.dpno, de.dpname, de.dpadr FROM doctor d INNER JOIN department de ON d.dpno = de.dpno",
                ["医生工号", "医生姓名", "职务", "性别", "年龄", "部门编号", "所属科室", "科室地址"]  # 新增“部门编号”列
            ),
            "患者表": (# 查patient表+doctor表+department表+room表，多表关联
                "SELECT p.pno, p.pname, p.psex, p.page, p.dno, d.dname, d.dpno, de.dpname, p.rno, r.radr, p.illness FROM patient p INNER JOIN doctor d ON p.dno = d.dno INNER JOIN department de ON d.dpno = de.dpno LEFT JOIN room r ON p.rno = r.rno",
                ["患者编号", "患者姓名", "性别", "年龄", "主治医师编号", "主治医师", "部门编号", "所属科室",
                 "所属病房号", "房间地址", "疾病种类"]
            )
        }

        #子窗口设置包括标题，大小，几何信息，获取电脑中心并将窗口居中
        self.setWindowTitle(f"{self.t_name} - 操作界面")
        self.resize(1600, 900)  # 宽度1600，避免列挤压
        win_geo = self.frameGeometry()
        scr_center = QDesktopWidget().availableGeometry().center()
        win_geo.moveCenter(scr_center)
        self.move(win_geo.topLeft())

        #UI美化，结合AI设计
        #QMainWindow, QWidget {background-color: #f5f7fa;}给子窗口的背景设为浅灰蓝色
        #QGroupBox 分组框标题字体18号加粗深灰色，分组框上边距内部填充，浅灰色设圆角，框背景90%透明度白色
        #QPushButton按钮默认是蓝色，边角圆8像素
        #QPushButton:hover鼠标移到按钮上时背景色变深，按钮轻微放大
        #QLabel {font-size: 16px; color: #34495e;}标签字体16号深灰色
        #QLineEdit, QSpinBox, QDateEdit, QComboBox 输入框/数字框/日期框/下拉框
        #QTableWidget {border-radius: 8px;}结果展示表格边角圆角
        #QHeaderView::section 表格表头背景蓝色、文字白色加粗，内部填充
        #QTableWidget::item{padding: 8px;}表格单元格内部填充
        #QTableWidget::item:selected 表格选中的单元格/行，背景浅天蓝色文字深灰色
        self.setStyleSheet("""
            QMainWindow, QWidget {background-color: #f5f7fa;}
            QGroupBox {
                font-size: 18px; font-weight: bold; color: #2c3e50;
                margin-top: 20px; padding: 20px; border: 2px solid #e1e8ed;
                border-radius: 10px; background-color: rgba(255,255,255,0.9);
            }
            QPushButton {
                font-size: 16px; padding: 12px 25px; margin: 0 10px;
                background-color: #3498db; color: white; border: none; border-radius: 8px;
            }
            QPushButton:hover {background-color: #2980b9; transform: scale(1.03);}
            QLabel {font-size: 16px; color: #34495e;}
            QLineEdit, QSpinBox, QDateEdit, QComboBox {
                font-size: 16px; padding: 10px; border: 1px solid #bdc3c7; border-radius: 6px;
                background-color: white;
            }
            QTableWidget {
                font-size: 16px; border: 1px solid #e1e8ed; border-radius: 8px;
                background-color: rgba(255,255,255,0.9);
            }
            QHeaderView::section {
                background-color: #3498db; color: white; font-weight: bold;
                padding: 12px; border-radius: 4px;
            }
            QTableWidget::item {padding: 8px;}
            QTableWidget::item:selected {background-color: #e3f2fd; color: #2c3e50;}
        """)

        #中心部件是子窗口的 内容容器，所有按钮、表格、输入框都要装到这个容器里，再把容器放到窗口正中间
        #相当于word里设置页边距，行距等
        cen_wid = QWidget()
        self.setCentralWidget(cen_wid)
        main_layout = QVBoxLayout(cen_wid)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        #按钮区，添加按钮并命名
        btn_layout = QHBoxLayout()# 水平布局
        self.add_btn = QPushButton("新增")
        self.query_btn = QPushButton("查询")
        self.upd_btn = QPushButton("修改")
        self.del_btn = QPushButton("删除")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.query_btn)
        btn_layout.addWidget(self.upd_btn)
        btn_layout.addWidget(self.del_btn)
        main_layout.addLayout(btn_layout)

        #查询条件区，添加查询框，设置输入的查询框并内置提示
        query_layout = QHBoxLayout()
        self.fld_label = QLabel("查询字段：")
        self.fld_combo = QComboBox()  # 字段映射下拉框
        self.val_label = QLabel("查询值：")
        self.val_txt = QLineEdit()  # 查询值输入框
        self.val_txt.setPlaceholderText("输入内容，留空查全表")
        query_layout.addWidget(self.fld_label)
        query_layout.addWidget(self.fld_combo)
        query_layout.addWidget(self.val_label)
        query_layout.addWidget(self.val_txt)
        main_layout.addLayout(query_layout)

        #表单输入区，创建输入控件的容器并基本布局
        self.form_group = QGroupBox("数据输入")
        form_wid = QWidget()
        self.form_layout = QFormLayout(form_wid)
        self.form_layout.setSpacing(15)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        self.wid_dict = {}  # 输入控件字典存输入控件，比如把“患者编号”输入框存起来，后续取值用
        self.fld_map = {}  # 字段映射存“中文字段名→数据库字段名”的映射
        self.create_wids()
        #把当前表的字段名填充到查询下拉框里
        if self.fld_map:
            self.fld_combo.addItems(list(self.fld_map.keys()))
        self.form_group.setLayout(QVBoxLayout())
        self.form_group.layout().addWidget(form_wid)
        #把整个数据输入分组框加到主布局里
        main_layout.addWidget(self.form_group)

        # 结果表格，规定结果输出位置
        self.res_table = QTableWidget()
        self.res_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.res_table)

        # 绑定事件，把按钮点击和功能接口联系起来
        self.add_btn.clicked.connect(self.add_data)
        self.query_btn.clicked.connect(self.query_data)
        self.upd_btn.clicked.connect(self.upd_data)
        self.del_btn.clicked.connect(self.del_data)

        # 打开时加载全表
        self.load_all()

    #获取字段映射
    #提前定义的字段映射，数据库里的英文字段转成能看懂的中文字段显示，
    #输入的中文内容，也能通过这个映射对应到数据库的英文字段里
    def get_fld_map(self):
        fld_map = {
            "科室表": {"部门名称": "dpname", "部门编号": "dpno", "部门地址": "dpadr", "部门电话": "dptel"},
            "医生表": {"医生工号": "dno", "医生姓名": "dname", "职务": "duty", "性别": "dsex", "年龄": "dage",
                       "部门编号": "dpno"},
            "患者表": {"患者编号": "pno", "患者姓名": "pname", "性别": "psex", "年龄": "page", "主治医师编号": "dno",
                       "所属病房号": "rno", "疾病种类": "illness", "入院日期": "startdate",
                       "预计出院日期": "predictenddate"},
            "药品表": {"药品编号": "dgno", "药品名称": "dgname", "生产厂家": "dgpro", "库存量": "dgnum",
                       "价格": "dgprice"},
            "病房表": {"病房编号": "rno", "病房地址": "radr", "所属部门编号": "dpno"},
            "患者用药表": {"药品编号": "dgno", "患者编号": "pno", "用药数量": "num"}
        }
        if self.t_name not in fld_map:#映射没对应
            QMessageBox.warning(self, "提示", f"未配置{self.t_name}字段！")
            return None
        return fld_map[self.t_name]

    #打开不同表的子窗口时，自动创建对应表的输入控件
    def create_wids(self):
        #如果重复打开同一个表，先删掉之前的输入控件，避免界面上出现重复的输入框
        for w in self.wid_dict.values():
            w.deleteLater()# 删除之前创建的输入控件
        self.wid_dict.clear()# 清空控件字典
        self.fld_map = self.get_fld_map()#添加新表映射
        if not self.fld_map:
            return

        col_wid = QWidget()#设置左右列的布局
        col_layout = QHBoxLayout(col_wid)
        left_layout = QFormLayout()
        right_layout = QFormLayout()
        cn_names = list(self.fld_map.keys())#取当前表的所有中文字段

        for i, cn in enumerate(cn_names):#遍历所有中文字段
            db_fld = self.fld_map[cn]#取对应的数据库字段，按字段名称判断，创建不同类型的输入控件
            if "性别" in cn:#性别创建特殊的下拉框选择男女
                w = QComboBox()
                w.addItems(["男", "女"])
            elif "日期" in cn: #日期字段用日期选择框，固定年月日格式字段
                w = QDateEdit(QDate.currentDate())
                w.setDisplayFormat("yyyy-MM-dd")
            elif "年龄" in cn or "数量" in cn or "价格" in cn: #数字字段用数字框
                w = QSpinBox()
                w.setRange(0, 999)
            else:
                w = QLineEdit()
            self.wid_dict[db_fld] = w #把创建好的控件存到字典里后续取值用
            #分左右列，偶数左列，奇数右列
            if i % 2 == 0:
                left_layout.addRow(QLabel(f"{cn}："), w)
            else:
                right_layout.addRow(QLabel(f"{cn}："), w)

        col_layout.addLayout(left_layout)
        col_layout.addLayout(right_layout)
        self.form_layout.addRow(col_wid) #把整个左右列布局加到输入区的表单布局里

    #加载全表数据，打开表的子窗口时，自动从数据库查数据并显示到表格里
    def load_all(self):
        if not self.cur or not self.fld_map:#前置校验，检查表名与映射
            return
        real_tname = self.get_real_tname()
        #判断当前表是否配置了多表关联
        if self.t_name in self.join_config:
            #使用多表关联SQL和表头
            join_sql, cn_names = self.join_config[self.t_name]
            sql = join_sql
        else:
            #未配置关联，使用原单表逻辑
            db_flds = list(self.fld_map.values())
            cn_names = list(self.fld_map.keys())
            sql = f"SELECT * FROM {real_tname}"

        try:
            self.cur.execute(sql) #执行SQL语句
            res = self.cur.fetchall()
            #清空表格旧数据，设置列数和表头
            self.res_table.setRowCount(0)
            self.res_table.setColumnCount(len(cn_names))
            self.res_table.setHorizontalHeaderLabels(cn_names)

            #逐行逐列填充数据到表格
            for row_idx, row in enumerate(res):
                self.res_table.insertRow(row_idx)
                for col_idx, val in enumerate(row):
                    #特殊处理性别：数据库存1/0，显示成男/女
                    if col_idx < len(cn_names) and "性别" in cn_names[col_idx]:
                        show_val = "男" if val == 1 else "女"
                    else:
                        show_val = str(val) if val is not None else ""
                    #把值放到表格单元格里
                    self.res_table.setItem(row_idx, col_idx, QTableWidgetItem(show_val))
        except Exception as e:#异常处理
            QMessageBox.warning(self, "加载失败", f"错误：{str(e)}")



    # 此前部分均属于页面设置和界面初始化，从这里开始进入增删改查

    #新增数据，重要功能
    def add_data(self):
        if not self.cur or not self.fld_map:# 基础校验，确认连接
            QMessageBox.warning(self, "提示", "数据库未连接！")
            return
        #患者表处理
        if self.t_name == "患者表":
            doc_no = self.wid_dict["dno"].text().strip()
            if doc_no:  # 仅当填写了主治医师编号时校验是否存在
                self.cur.execute("SELECT COUNT(*) FROM doctor WHERE dno = ?", (doc_no,))
                count = self.cur.fetchone()[0]
                if count == 0:
                    QMessageBox.warning(self, "提示",
                                        f"主治医师编号【{doc_no}】不存在！请先在医生表新增该医生，再添加患者。")
                    return

        #患者用药表处理
        if self.t_name == "患者用药表":
            dgno = self.wid_dict["dgno"].text().strip()
            pno = self.wid_dict["pno"].text().strip()
            if not dgno or not pno: # 联合主键检验，主体完整性约束
                QMessageBox.warning(self, "提示", "药品编号和患者编号不能为空！")
                return
            #查询该组合是否已存在
            self.cur.execute("SELECT COUNT(*) FROM PD WHERE dgno = ? AND pno = ?", (dgno, pno))
            count = self.cur.fetchone()[0]
            if count > 0:
                QMessageBox.warning(self, "提示",
                                    f"该患者（{pno}）已使用过该药品（{dgno}），无法重复新增！请修改已有记录的用药数量。")
                return

        vals = []  # 存最终要插入数据库的值
        db_flds = list(self.fld_map.values())
        for f in db_flds:
            w = self.wid_dict[f]  # 取对应的输入控件，对性别，日期，数字特殊处理
            if isinstance(w, QComboBox) and "性别" in [k for k, v in self.fld_map.items() if v == f][0]:
                val = 1 if w.currentText() == "男" else 0
            elif isinstance(w, QDateEdit):
                val = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, QSpinBox):
                val = w.value()
            else:
                val = w.text().strip()
                #非主键字段允许为空
                cn = [k for k, v in self.fld_map.items() if v == f][0]
                #仅主键字段强制非空
                if not val and (self.t_name != "患者用药表" and f == db_flds[0]):
                    QMessageBox.warning(self, "提示", f"主键字段【{cn}】不能为空！")
                    return
            vals.append(val)

        real_tname = self.get_real_tname()  # 转sql中文表名转英文表名
        ph = ", ".join(["?"] * len(db_flds))  # 生成占位符，把输入值和SQL语句分离
        # 执行sql insert命令插入新元组
        sql = f"INSERT INTO {real_tname} ({', '.join(db_flds)}) VALUES ({ph})"
        try:
            self.cur.execute(sql, vals)
            self.db.commit()  # 提交事务
            QMessageBox.information(self, "成功", "新增数据成功！")
            self.clear_inputs()
            self.load_all()  # 重新调用界面刷新表格，显示新增后的数据
        except Exception as e:
            self.db.rollback()  # 触发回滚则失败
            QMessageBox.warning(self, "失败", f"错误：{str(e)}")

    # 查询数据，重要功能
    def query_data(self):
        if not self.cur or not self.fld_map:  # 连接校验
            QMessageBox.warning(self, "提示", "数据库未连接！")
            return
        # 获取选择的字段
        sel_cn = self.fld_combo.currentText()
        if not sel_cn:
            QMessageBox.warning(self, "提示", "请选择查询字段！")
            return
        # 转数据库英文字段
        target_fld = None
        for cn, db_f in self.fld_map.items():
            if cn == sel_cn:
                target_fld = db_f
                break
        if not target_fld:
            QMessageBox.warning(self, "提示", f"字段【{sel_cn}】不存在！")
            return
        # 取用户输入的查询值
        q_val = self.val_txt.text().strip()
        if not q_val:  # 先判断留空，直接查全表
            self.load_all()
            return

        # 性别字段格式转换
        if sel_cn == "性别":
            if q_val == "男":
                q_val = "1"
            elif q_val == "女":
                q_val = "0"
            else:
                QMessageBox.information(self, "提示", "性别查询请输入“男”或“女”！")
                return

        # 中文表名转英文
        real_tname = self.get_real_tname()
        # 判断是否为关联表，拼接对应查询SQL，多表关联时，字段要加表别名
        if self.t_name in self.join_config:
            join_sql, cn_names = self.join_config[self.t_name]
            if self.t_name == "医生表":
                sql = f"{join_sql} WHERE d.{target_fld} LIKE ?"
            elif self.t_name == "患者表":
                sql = f"{join_sql} WHERE p.{target_fld} LIKE ?"
            else:
                sql = f"{join_sql} WHERE {target_fld} LIKE ?"
        else:  # 单表查询直接拼接
            cn_names = list(self.fld_map.keys())
            sql = f"SELECT * FROM {real_tname} WHERE {target_fld} LIKE ?"

        q_param = f"%{q_val}%"  # %模糊查询的通配符
        try:
            self.cur.execute(sql, (q_param,))
            res = self.cur.fetchall()  # 获取查询结果
            # 逻辑与load_all()相同，只是展示的是部分结果
            self.res_table.setRowCount(0)
            self.res_table.setColumnCount(len(cn_names))
            self.res_table.setHorizontalHeaderLabels(cn_names)
            for row_idx, row in enumerate(res):
                self.res_table.insertRow(row_idx)
                for col_idx, val in enumerate(row):
                    # 性别转中文
                    if col_idx < len(cn_names) and "性别" in cn_names[col_idx]:
                        show_val = "男" if val == 1 else "女"
                    else:
                        show_val = str(val) if val is not None else ""
                    self.res_table.setItem(row_idx, col_idx, QTableWidgetItem(show_val))
            if not res:
                QMessageBox.information(self, "提示", f"未找到【{sel_cn}包含{q_val}】的数据！")
        except Exception as e:
            QMessageBox.warning(self, "查询失败", f"错误：{str(e)}")

    # 修改数据，重要功能
    def upd_data(self):
        if not self.cur or not self.fld_map:  # 连接校验
            QMessageBox.warning(self, "提示", "数据库未连接！")
            return
        # 获取用户选择的查询字段
        db_flds = list(self.fld_map.values())
        cn_names = list(self.fld_map.keys())

        # 区分联合主键（PD表）和单主键
        if self.t_name == "患者用药表":  # 如果是这个表就是联合主键，否则为单主键
            # PD表：联合主键（dgno + pno）
            main_flds = ["dgno", "pno"]
            non_main_flds = [f for f in db_flds if f not in main_flds]

            # 1. 获取并校验联合主键值
            main_vals = {}
            for fld in main_flds:
                wid = self.wid_dict.get(fld)  # 取输入的主键值控件
                if not wid:
                    QMessageBox.warning(self, "提示", f"未找到字段【{fld}】的输入控件！")
                    return
                val = wid.text().strip() if isinstance(wid, QLineEdit) else str(wid.value())  # 取输入的主键值
                if not val:
                    QMessageBox.warning(self, "提示", f"请输入【{[k for k, v in self.fld_map.items() if v == fld][0]}】！")
                    return
                main_vals[fld] = val  # 把取到的主键值存到字典里

            # 2. 校验联合主键对应的记录是否存在
            self.cur.execute("SELECT COUNT(*) FROM PD WHERE dgno = ? AND pno = ?",
                             (main_vals["dgno"], main_vals["pno"]))
            if self.cur.fetchone()[0] == 0:
                QMessageBox.warning(self, "提示", "该药品+患者的组合不存在，无法修改！")
                return
        else:
            # 其他表：单主键逻辑
            main_fld = db_flds[0]
            main_cn = cn_names[0]
            main_wid = self.wid_dict[main_fld]

            # 1. 获取并校验单主键值
            if isinstance(main_wid, QDateEdit):
                main_val = main_wid.date().toString("yyyy-MM-dd")
            elif isinstance(main_wid, QSpinBox):
                main_val = main_wid.value()
            elif isinstance(main_wid, QComboBox):
                main_val = 1 if main_wid.currentText() == "男" else 0
            else:
                main_val = main_wid.text().strip()
                if not main_val:
                    QMessageBox.warning(self, "提示", f"请输入主键【{main_cn}】！")
                    return

            # 2. 校验单主键对应的记录是否存在
            self.cur.execute(f"SELECT COUNT(*) FROM {self.get_real_tname()} WHERE {main_fld} = ?", (main_val,))
            if self.cur.fetchone()[0] == 0:
                QMessageBox.warning(self, "提示", "主键对应的记录不存在，无法修改！")
                return

            non_main_flds = db_flds[1:]  # 筛选非主键字段：除了第一个字段的所有字段

        # 3. 收集非主键字段的修改值
        upd_list = []  # 存要修改的字段
        upd_vals = []  # 存要修改的字段值
        for f in non_main_flds:
            cn = [k for k, v in self.fld_map.items() if v == f][0]
            w = self.wid_dict[f]  # 对应的输入控件

            if isinstance(w, QComboBox) and "性别" in cn:
                val = 1 if w.currentText() == "男" else 0
            elif isinstance(w, QDateEdit):
                val = w.date().toString("yyyy-MM-dd")
            elif isinstance(w, QSpinBox):
                val = w.value()
            else:
                val = w.text().strip()
                if not val:
                    continue  # 空值不修改

            upd_list.append(f"{f} = ?")  # 拼接“字段=?”，用户填了哪些字段，就只改哪些字段
            upd_vals.append(val)  # 收集对应的值

        if not upd_list:
            QMessageBox.warning(self, "提示", "请输入要修改的字段！")
            return

        # 4. 构建并执行修改SQL
        real_tname = self.get_real_tname()
        if self.t_name == "患者用药表":
            # 联合主键的UPDATE语句
            sql = f"UPDATE {real_tname} SET {', '.join(upd_list)} WHERE dgno = ? AND pno = ?"
            upd_vals.append(main_vals["dgno"])  # 追加联合主键值
            upd_vals.append(main_vals["pno"])
        else:
            # 单主键的UPDATE语句
            sql = f"UPDATE {real_tname} SET {', '.join(upd_list)} WHERE {main_fld} = ?"
            upd_vals.append(main_val)  # 追加单主键值

        try:
            self.cur.execute(sql, upd_vals)
            self.db.commit()  # 提交修改
            QMessageBox.information(self, "成功", f"修改成功！影响行数：{self.cur.rowcount}")
            self.clear_inputs()
            self.load_all()  # 刷新表格
        except Exception as e:
            self.db.rollback()  # 失败回滚
            QMessageBox.warning(self, "失败", f"错误：{str(e)}")

    # 删除数据，重要功能
    def del_data(self):
        if not self.cur or not self.fld_map:   # 连接校验
            QMessageBox.warning(self, "提示", "数据库未连接！")
            return
        db_flds = list(self.fld_map.values())  # 数据库字段列表
        cn_names = list(self.fld_map.keys())  # 中文字段列表

        # 科室表删除前校验关联数据
        if self.t_name == "科室表":
            dept_no = self.wid_dict["dpno"].text().strip()  # 取部门编号
            if not dept_no:
                QMessageBox.warning(self, "提示", "请输入部门编号！")
                return
            # 查询关联的医生和病房
            self.cur.execute("SELECT COUNT(*) FROM doctor WHERE dpno = ?", (dept_no,))
            doc_count = self.cur.fetchone()[0]
            self.cur.execute("SELECT COUNT(*) FROM room WHERE dpno = ?", (dept_no,))
            room_count = self.cur.fetchone()[0]
            if doc_count > 0 or room_count > 0:  # 有关联数据就禁止删除
                QMessageBox.warning(self, "提示", f"该科室关联了{doc_count}名医生、{room_count}个病房，无法删除！")
                return

        # 区分联合主键（PD表）和单主键（其他表）
        if self.t_name == "患者用药表":
            # PD表：联合主键（dgno+pno）
            dgno = self.wid_dict["dgno"].text().strip()
            pno = self.wid_dict["pno"].text().strip()
            if not dgno or not pno:  # 主键完整性校验
                QMessageBox.warning(self, "提示", "药品编号和患者编号不能为空！")
                return
            # 确认删除提示
            reply = QMessageBox.question(self, "确认", f"确定删除【药品编号={dgno}，患者编号={pno}】的记录？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            # 准备删除delete，放入到删除的变量中
            sql = "DELETE FROM PD WHERE dgno = ? AND pno = ?"
            params = (dgno, pno)
        else:
            # 其他表：单主键逻辑
            main_fld = db_flds[0]  # 取主键字段，即第一个字段
            main_cn = cn_names[0]  # 主键中文字段
            main_wid = self.wid_dict[main_fld]

            # 按控件类型取值，与修改和新增的逻辑一致
            if isinstance(main_wid, QDateEdit):
                main_val = main_wid.date().toString("yyyy-MM-dd")
            elif isinstance(main_wid, QSpinBox):
                main_val = main_wid.value()
            elif isinstance(main_wid, QComboBox):
                main_val = 1 if main_wid.currentText() == "男" else 0
            else:
                main_val = main_wid.text().strip()
                if not main_val:
                    QMessageBox.warning(self, "提示", f"请输入主键【{main_cn}】！")
                    return

            # 确认删除
            reply = QMessageBox.question(self, "确认", f"确定删除【{main_cn}={main_val}】的数据？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            # 准备删除delete，放入到删除的变量中
            real_tname = self.get_real_tname()
            sql = f"DELETE FROM {real_tname} WHERE {main_fld} = ?"
            params = (main_val,)

        try:
            self.cur.execute(sql, params)  # 执行删除SQL
            self.db.commit()  # 提交删除
            QMessageBox.information(self, "成功", f"删除成功！影响行数：{self.cur.rowcount}")
            self.clear_inputs()
            self.load_all()  # 刷新表格
        except Exception as e:
            self.db.rollback()  # 事务回滚
            QMessageBox.warning(self, "失败", f"错误：{str(e)}")

    # 增删改查完成，下面是增删改查用到的通用功能函数

    # 获取真实表名
    def get_real_tname(self):
        #  定义中文英文的映射字典
        name_map = {
            "科室表": "department",
            "医生表": "doctor",
            "患者表": "patient",
            "药品表": "drug",
            "病房表": "room",
            "患者用药表": "PD"
        }
        #  按当前表名取对应的英文表名，取不到就返回原表名
        return name_map.get(self.t_name, self.t_name)

    # 清空输入框函数
    def clear_inputs(self):
        for f, w in self.wid_dict.items():  # 遍历所有输入控件
            if isinstance(w, QLineEdit):  # 按控件类型清空或恢复默认值
                w.clear()
            elif isinstance(w, QDateEdit):
                w.setDate(QDate.currentDate())
            elif isinstance(w, QSpinBox):
                w.setValue(0)
            elif isinstance(w, QComboBox):
                w.setCurrentIndex(0)
        self.val_txt.clear()  # 清空查询值输入框

# 主窗口搭建，主窗口和子窗口逻辑上是一样的
class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        # 窗口大小+居中
        self.setWindowTitle("医院住院信息管理系统")  # 主菜单标题
        self.resize(1000, 800)  # 大小
        win_geo = self.frameGeometry()  # 定位屏幕中心
        scr_center = QDesktopWidget().availableGeometry().center()
        win_geo.moveCenter(scr_center)  # 定位视窗中心
        self.move(win_geo.topLeft())    # 让两中心重合，即放到屏幕中间

        # 设置背景图
        self.set_bg("hospital_bg.jpg")

        # 中心透明部件，设置透明背景与内间距
        cen_wid = QWidget()
        cen_wid.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(cen_wid)
        main_layout = QVBoxLayout(cen_wid)
        main_layout.setSpacing(50)
        main_layout.setContentsMargins(60, 60, 60, 60)

        # 标题
        title = QLabel("医院住院信息管理系统")
        title.setObjectName("title")   # 给标签命名，方便精准设置样式
        title.setStyleSheet("QLabel#title {font-size: 36px; font-weight: bold; color: #333; padding-bottom: 20px;}")
        main_layout.addWidget(title, alignment=Qt.AlignCenter)  # 居中

        # 表按钮区，左右两列
        btn_layout = QHBoxLayout()
        left_btn = QVBoxLayout()
        right_btn = QVBoxLayout()
        left_btn.setSpacing(25)
        right_btn.setSpacing(25)
        t_list = ["科室表", "医生表", "患者表", "药品表", "病房表", "患者用药表"]
        for i, t in enumerate(t_list):
            btn = QPushButton(t)
            # 按钮样式美化：绿色背景、圆角、hover放大，参考AI
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 18px; padding: 20px 30px; min-width: 200px; min-height: 70px;
                    background-color: #2ecc71; color: white; border: none; border-radius: 10px;
                }
                QPushButton:hover {background-color: #27ae60; transform: scale(1.05);}
            """)
            # 绑定点击事件
            btn.clicked.connect(lambda checked, tn=t: self.open_table(tn))
            if i < 3:  # 前3个放左边
                left_btn.addWidget(btn, alignment=Qt.AlignCenter)
            else:  # 后3个放右边
                right_btn.addWidget(btn, alignment=Qt.AlignCenter)
        btn_layout.addLayout(left_btn)
        btn_layout.addLayout(right_btn)
        main_layout.addLayout(btn_layout)

        # 数据库连接
        self.db = get_db()
        if not self.db:
            QMessageBox.critical(self, "错误", "数据库连接失败，无法操作！")
            for btn in cen_wid.findChildren(QPushButton):
                btn.setEnabled(False)

    # 设置背景图
    def set_bg(self, img_path):
        try:
            #  加载背景图片文件
            pix = QPixmap(img_path)
            #  缩放图片适配窗口大小，保持宽高比，放大到覆盖窗口，平滑缩放
            pix = pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            pal = QPalette()
            pal.setBrush(QPalette.Background, QBrush(pix))  # 创建调色板，把图片设为窗口背景
            self.setPalette(pal)  # 应用调色板到主窗口
        except Exception as e:  # 加载失败兜底用浅灰色背景，避免窗口背景空白
            self.setStyleSheet("background-color: #f0f2f5;")
            QMessageBox.warning(self, "提示", f"背景图加载失败：{str(e)}")

    # 打开子窗口，主窗口点击按钮时，调用这个函数打开对应的TableWin子窗口
    def open_table(self, t_name):
        if not self.db:
            QMessageBox.warning(self, "提示", "数据库未连接！")
            return
        try:  # 创建子窗口实例并显示子窗口
            self.table_win = TableWin(t_name, self.db)
            self.table_win.show()
        except Exception as e:  # 失败保底
            QMessageBox.warning(self, "错误", f"打开失败：{str(e)}")

    # 关闭时断开连接
    def closeEvent(self, event):
        if self.db:  # 若正常打开则正常关闭
            self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)  # 初始化Qt应用程序
    win = MainWin()  # 创建主窗口实例
    win.show()  # 显示主窗口
    sys.exit(app.exec_())  # 启动应用事件循环，等待用户操作