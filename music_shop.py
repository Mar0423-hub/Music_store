import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict, Any


class Database:
    def __init__(self, db_name="music_shop.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных с таблицами"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица ансамблей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ensembles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                founded_year INTEGER
            )
        ''')
        
        # Таблица музыкантов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS musicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                instrument TEXT
            )
        ''')
        
        # Таблица связи музыкантов и ансамблей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ensemble_musicians (
                ensemble_id INTEGER,
                musician_id INTEGER,
                FOREIGN KEY (ensemble_id) REFERENCES ensembles (id),
                FOREIGN KEY (musician_id) REFERENCES musicians (id)
            )
        ''')
        
        # Таблица музыкальных произведений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compositions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                composer TEXT,
                duration INTEGER,
                ensemble_id INTEGER,
                FOREIGN KEY (ensemble_id) REFERENCES ensembles (id)
            )
        ''')
        
        # Таблица компаний-производителей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                is_wholesaler BOOLEAN DEFAULT 0
            )
        ''')
        
        # Таблица пластинок/компакт-дисков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matrix_number TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company_id INTEGER,
                wholesale_price DECIMAL(10,2),
                retail_price DECIMAL(10,2),
                release_date DATE,
                last_year_sold INTEGER DEFAULT 0,
                current_year_sold INTEGER DEFAULT 0,
                remaining_quantity INTEGER DEFAULT 0,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # Таблица записей на пластинках
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cd_recordings (
                cd_id INTEGER,
                composition_id INTEGER,
                performance_date DATE,
                conductor TEXT,
                FOREIGN KEY (cd_id) REFERENCES cds (id),
                FOREIGN KEY (composition_id) REFERENCES compositions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Выполнение запроса с возвратом результатов"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Выполнение запроса на обновление/вставку"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id


class MusicShopApp:
    def __init__(self):
        self.db = Database()
    
    def get_ensemble_compositions_count(self, ensemble_name: str) -> int:
        """1) Количество музыкальных произведений заданного ансамбля"""
        query = '''
            SELECT COUNT(*) as count 
            FROM compositions c
            JOIN ensembles e ON c.ensemble_id = e.id
            WHERE e.name LIKE ?
        '''
        result = self.db.execute_query(query, (f'%{ensemble_name}%',))
        return result[0]['count'] if result else 0
    
    def get_ensemble_cds(self, ensemble_name: str) -> List[Dict]:
        """2) Название всех компакт-дисков заданного ансамбля"""
        query = '''
            SELECT DISTINCT cd.title, cd.matrix_number
            FROM cds cd
            JOIN cd_recordings cr ON cd.id = cr.cd_id
            JOIN compositions c ON cr.composition_id = c.id
            JOIN ensembles e ON c.ensemble_id = e.id
            WHERE e.name LIKE ?
        '''
        return self.db.execute_query(query, (f'%{ensemble_name}%',))
    
    def get_sales_leaders(self, year: int = None) -> List[Dict]:
        """3) Лидеры продаж текущего года"""
        if year is None:
            year = datetime.now().year
        
        query = '''
            SELECT title, matrix_number, current_year_sold as sold_count
            FROM cds
            WHERE current_year_sold > 0
            ORDER BY current_year_sold DESC
            LIMIT 10
        '''
        return self.db.execute_query(query)
    
    def add_cd(self, cd_data: Dict) -> int:
        """4) Добавление нового компакт-диска"""
        query = '''
            INSERT INTO cds (
                matrix_number, title, company_id, wholesale_price, 
                retail_price, release_date, remaining_quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self.db.execute_update(query, (
            cd_data['matrix_number'], cd_data['title'], cd_data['company_id'],
            cd_data['wholesale_price'], cd_data['retail_price'],
            cd_data['release_date'], cd_data['remaining_quantity']
        ))
    
    def update_cd(self, cd_id: int, cd_data: Dict) -> bool:
        """4) Обновление данных о компакт-диске"""
        query = '''
            UPDATE cds SET 
                matrix_number = ?, title = ?, company_id = ?, 
                wholesale_price = ?, retail_price = ?, 
                release_date = ?, remaining_quantity = ?,
                current_year_sold = ?, last_year_sold = ?
            WHERE id = ?
        '''
        try:
            self.db.execute_update(query, (
                cd_data['matrix_number'], cd_data['title'], cd_data['company_id'],
                cd_data['wholesale_price'], cd_data['retail_price'],
                cd_data['release_date'], cd_data['remaining_quantity'],
                cd_data['current_year_sold'], cd_data['last_year_sold'], cd_id
            ))
            return True
        except Exception as e:
            print(f"Error updating CD: {e}")
            return False
    
    def add_ensemble(self, ensemble_data: Dict) -> int:
        """5) Добавление нового ансамбля"""
        query = '''
            INSERT INTO ensembles (name, type, founded_year)
            VALUES (?, ?, ?)
        '''
        return self.db.execute_update(query, (
            ensemble_data['name'], ensemble_data['type'], ensemble_data['founded_year']
        ))
    
    def get_all_ensembles(self) -> List[Dict]:
        """Получение всех ансамблей"""
        return self.db.execute_query('SELECT * FROM ensembles ORDER BY name')
    
    def get_all_cds(self) -> List[Dict]:
        """Получение всех компакт-дисков"""
        return self.db.execute_query('SELECT * FROM cds ORDER BY title')
    
    def get_companies(self) -> List[Dict]:
        """Получение всех компаний"""
        return self.db.execute_query('SELECT * FROM companies ORDER BY name')


class MusicShopGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Музыкальный магазин - Управление базой данных")
        self.root.geometry("900x700")
        
        self.app = MusicShopApp()
        
        self.create_widgets()
        self.load_initial_data()
        self.add_demo_data()  # Автоматически добавляем демо-данныe
    
    def create_widgets(self):
        # Создание вкладок
        notebook = ttk.Notebook(self.root)
        
        # Вкладка 1: Количество произведений ансамбля
        tab1 = ttk.Frame(notebook)
        self.create_tab1(tab1)
        
        # Вкладка 2: CD ансамбля
        tab2 = ttk.Frame(notebook)
        self.create_tab2(tab2)
        
        # Вкладка 3: Лидеры продаж
        tab3 = ttk.Frame(notebook)
        self.create_tab3(tab3)
        
        # Вкладка 4: Управление CD
        tab4 = ttk.Frame(notebook)
        self.create_tab4(tab4)
        
        # Вкладка 5: Управление ансамблями
        tab5 = ttk.Frame(notebook)
        self.create_tab5(tab5)
        
        notebook.add(tab1, text="Произведения ансамбля")
        notebook.add(tab2, text="CD ансамбля")
        notebook.add(tab3, text="Лидеры продаж")
        notebook.add(tab4, text="Управление CD")
        notebook.add(tab5, text="Управление ансамблями")
        
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
    
    def create_tab1(self, parent):
        tk.Label(parent, text="Поиск количества музыкальных произведений ансамбля", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = tk.Frame(parent)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Название ансамбля:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.ensemble_entry = tk.Entry(frame, width=40, font=('Arial', 10))
        self.ensemble_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Найти количество произведений", 
                 command=self.show_compositions_count, bg='lightblue').grid(row=1, column=0, columnspan=2, pady=10)
        
        self.result_label = tk.Label(parent, text="", font=('Arial', 12, 'bold'), fg='darkgreen')
        self.result_label.pack(pady=10)
        
        # Примеры для тестирования
        examples_frame = tk.LabelFrame(parent, text="Примеры для тестирования")
        examples_frame.pack(pady=10, fill='x', padx=20)
        
        examples = [
            "Лондонский филармонический оркестр",
            "The Beatles", 
            "Квартет имени Бородина"
        ]
        
        for example in examples:
            tk.Label(examples_frame, text=f"• {example}", font=('Arial', 9)).pack(anchor='w', padx=10, pady=2)
    
    def create_tab2(self, parent):
        tk.Label(parent, text="Поиск компакт-дисков ансамбля", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = tk.Frame(parent)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Название ансамбля:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.ensemble_cd_entry = tk.Entry(frame, width=40, font=('Arial', 10))
        self.ensemble_cd_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame, text="Найти CD ансамбля", 
                 command=self.show_ensemble_cds, bg='lightgreen').grid(row=1, column=0, columnspan=2, pady=10)
        
        # Таблица результатов
        tree_frame = tk.Frame(parent)
        tree_frame.pack(pady=10, fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.cd_tree = ttk.Treeview(tree_frame, columns=('Title', 'Matrix'), show='headings',
                                   yscrollcommand=scrollbar.set, height=8)
        self.cd_tree.heading('Title', text='Название CD')
        self.cd_tree.heading('Matrix', text='Номер матрицы')
        self.cd_tree.column('Title', width=400)
        self.cd_tree.column('Matrix', width=200)
        self.cd_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=self.cd_tree.yview)
    
    def create_tab3(self, parent):
        tk.Label(parent, text="Лидеры продаж текущего года", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Button(parent, text="Обновить список лидеров продаж", 
                 command=self.show_sales_leaders, bg='lightcoral', font=('Arial', 10)).pack(pady=10)
        
        # Таблица лидеров продаж
        tree_frame = tk.Frame(parent)
        tree_frame.pack(pady=10, fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.sales_tree = ttk.Treeview(tree_frame, columns=('Title', 'Matrix', 'Sold'), show='headings',
                                      yscrollcommand=scrollbar.set, height=8)
        self.sales_tree.heading('Title', text='Название CD')
        self.sales_tree.heading('Matrix', text='Номер матрицы')
        self.sales_tree.heading('Sold', text='Продано в этом году')
        self.sales_tree.column('Title', width=350)
        self.sales_tree.column('Matrix', width=150)
        self.sales_tree.column('Sold', width=150)
        self.sales_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=self.sales_tree.yview)
    
    def create_tab4(self, parent):
        tk.Label(parent, text="Управление компакт-дисками", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Форма для добавления/редактирования CD
        form_frame = tk.LabelFrame(parent, text="Добавить/Редактировать CD")
        form_frame.pack(pady=10, fill='x', padx=20)
        
        tk.Label(form_frame, text="Номер матрицы:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.matrix_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.matrix_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Название:*").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.title_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.title_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Оптовая цена:*").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.wholesale_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.wholesale_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Розничная цена:*").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.retail_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.retail_entry.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Количество на складе:*").grid(row=4, column=0, sticky='e', padx=5, pady=5)
        self.quantity_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.quantity_entry.grid(row=4, column=1, padx=5, pady=5)
        
        button_frame = tk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="Добавить CD", command=self.add_cd, bg='lightgreen', width=15).pack(side='left', padx=5)
        tk.Button(button_frame, text="Обновить выбранный", command=self.update_cd, bg='lightblue', width=15).pack(side='left', padx=5)
        tk.Button(button_frame, text="Очистить форму", command=self.clear_cd_form, bg='lightyellow', width=15).pack(side='left', padx=5)
        
        # Таблица существующих CD
        list_frame = tk.LabelFrame(parent, text="Существующие компакт-диски")
        list_frame.pack(pady=10, fill='both', expand=True, padx=20)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.cd_management_tree = ttk.Treeview(list_frame, 
                                              columns=('ID', 'Title', 'Matrix', 'Price', 'Remaining'), 
                                              show='headings', yscrollcommand=scrollbar.set, height=6)
        self.cd_management_tree.heading('ID', text='ID')
        self.cd_management_tree.heading('Title', text='Название')
        self.cd_management_tree.heading('Matrix', text='Номер матрицы')
        self.cd_management_tree.heading('Price', text='Розничная цена')
        self.cd_management_tree.heading('Remaining', text='Остаток')
        self.cd_management_tree.column('ID', width=50)
        self.cd_management_tree.column('Title', width=300)
        self.cd_management_tree.column('Matrix', width=150)
        self.cd_management_tree.column('Price', width=100)
        self.cd_management_tree.column('Remaining', width=80)
        self.cd_management_tree.pack(side='left', fill='both', expand=True)
        self.cd_management_tree.bind('<<TreeviewSelect>>', self.on_cd_select)
        
        scrollbar.config(command=self.cd_management_tree.yview)
    
    def create_tab5(self, parent):
        tk.Label(parent, text="Управление ансамблями", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Форма для добавления ансамблей
        form_frame = tk.LabelFrame(parent, text="Добавить новый ансамбль")
        form_frame.pack(pady=10, fill='x', padx=20)
        
        tk.Label(form_frame, text="Название ансамбля:*").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.ensemble_name_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.ensemble_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Тип ансамбля:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.ensemble_type_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.ensemble_type_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Год основания:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.founded_year_entry = tk.Entry(form_frame, width=30, font=('Arial', 10))
        self.founded_year_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Button(form_frame, text="Добавить ансамбль", command=self.add_ensemble, 
                 bg='lightgreen').grid(row=3, column=0, columnspan=2, pady=10)
        
        # Таблица существующих ансамблей
        list_frame = tk.LabelFrame(parent, text="Существующие ансамбли")
        list_frame.pack(pady=10, fill='both', expand=True, padx=20)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.ensemble_tree = ttk.Treeview(list_frame, 
                                         columns=('ID', 'Name', 'Type', 'Year'), 
                                         show='headings', yscrollcommand=scrollbar.set, height=8)
        self.ensemble_tree.heading('ID', text='ID')
        self.ensemble_tree.heading('Name', text='Название')
        self.ensemble_tree.heading('Type', text='Тип')
        self.ensemble_tree.heading('Year', text='Год основания')
        self.ensemble_tree.column('ID', width=50)
        self.ensemble_tree.column('Name', width=250)
        self.ensemble_tree.column('Type', width=150)
        self.ensemble_tree.column('Year', width=100)
        self.ensemble_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=self.ensemble_tree.yview)
    
    def load_initial_data(self):
        self.refresh_cd_list()
        self.refresh_ensemble_list()
    
    def add_demo_data(self):
        """Добавление демонстрационных данных при первом запуске"""
        try:
            # Проверяем, есть ли уже данные
            existing_ensembles = self.app.get_all_ensembles()
            if existing_ensembles:
                return  # Данные уже есть
            
            # Добавляем компании
            companies = [
                ("EMI", "Лондон, Великобритания", 1),
                ("Sony Music", "Нью-Йорк, США", 1),
                ("Universal Music", "Калифорния, США", 1)
            ]
            
            for company in companies:
                self.app.db.execute_update(
                    "INSERT INTO companies (name, address, is_wholesaler) VALUES (?, ?, ?)",
                    company
                )
            
            # Добавляем ансамбли
            ensembles = [
                ("Лондонский филармонический оркестр", "Оркестр", 1932),
                ("The Beatles", "Рок-группа", 1960),
                ("Квартет имени Бородина", "Струнный квартет", 1945)
            ]
            
            for ensemble in ensembles:
                self.app.db.execute_update(
                    "INSERT INTO ensembles (name, type, founded_year) VALUES (?, ?, ?)",
                    ensemble
                )
            
            # Добавляем музыкальные произведения
            compositions = [
                ("Симфония №5", "Бетховен", 1808, 1),
                ("Yesterday", "Леннон/Маккартни", 1965, 2),
                ("Квартет №8", "Шостакович", 1960, 3)
            ]
            
            for comp in compositions:
                self.app.db.execute_update(
                    "INSERT INTO compositions (title, composer, duration, ensemble_id) VALUES (?, ?, ?, ?)",
                    comp
                )
            
            # Добавляем CD
            cds = [
                ("CD001", "Великие симфонии", 1, 5.00, 15.00, "2023-01-15", 100, 50, 200),
                ("CD002", "The Beatles Greatest Hits", 2, 6.00, 18.00, "2023-02-20", 200, 150, 100),
                ("CD003", "Русская классика", 3, 4.50, 12.00, "2023-03-10", 50, 30, 70)
            ]
            
            for cd in cds:
                self.app.db.execute_update('''
                    INSERT INTO cds (matrix_number, title, company_id, wholesale_price, 
                                   retail_price, release_date, last_year_sold, current_year_sold, remaining_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', cd)
            
            # Добавляем записи на CD
            recordings = [
                (1, 1, "2022-10-15", "Сэр Джон Барбиролли"),
                (2, 2, "2023-01-20", ""),
                (3, 3, "2023-02-10", "Рудольф Баршай")
            ]
            
            for recording in recordings:
                self.app.db.execute_update(
                    "INSERT INTO cd_recordings (cd_id, composition_id, performance_date, conductor) VALUES (?, ?, ?, ?)",
                    recording
                )
            
            print("Демонстрационные данные добавлены успешно!")
            self.refresh_cd_list()
            self.refresh_ensemble_list()
            
        except Exception as e:
            print(f"Ошибка при добавлении демо-данных: {e}")
    
    def show_compositions_count(self):
        ensemble_name = self.ensemble_entry.get().strip()
        if not ensemble_name:
            messagebox.showerror("Ошибка", "Введите название ансамбля")
            return
        
        count = self.app.get_ensemble_compositions_count(ensemble_name)
        if count == 0:
            self.result_label.config(text=f"Ансамбль '{ensemble_name}' не найден или у него нет произведений", fg='red')
        else:
            self.result_label.config(text=f"Ансамбль '{ensemble_name}' имеет {count} музыкальных произведений", fg='darkgreen')
    
    def show_ensemble_cds(self):
        ensemble_name = self.ensemble_cd_entry.get().strip()
        if not ensemble_name:
            messagebox.showerror("Ошибка", "Введите название ансамбля")
            return
        
        cds = self.app.get_ensemble_cds(ensemble_name)
        
        # Очистка таблицы
        for item in self.cd_tree.get_children():
            self.cd_tree.delete(item)
        
        # Заполнение данными
        if not cds:
            self.cd_tree.insert('', 'end', values=("CD не найдены", ""))
        else:
            for cd in cds:
                self.cd_tree.insert('', 'end', values=(cd['title'], cd['matrix_number']))
    
    def show_sales_leaders(self):
        leaders = self.app.get_sales_leaders()
        
        # Очистка таблицы
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        
        # Заполнение данными
        if not leaders:
            self.sales_tree.insert('', 'end', values=("Нет данных о продажах", "", ""))
        else:
            for leader in leaders:
                self.sales_tree.insert('', 'end', values=(
                    leader['title'], leader['matrix_number'], leader['sold_count']
                ))
    
    def add_cd(self):
        try:
            # Валидация данных
            if not all([self.matrix_entry.get(), self.title_entry.get(), 
                       self.wholesale_entry.get(), self.retail_entry.get(), 
                       self.quantity_entry.get()]):
                messagebox.showerror("Ошибка", "Заполните все обязательные поля (отмечены *)")
                return
            
            cd_data = {
                'matrix_number': self.matrix_entry.get(),
                'title': self.title_entry.get(),
                'company_id': 1,  # Упрощенно - первая компания
                'wholesale_price': float(self.wholesale_entry.get()),
                'retail_price': float(self.retail_entry.get()),
                'release_date': datetime.now().strftime('%Y-%m-%d'),
                'remaining_quantity': int(self.quantity_entry.get()),
                'current_year_sold': 0,
                'last_year_sold': 0
            }
            
            self.app.add_cd(cd_data)
            messagebox.showinfo("Успех", "CD успешно добавлен")
            self.clear_cd_form()
            self.refresh_cd_list()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность числовых данных (цена и количество)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def update_cd(self):
        selection = self.cd_management_tree.selection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите CD для обновления")
            return
        
        try:
            item = self.cd_management_tree.item(selection[0])
            cd_id = item['values'][0]
            
            # Валидация данных
            if not all([self.matrix_entry.get(), self.title_entry.get(), 
                       self.wholesale_entry.get(), self.retail_entry.get(), 
                       self.quantity_entry.get()]):
                messagebox.showerror("Ошибка", "Заполните все обязательные поля")
                return
            
            cd_data = {
                'matrix_number': self.matrix_entry.get(),
                'title': self.title_entry.get(),
                'company_id': 1,
                'wholesale_price': float(self.wholesale_entry.get()),
                'retail_price': float(self.retail_entry.get()),
                'release_date': datetime.now().strftime('%Y-%m-%d'),
                'remaining_quantity': int(self.quantity_entry.get()),
                'current_year_sold': 0,
                'last_year_sold': 0
            }
            
            if self.app.update_cd(cd_id, cd_data):
                messagebox.showinfo("Успех", "CD успешно обновлен")
                self.refresh_cd_list()
            else:
                messagebox.showerror("Ошибка", "Ошибка при обновлении CD")
                
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность числовых данных")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")
    
    def add_ensemble(self):
        try:
            ensemble_name = self.ensemble_name_entry.get().strip()
            if not ensemble_name:
                messagebox.showerror("Ошибка", "Введите название ансамбля")
                return
            
            ensemble_data = {
                'name': ensemble_name,
                'type': self.ensemble_type_entry.get() or "Не указан",
                'founded_year': int(self.founded_year_entry.get() or 0)
            }
            
            self.app.add_ensemble(ensemble_data)
            messagebox.showinfo("Успех", "Ансамбль успешно добавлен")
            self.clear_ensemble_form()
            self.refresh_ensemble_list()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Год основания должен быть числом")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")
    
    def on_cd_select(self, event):
        selection = self.cd_management_tree.selection()
        if selection:
            item = self.cd_management_tree.item(selection[0])
            values = item['values']
            
            # Получаем полные данные о CD
            cds = self.app.get_all_cds()
            selected_cd = next((cd for cd in cds if cd['id'] == values[0]), None)
            
            if selected_cd:
                self.matrix_entry.delete(0, tk.END)
                self.matrix_entry.insert(0, selected_cd['matrix_number'])
                
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, selected_cd['title'])
                
                self.wholesale_entry.delete(0, tk.END)
                self.wholesale_entry.insert(0, str(selected_cd['wholesale_price']))
                
                self.retail_entry.delete(0, tk.END)
                self.retail_entry.insert(0, str(selected_cd['retail_price']))
                
                self.quantity_entry.delete(0, tk.END)
                self.quantity_entry.insert(0, str(selected_cd['remaining_quantity']))
    
    def refresh_cd_list(self):
        for item in self.cd_management_tree.get_children():
            self.cd_management_tree.delete(item)
        
        cds = self.app.get_all_cds()
        for cd in cds:
            self.cd_management_tree.insert('', 'end', values=(
                cd['id'], cd['title'], cd['matrix_number'], 
                f"{cd['retail_price']} руб.", cd['remaining_quantity']
            ))
    
    def refresh_ensemble_list(self):
        for item in self.ensemble_tree.get_children():
            self.ensemble_tree.delete(item)
        
        ensembles = self.app.get_all_ensembles()
        for ensemble in ensembles:
            self.ensemble_tree.insert('', 'end', values=(
                ensemble['id'], ensemble['name'], ensemble['type'], 
                ensemble['founded_year'] if ensemble['founded_year'] else "Не указан"
            ))
    
    def clear_cd_form(self):
        self.matrix_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.wholesale_entry.delete(0, tk.END)
        self.retail_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
    
    def clear_ensemble_form(self):
        self.ensemble_name_entry.delete(0, tk.END)
        self.ensemble_type_entry.delete(0, tk.END)
        self.founded_year_entry.delete(0, tk.END)


def main():
    """Основная функция запуска приложения"""
    try:
        root = tk.Tk()
        app = MusicShopGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")
        messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {e}")


if __name__ == "__main__":
    main()