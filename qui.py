import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import geometry_kb as kb
from engine import ConstraintNetwork
from typing import Optional, Tuple, Dict

class GeometryCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Máy tính Hình học - Geometry Calculator")
        self.root.geometry("1200x800")
        
        # Networks
        self.tri_net = None
        self.rect_net = None
        
        # Input variables
        self.input_vars = {}
        
        # Shape selection
        self.shape_var = tk.StringVar(value="auto")  # "auto", "triangle", "rectangle"

        # Lưu network sau khi tính toán
        self.last_network = None
        # Lưu loại hình sau khi tính toán
        self.last_is_triangle = None
        # Lưu kết quả sau khi tính toán
        self.last_result = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Left panel - Input
        left_frame = ttk.LabelFrame(main_frame, text="Nhập dữ liệu", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Shape selection
        shape_frame = ttk.LabelFrame(left_frame, text="Chọn hình", padding="5")
        shape_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(shape_frame, text="Tự động phân loại", variable=self.shape_var, 
                       value="auto").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Triangle options
        ttk.Label(shape_frame, text="Tam giác:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5,2))
        ttk.Radiobutton(shape_frame, text="Tam giác thường", variable=self.shape_var, value="triangle").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tam giác vuông", variable=self.shape_var, value="triangle_right").grid(row=1, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tam giác đều", variable=self.shape_var, value="triangle_equilateral").grid(row=1, column=3, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tam giác cân", variable=self.shape_var, value="triangle_isosceles").grid(row=1, column=4, sticky=tk.W, padx=5)

        # Quadrilateral options
        ttk.Label(shape_frame, text="Tứ giác:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5,2))
        ttk.Radiobutton(shape_frame, text="Hình vuông", variable=self.shape_var, value="square").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Hình chữ nhật", variable=self.shape_var, value="rectangle").grid(row=2, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Hình thoi", variable=self.shape_var, value="rhombus").grid(row=2, column=3, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Hình bình hành", variable=self.shape_var, value="parallelogram").grid(row=2, column=4, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Hình thang", variable=self.shape_var, value="trapezoid").grid(row=2, column=5, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tứ giác thường", variable=self.shape_var, value="quadrilateral").grid(row=2, column=6, sticky=tk.W, padx=5)
        
        # --- THÊM NÚT HIỂN THỊ NÂNG CAO ---
        self.advanced_var = tk.BooleanVar(value=False)
        advanced_btn = ttk.Checkbutton(left_frame, text="Hiển thị nâng cao (nhập riêng từng chiều cao h_a, h_b, h_c, h_d)", variable=self.advanced_var, command=self.toggle_advanced)
        advanced_btn.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # Input fields - Sides
        sides_frame = ttk.LabelFrame(left_frame, text="Cạnh (Sides)", padding="5")
        sides_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.input_vars['a'] = tk.StringVar()
        self.input_vars['b'] = tk.StringVar()
        self.input_vars['c'] = tk.StringVar()
        self.input_vars['d'] = tk.StringVar()
        
        ttk.Label(sides_frame, text="a:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(sides_frame, textvariable=self.input_vars['a'], width=15).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(sides_frame, text="b:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(sides_frame, textvariable=self.input_vars['b'], width=15).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(sides_frame, text="c:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(sides_frame, textvariable=self.input_vars['c'], width=15).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(sides_frame, text="d:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(sides_frame, textvariable=self.input_vars['d'], width=15).grid(row=1, column=3, padx=5, pady=2)
        
        # --- THÊM INPUT CHIỀU CAO ---
        self.input_vars['h'] = tk.StringVar()
        ttk.Label(sides_frame, text="h (chiều cao, ứng với cạnh a):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(sides_frame, textvariable=self.input_vars['h'], width=15).grid(row=2, column=1, padx=5, pady=2)

        # --- INPUT CHIỀU CAO NÂNG CAO ---
        self.input_vars['h_a'] = tk.StringVar()
        self.input_vars['h_b'] = tk.StringVar()
        self.input_vars['h_c'] = tk.StringVar()
        self.input_vars['h_d'] = tk.StringVar()
        self.hb_label = ttk.Label(sides_frame, text="h_b (chiều cao ứng với cạnh b):")
        self.hb_entry = ttk.Entry(sides_frame, textvariable=self.input_vars['h_b'], width=15)
        self.hc_label = ttk.Label(sides_frame, text="h_c (chiều cao ứng với cạnh c):")
        self.hc_entry = ttk.Entry(sides_frame, textvariable=self.input_vars['h_c'], width=15)
        self.hd_label = ttk.Label(sides_frame, text="h_d (chiều cao ứng với cạnh d):")
        self.hd_entry = ttk.Entry(sides_frame, textvariable=self.input_vars['h_d'], width=15)
        # Ẩn mặc định
        self.hb_label.grid_remove()
        self.hb_entry.grid_remove()
        self.hc_label.grid_remove()
        self.hc_entry.grid_remove()
        self.hd_label.grid_remove()
        self.hd_entry.grid_remove()

        # Input fields - Angles
        angles_frame = ttk.LabelFrame(left_frame, text="Góc (Angles) - độ", padding="5")
        angles_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.input_vars['A'] = tk.StringVar()
        self.input_vars['B'] = tk.StringVar()
        self.input_vars['C'] = tk.StringVar()
        self.input_vars['D'] = tk.StringVar()
        
        ttk.Label(angles_frame, text="A:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(angles_frame, textvariable=self.input_vars['A'], width=15).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(angles_frame, text="B:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(angles_frame, textvariable=self.input_vars['B'], width=15).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(angles_frame, text="C:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(angles_frame, textvariable=self.input_vars['C'], width=15).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(angles_frame, text="D:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(angles_frame, textvariable=self.input_vars['D'], width=15).grid(row=1, column=3, padx=5, pady=2)
        
        # Input fields - Perimeter and Area
        other_frame = ttk.LabelFrame(left_frame, text="Chu vi & Diện tích", padding="5")
        other_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.input_vars['perimeter'] = tk.StringVar()
        self.input_vars['area'] = tk.StringVar()
        
        ttk.Label(other_frame, text="Chu vi:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(other_frame, textvariable=self.input_vars['perimeter'], width=15).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(other_frame, text="Diện tích:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(other_frame, textvariable=self.input_vars['area'], width=15).grid(row=0, column=3, padx=5, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Tính toán", command=self.calculate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Xóa dữ liệu", command=self.clear_inputs).pack(side=tk.LEFT, padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(left_frame, text="Kết quả", padding="5")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        left_frame.rowconfigure(5, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, width=40, height=15, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Graph
        right_frame = ttk.LabelFrame(main_frame, text="Đồ thị hình học", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        
        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.text(0.5, 0.5, 'Nhập dữ liệu và nhấn "Tính toán"\nđể xem đồ thị', 
                    ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def clear_inputs(self):
        """Clear all input fields"""
        for var in self.input_vars.values():
            var.set("")
        self.results_text.delete(1.0, tk.END)
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.text(0.5, 0.5, 'Nhập dữ liệu và nhấn "Tính toán"\nđể xem đồ thị', 
                    ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
        self.canvas.draw()
        self.last_network = None
        self.last_is_triangle = None
        self.last_result = None

    def toggle_advanced(self):
        """Hiện/ẩn các trường nhập chiều cao nâng cao"""
        if self.advanced_var.get():
            # Hiện các trường nhập h_b, h_c, h_d
            self.hb_label.grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
            self.hb_entry.grid(row=2, column=3, padx=5, pady=2)
            self.hc_label.grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
            self.hc_entry.grid(row=3, column=1, padx=5, pady=2)
            self.hd_label.grid(row=3, column=2, sticky=tk.W, padx=5, pady=2)
            self.hd_entry.grid(row=3, column=3, padx=5, pady=2)
        else:
            # Ẩn các trường nhập h_b, h_c, h_d
            self.hb_label.grid_remove()
            self.hb_entry.grid_remove()
            self.hc_label.grid_remove()
            self.hc_entry.grid_remove()
            self.hd_label.grid_remove()
            self.hd_entry.grid_remove()

    def parse_inputs(self) -> Dict[str, float]:
        """Parse input values from GUI, return dict of name->value (None if empty)"""
        inputs = {}
        for name, var in self.input_vars.items():
            val_str = var.get().strip()
            if val_str:
                try:
                    val = float(val_str)
                    inputs[name] = val
                except ValueError:
                    pass  # Invalid number, skip
        # Nếu nâng cao, ưu tiên các giá trị h_a, h_b, h_c, h_d nếu có
        if self.advanced_var.get():
            for hname in ['h_a', 'h_b', 'h_c', 'h_d']:
                if hname in inputs:
                    inputs[hname] = inputs[hname]
        # Nếu chỉ nhập h, gán cho h_a
        if 'h' in inputs and 'h_a' not in inputs:
            inputs['h_a'] = inputs['h']
        return inputs
    
    def validate_inputs(self, inputs: Dict[str, float]) -> Tuple[bool, str]:
        """Validate input values"""
        # Check sides > 0
        for side in ('a', 'b', 'c', 'd'):
            if side in inputs and inputs[side] <= 0:
                return False, f"Cạnh {side} phải > 0"
        
        # Check angles in (0, 360)
        for angle in ('A', 'B', 'C', 'D'):
            if angle in inputs:
                val = inputs[angle]
                if val <= 0 or val >= 360:
                    return False, f"Góc {angle} phải trong khoảng (0, 360)"
        
        # Kiểm tra chiều cao > 0 nếu có
        if 'h' in inputs and inputs['h'] <= 0:
            return False, "Chiều cao (h) phải > 0"
        return True, ""
    
    def score_network(self, net: ConstraintNetwork, other: ConstraintNetwork) -> int:
        """Scoring function to help auto-detect best network"""
        known = sum(1 for v in net.vars.values() if v.is_known())
        unique_known = sum(1 for n, v in net.vars.items() if n not in other.vars and v.is_known())
        return known + unique_known * 2

    def choose_network(self, inputs: Dict[str, float]) -> Tuple[Optional[ConstraintNetwork], str]:
        """Choose which network to use based on shape selection or auto-detect"""
        shape = self.shape_var.get()
        
        # --- LOGIC CHỌN THỦ CÔNG (MANUAL) ---
        if shape == "triangle":
            return kb.create_triangle_network(), "Tam giác thường (đã chọn)"
            
        elif shape == "triangle_right":
            net = kb.create_triangle_network()
            # Chỉ thêm C=90 nếu chưa có góc vuông nào
            has_right_angle = any(abs(inputs.get(ang, 0) - 90) < 0.1 for ang in ['A','B','C'])
            if not has_right_angle:
                inputs['C'] = 90.0 
            return net, "Tam giác vuông (đã chọn)"
            
        elif shape == "triangle_equilateral":
            net = kb.create_triangle_network()
            # Lấy 1 cạnh làm chuẩn để điền cho các cạnh kia
            val_a = inputs.get('a') or inputs.get('b') or inputs.get('c') or inputs.get('d')
            if val_a is not None:
                inputs.update({'a': val_a, 'b': val_a, 'c': val_a})
            # Tam giác đều thì góc bắt buộc là 60 (Đúng định nghĩa)
            inputs.update({'A': 60.0, 'B': 60.0, 'C': 60.0})
            return net, "Tam giác đều (đã chọn, auto-fill)"
            
        elif shape == "triangle_isosceles":
            net = kb.create_triangle_network()
            # [FIX] KHÔNG ĐƯỢC tự ý gán góc 70 độ.
            # Chỉ đồng bộ cạnh nếu người dùng nhập thiếu.
            a, b, c = inputs.get('a'), inputs.get('b'), inputs.get('c')
            
            # Logic: Nếu nhập 2 cạnh -> coi như bằng nhau (nếu chưa nhập cạnh thứ 3)
            # Hoặc nếu nhập 1 cạnh -> chờ solver tính.
            # Ở đây ta chỉ validate xem có cân thật không, hoặc copy giá trị nếu user nhập kiểu "a=10" (ý là cạnh bên)
            
            # Mẹo: Nếu user chỉ nhập a=10 và chọn cân -> Tự hiểu là a=b=10? 
            # Tạm thời giữ logic copy cạnh, nhưng BỎ logic setdefault 70 độ.
            if a is not None and b is None and c is None: # Chỉ nhập a
                 inputs['b'] = a # Giả định cân tại C
            elif b is not None and a is None and c is None:
                 inputs['c'] = b
            
            return net, "Tam giác cân (đã chọn)"
            
        elif shape == "square":
            net = kb.create_square_network()
            val = inputs.get('a') or inputs.get('b') or inputs.get('c') or inputs.get('d')
            if val is not None:
                inputs.update({'a': val, 'b': val, 'c': val, 'd': val})
            inputs.update({'A': 90.0, 'B': 90.0, 'C': 90.0, 'D': 90.0})
            return net, "Hình vuông (đã chọn, auto-fill)"
            
        elif shape == "rectangle":
            net = kb.create_rectangle_network()
            # Đồng bộ cạnh đối
            val_ac = inputs.get('a') if inputs.get('a') is not None else inputs.get('c')
            if val_ac is not None: inputs.update({'a': val_ac, 'c': val_ac})
            val_bd = inputs.get('b') if inputs.get('b') is not None else inputs.get('d')
            if val_bd is not None: inputs.update({'b': val_bd, 'd': val_bd})
            
            inputs.update({'A': 90.0, 'B': 90.0, 'C': 90.0, 'D': 90.0})
            msg = "Hình chữ nhật (đã chọn)"
            if val_ac and inputs.get('c') and abs(val_ac - inputs['c']) > 1e-6:
                 msg += " (Đã đồng bộ cạnh)"
            return net, msg

        elif shape == "rhombus":
            net = kb.create_rhombus_network()
            val = inputs.get('a')
            if val is not None:
                inputs.update({'a': val, 'b': val, 'c': val, 'd': val})
            return net, "Hình thoi (đã chọn)"

        elif shape == "parallelogram":
            net = kb.create_parallelogram_network()
            if inputs.get('a'): inputs['c'] = inputs['a']
            if inputs.get('b'): inputs['d'] = inputs['b']
            if inputs.get('A'): inputs['C'] = inputs['A']
            if inputs.get('B'): inputs['D'] = inputs['B']
            return net, "Hình bình hành (đã chọn)"

        elif shape == "trapezoid":
            net = kb.create_trapezoid_network()
            return net, "Hình thang (đã chọn)"

        elif shape == "quadrilateral":
            net = kb.create_quadrilateral_network()
            return net, "Tứ giác thường (đã chọn)"

        # --- LOGIC TỰ ĐỘNG (AUTO-DETECT) - GIỮ NGUYÊN ---
        tri_side_names = {'a', 'b', 'c'}
        rect_side_names = {'a', 'b', 'c', 'd'}
        has_d = ('d' in inputs) or ('D' in inputs)
        
        if has_d: return kb.create_rectangle_network(), "Tứ giác (có d)"
        
        if sum(1 for n in inputs if n in tri_side_names) >= 3:
             return kb.create_triangle_network(), "Tam giác (3 cạnh)"
        
        # --- FALLBACK: CHẤM ĐIỂM (SCORING) ---
        tri_net = kb.create_triangle_network()
        rect_net = kb.create_rectangle_network()
        tri_net.reset(); rect_net.reset()
        # Nạp input tạm để chấm điểm
        for k, v in inputs.items():
            if k in tri_net.vars: tri_net.set_input(k, v, 'temp')
            if k in rect_net.vars: rect_net.set_input(k, v, 'temp')
            
        tscore = self.score_network(tri_net, rect_net)
        rscore = self.score_network(rect_net, tri_net)
        
        if tscore == 0 and rscore == 0:
            return None, "Không đủ dữ liệu"
        if tscore >= rscore:
            return kb.create_triangle_network(), f"Tam giác (Score: {tscore})"
        else:
            return kb.create_rectangle_network(), f"Tứ giác (Score: {rscore})"

    def classify_shape(self, net: ConstraintNetwork, res: Dict[str, Optional[float]], is_triangle: bool) -> Tuple[str, list]:
        """Classify the shape type"""
        if is_triangle:
            a, b, c = res.get('a'), res.get('b'), res.get('c')
            A, B, C = res.get('A'), res.get('B'), res.get('C')
            
            def close(x, y, thr=1e-6):
                return x is not None and y is not None and abs(x - y) < thr
            
            equilateral = (a is not None and b is not None and c is not None and 
                          close(a, b) and close(b, c))
            isos = ((a is not None and b is not None and close(a, b)) or
                   (a is not None and c is not None and close(a, c)) or
                   (b is not None and c is not None and close(b, c)))
            right_angle = ((A is not None and abs(A - 90) < 0.1) or
                          (B is not None and abs(B - 90) < 0.1) or
                          (C is not None and abs(C - 90) < 0.1))
            right_by_pyth = False
            if a is not None and b is not None and c is not None:
                if (abs(a*a + b*b - c*c) < 1e-3 or abs(a*a + c*c - b*b) < 1e-3 or 
                    abs(b*b + c*c - a*a) < 1e-3):
                    right_by_pyth = True
            right = right_angle or right_by_pyth
            
            if equilateral:
                return "Tam giác đều", ["Tam giác đều", "Tam giác cân", "Tam giác"]
            if right and isos:
                return "Tam giác vuông cân", ["Tam giác vuông cân", "Tam giác vuông", "Tam giác cân", "Tam giác"]
            if right:
                return "Tam giác vuông", ["Tam giác vuông", "Tam giác"]
            if isos:
                return "Tam giác cân", ["Tam giác cân", "Tam giác"]
            return "Tam giác thường", ["Tam giác"]
        else:
            a, b, c, d = res.get('a'), res.get('b'), res.get('c'), res.get('d')
            A, B, C, D = res.get('A'), res.get('B'), res.get('C'), res.get('D')
            
            def close(x, y, thr=1e-6):
                return x is not None and y is not None and abs(x - y) < thr
            
            all_sides_equal = (a is not None and b is not None and c is not None and d is not None and
                              close(a, b) and close(b, c) and close(c, d))
            all_angles_90 = (A is not None and B is not None and C is not None and D is not None and
                            all(abs(x - 90) < 0.1 for x in (A, B, C, D)))
            right_any = any(x is not None and abs(x - 90) < 0.1 for x in (A, B, C, D))
            opp_sides_equal = ((a is not None and c is not None and close(a, c)) and
                              (b is not None and d is not None and close(b, d)))
            opp_angles_equal = ((A is not None and C is not None and close(A, C, 1e-3)) and
                               (B is not None and D is not None and close(B, D, 1e-3)))
            
            if all_sides_equal and (all_angles_90 or right_any):
                return "Hình vuông", ["Hình vuông", "Hình chữ nhật", "Hình bình hành", "Tứ giác"]
            if (all_angles_90 or right_any) and (opp_sides_equal or (a is not None and b is not None)):
                return "Hình chữ nhật", ["Hình chữ nhật", "Hình bình hành", "Tứ giác"]
            if all_sides_equal and (opp_angles_equal or opp_sides_equal):
                return "Hình thoi", ["Hình thoi", "Hình bình hành", "Tứ giác"]
            if opp_sides_equal or opp_angles_equal:
                return "Hình bình hành", ["Hình bình hành", "Tứ giác"]
            # Trapezoid detection qua tổng góc kề = 180
            def adjacent_sum_180(x, y):
                return x is not None and y is not None and abs((x + y) - 180.0) < 0.1
            trapezoid = False
            if (A is not None and B is not None and adjacent_sum_180(A, B)) or \
               (B is not None and C is not None and adjacent_sum_180(B, C)) or \
               (C is not None and D is not None and adjacent_sum_180(C, D)) or \
               (D is not None and A is not None and adjacent_sum_180(D, A)):
                trapezoid = True
            if trapezoid:
                is_isos = (b is not None and d is not None and close(b, d)) or (a is not None and c is not None and close(a, c))
                if is_isos:
                    return "Hình thang cân", ["Hình thang cân", "Hình thang", "Tứ giác"]
                return "Hình thang", ["Hình thang", "Tứ giác"]
            return "Tứ giác thường", ["Tứ giác"]
    
    def draw_triangle(self, a: float, b: float, c: float, A: Optional[float], 
                     B: Optional[float], C: Optional[float]):
        """Draw triangle using side lengths"""
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Place first vertex at origin, second on x-axis
        # Use law of cosines to find coordinates
        if a is None or b is None or c is None:
            self.ax.text(0.5, 0.5, 'Không đủ dữ liệu để vẽ tam giác', 
                        ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
            return
        
        # Place vertices: A at (0,0), B at (c, 0), C calculated
        # Using law of cosines: a^2 = b^2 + c^2 - 2bc*cos(A)
        # Calculate angle A from sides using law of cosines
        if b > 0 and c > 0:
            cos_A = (b*b + c*c - a*a) / (2*b*c)
            cos_A = max(-1, min(1, cos_A))  # Clamp to valid range
            sin_A = math.sqrt(1 - cos_A*cos_A) if abs(cos_A) <= 1 else 0
        else:
            cos_A = 0
            sin_A = 0
        
        # Vertex coordinates
        # A at origin, B on x-axis at distance c, C at angle from A
        A_coord = (0, 0)
        B_coord = (c, 0)
        C_coord = (b * cos_A, b * sin_A)
        
        # Draw triangle
        triangle = plt.Polygon([A_coord, B_coord, C_coord], fill=False, edgecolor='blue', linewidth=2)
        self.ax.add_patch(triangle)
        
        # Label vertices
        self.ax.plot(*A_coord, 'ro', markersize=8)
        self.ax.plot(*B_coord, 'ro', markersize=8)
        self.ax.plot(*C_coord, 'ro', markersize=8)
        
        self.ax.text(A_coord[0], A_coord[1] - 0.1, 'A', ha='center', va='top', fontsize=12, fontweight='bold')
        self.ax.text(B_coord[0], B_coord[1] - 0.1, 'B', ha='center', va='top', fontsize=12, fontweight='bold')
        self.ax.text(C_coord[0], C_coord[1] + 0.1, 'C', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # Label sides
        mid_ab = ((A_coord[0] + B_coord[0])/2, (A_coord[1] + B_coord[1])/2)
        mid_bc = ((B_coord[0] + C_coord[0])/2, (B_coord[1] + C_coord[1])/2)
        mid_ca = ((C_coord[0] + A_coord[0])/2, (C_coord[1] + A_coord[1])/2)
        
        self.ax.text(mid_ab[0], mid_ab[1] - 0.15, f'c={c:.2f}', ha='center', va='top', fontsize=10)
        self.ax.text(mid_bc[0], mid_bc[1], f'a={a:.2f}', ha='center', va='center', fontsize=10)
        self.ax.text(mid_ca[0], mid_ca[1], f'b={b:.2f}', ha='center', va='center', fontsize=10)
        
        self.ax.set_xlim(-0.5, max(c, b*cos_A) + 0.5)
        self.ax.set_ylim(-0.5, b*sin_A + 0.5)
        self.ax.set_title('Tam giác', fontsize=14, fontweight='bold')
    
    def draw_rectangle(self, a: Optional[float], b: Optional[float], 
                      c: Optional[float], d: Optional[float],
                      A: Optional[float], B: Optional[float], 
                      C: Optional[float], D: Optional[float]):
        """Draw rectangle/quadrilateral"""
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Xác định loại hình để vẽ đúng đặc trưng
        shape = self.shape_var.get()
        # Hình chữ nhật: a==c, b==d, góc 90
        if shape == "rectangle" and a is not None and b is not None and c is not None and d is not None and \
            abs(a-c)<1e-6 and abs(b-d)<1e-6 and all(x is not None and abs(x-90)<0.1 for x in (A,B,C,D)):
            A_coord = (0, 0)
            B_coord = (a, 0)
            C_coord = (a, b)
            D_coord = (0, b)
        # Hình vuông: a==b==c==d, góc 90
        elif shape == "square" and a is not None and b is not None and c is not None and d is not None and \
            abs(a-b)<1e-6 and abs(a-c)<1e-6 and abs(a-d)<1e-6 and all(x is not None and abs(x-90)<0.1 for x in (A,B,C,D)):
            A_coord = (0, 0)
            B_coord = (a, 0)
            C_coord = (a, a)
            D_coord = (0, a)
        # Hình bình hành: a==c, b==d, góc đối bằng nhau
        elif shape == "parallelogram" and a is not None and b is not None and c is not None and d is not None and \
            abs(a-c)<1e-6 and abs(b-d)<1e-6 and A is not None and C is not None and abs(A-C)<1e-6:
            angle_A_rad = math.radians(A)
            A_coord = (0, 0)
            B_coord = (a, 0)
            D_coord = (b * math.cos(angle_A_rad), b * math.sin(angle_A_rad))
            C_coord = (B_coord[0] + D_coord[0], B_coord[1] + D_coord[1])
        # Hình thang: a, c là đáy, b, d là cạnh bên, biết chiều cao h
        elif shape == "trapezoid" and a is not None and c is not None and b is not None and d is not None:
            # Giả sử đáy a nằm dưới, đáy c nằm trên, b và d là cạnh bên, vẽ hình thang cân nếu có
            h = None
            if abs(b-d)<1e-6:
                # Hình thang cân
                h = math.sqrt(b**2 - ((c-a)/2)**2) if b > abs(c-a)/2 else b
                A_coord = (0, 0)
                B_coord = (a, 0)
                D_coord = ((a-c)/2, h)
                C_coord = (D_coord[0]+c, h)
            else:
                # Hình thang thường: vẽ đơn giản
                h = min(b, d)
                A_coord = (0, 0)
                B_coord = (a, 0)
                D_coord = (0, h)
                C_coord = (c, h)
        # Hình thoi: a==b==c==d, góc không nhất thiết 90
        elif shape == "rhombus" and a is not None and b is not None and c is not None and d is not None and \
            abs(a-b)<1e-6 and abs(a-c)<1e-6 and abs(a-d)<1e-6:
            # Dùng góc A nếu có
            angle_A_rad = math.radians(A) if A is not None else math.pi/3
            A_coord = (0, 0)
            B_coord = (a, 0)
            D_coord = (a * math.cos(angle_A_rad), a * math.sin(angle_A_rad))
            C_coord = (B_coord[0] + D_coord[0], B_coord[1] + D_coord[1])
        # Tứ giác thường: vẽ theo dữ liệu cạnh (ưu tiên a,b,c,d)
        elif a is not None and b is not None and c is not None and d is not None:
            # Vẽ tứ giác lồi đơn giản: A(0,0), B(a,0), C(a,b), D(0,d)
            A_coord = (0, 0)
            B_coord = (a, 0)
            C_coord = (a, b)
            D_coord = (0, d)
        else:
            self.ax.text(0.5, 0.5, 'Không đủ dữ liệu để vẽ tứ giác\n(Cần đủ 4 cạnh)', 
                        ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
            return

        # Vẽ tứ giác
        quad = plt.Polygon([A_coord, B_coord, C_coord, D_coord], fill=False, edgecolor='blue', linewidth=2)
        self.ax.add_patch(quad)
        # Label vertices
        for coord, label in [(A_coord, 'A'), (B_coord, 'B'), (C_coord, 'C'), (D_coord, 'D')]:
            self.ax.plot(*coord, 'ro', markersize=8)
            offset_x = -0.1 if coord[0] < 0.1 else 0.1
            offset_y = -0.1 if coord[1] < 0.1 else 0.1
            self.ax.text(coord[0] + offset_x, coord[1] + offset_y, label, 
                        ha='center', va='center', fontsize=12, fontweight='bold')
        # Label sides if available
        if a is not None:
            mid_ab = ((A_coord[0] + B_coord[0])/2, (A_coord[1] + B_coord[1])/2)
            self.ax.text(mid_ab[0], mid_ab[1] - 0.1, f'a={a:.2f}', ha='center', va='top', fontsize=10)
        if b is not None:
            mid_ad = ((A_coord[0] + D_coord[0])/2, (A_coord[1] + D_coord[1])/2)
            self.ax.text(mid_ad[0] - 0.1, mid_ad[1], f'b={b:.2f}', ha='right', va='center', fontsize=10)
        if c is not None:
            mid_bc = ((B_coord[0] + C_coord[0])/2, (B_coord[1] + C_coord[1])/2)
            self.ax.text(mid_bc[0], mid_bc[1] + 0.1, f'c={c:.2f}', ha='center', va='bottom', fontsize=10)
        if d is not None:
            mid_cd = ((C_coord[0] + D_coord[0])/2, (C_coord[1] + D_coord[1])/2)
            self.ax.text(mid_cd[0] + 0.1, mid_cd[1], f'd={d:.2f}', ha='left', va='center', fontsize=10)
        # Set limits
        all_x = [A_coord[0], B_coord[0], C_coord[0], D_coord[0]]
        all_y = [A_coord[1], B_coord[1], C_coord[1], D_coord[1]]
        self.ax.set_xlim(min(all_x) - 0.5, max(all_x) + 0.5)
        self.ax.set_ylim(min(all_y) - 0.5, max(all_y) + 0.5)
        self.ax.set_title('Tứ giác', fontsize=14, fontweight='bold')
    
    def detect_ssa_cases(self, assigned: Dict[str, float]) -> list:
        """
        Detect SSA pattern and return list of possible solution assignments.
        Pattern: exactly one angle (A/B/C) and at least two sides among a/b/c.
        Returns list of solution dicts (may be empty).
        """
        ang2side = {'A': 'a', 'B': 'b', 'C': 'c'}
        side_set = {'a', 'b', 'c'}

        # collect provided angle(s) and side(s)
        angles_provided = [k for k in assigned.keys() if k in ang2side.keys()]
        sides_provided = [k for k in assigned.keys() if k in side_set]

        # require exactly one angle and at least two sides
        if len(angles_provided) != 1 or len(sides_provided) < 2:
            return []

        Aname = angles_provided[0]
        opp_side = ang2side[Aname]
        # angle must be opposite one of the provided sides to be SSA
        if opp_side not in sides_provided:
            return []

        # identify the other provided side (the one not opposite the given angle)
        other_side = [s for s in sides_provided if s != opp_side]
        if not other_side:
            return []
        other = other_side[0]

        # numeric values
        a_val = assigned.get(opp_side)
        b_val = assigned.get(other)
        Adeg = assigned.get(Aname)
        if a_val is None or b_val is None or Adeg is None:
            return []

        sinA = math.sin(math.radians(Adeg))
        if abs(sinA) < 1e-12:
            return []

        # compute sin of the angle opposite the 'other' side
        sin_other = (b_val * sinA) / a_val
        # out of range => no solution
        if sin_other < -1.0 - 1e-12 or sin_other > 1.0 + 1e-12:
            return []
        # clamp numeric noise
        sin_other = max(-1.0, min(1.0, sin_other))

        sols = []
        try:
            primary = math.degrees(math.asin(sin_other))
        except ValueError:
            return []

        candidates = [primary]
        # second possible angle (supplement) when sin in (-1,1)
        if abs(abs(sin_other) - 1.0) > 1e-12:
            supplement = 180.0 - primary
            if abs(supplement - primary) > 1e-6:
                candidates.append(supplement)

        # mapping side->angle names and vice versa
        side_to_angle = {'a':'A','b':'B','c':'C'}
        angle_to_side = {v:k for k,v in side_to_angle.items()}

        for cand_angle in candidates:
            # other angle name (angle opposite the known 'other' side)
            other_angle_name = side_to_angle[other]
            third_angle_name = ({'A','B','C'} - {Aname, other_angle_name}).pop()
            Bdeg = cand_angle
            Cdeg = 180.0 - Adeg - Bdeg
            if Cdeg <= 0:
                continue
            # compute third side via law of sines (use opp_side as reference)
            third_side_name = angle_to_side[third_angle_name]
            # avoid division by zero
            if abs(sinA) < 1e-12:
                continue
            third_side = a_val * math.sin(math.radians(Cdeg)) / sinA
            # build solution dict (include original provided and computed entries)
            sol = {}
            for k,v in assigned.items():
                sol[k] = v
            # add computed angles and side
            sol[other_angle_name] = Bdeg
            sol[third_angle_name] = Cdeg
            sol[third_side_name] = third_side
            sols.append(sol)

        return sols
    
    def calculate(self):
        """Main calculation function"""
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Parse inputs (including perimeter and area)
        inputs = self.parse_inputs()
        if not inputs:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một giá trị!")
            return

        # --- KIỂM TRA LOGIC GÓC TAM GIÁC ---
        shape_sel = self.shape_var.get()
        tri_modes = {"triangle", "triangle_right", "triangle_equilateral", "triangle_isosceles"}
        is_triangle = shape_sel in tri_modes or (shape_sel == "auto" and any(k in inputs for k in ['a','b','c']))

        if is_triangle:
            # Kiểm tra từng góc
            for ang in ['A', 'B', 'C']:
                if ang in inputs and (inputs[ang] <= 0 or inputs[ang] >= 180):
                    messagebox.showerror("Lỗi", f"Góc {ang} = {inputs[ang]}° không hợp lệ cho tam giác (phải trong khoảng (0, 180))")
                    return
            # Kiểm tra tổng góc nếu nhập đủ
            angle_sum = sum(inputs.get(ang, 0) for ang in ['A', 'B', 'C'] if ang in inputs)
            if sum(1 for ang in ['A', 'B', 'C'] if ang in inputs) == 3 and (angle_sum < 180.0 - 1e-6 or angle_sum > 180.0 + 1e-6):
                messagebox.showerror("Lỗi", f"Tổng 3 góc tam giác = {angle_sum:.2f}° không hợp lệ (phải đúng bằng 180°)")
                return
            # --- Kiểm tra xung đột dữ liệu tam giác vuông ---
            if shape_sel == "triangle_right":
                # Nếu nhập đủ 3 cạnh, kiểm tra có phải tam giác vuông không
                a, b, c = inputs.get('a'), inputs.get('b'), inputs.get('c')
                if a and b and c:
                    # Sắp xếp để c là cạnh lớn nhất
                    sides = sorted([a, b, c])
                    if abs(sides[2]**2 - (sides[0]**2 + sides[1]**2)) > 1e-2:
                        messagebox.showerror("Lỗi", "Ba cạnh nhập vào không tạo thành tam giác vuông (không thỏa mãn định lý Pythagoras). Vui lòng kiểm tra lại!")
                        return
                # Nếu nhập góc vuông và cạnh đối diện không phải là cạnh lớn nhất
                for ang, side in zip(['A', 'B', 'C'], ['a', 'b', 'c']):
                    if ang in inputs and abs(inputs[ang] - 90) < 1e-2:
                        # Góc vuông phải đối diện cạnh lớn nhất
                        a, b, c = inputs.get('a'), inputs.get('b'), inputs.get('c')
                        if a and b and c:
                            max_side = max(a, b, c)
                            if abs(inputs.get(side, 0) - max_side) > 1e-2:
                                messagebox.showerror("Lỗi", f"Góc {ang} là góc vuông nhưng cạnh đối diện ({side}) không phải là cạnh lớn nhất. Dữ liệu không hợp lệ cho tam giác vuông.")
                                return

        # Validate perimeter, area, height
        if 'perimeter' in inputs and inputs['perimeter'] <= 0:
            messagebox.showerror("Lỗi", "Chu vi phải > 0")
            return
        if 'area' in inputs and inputs['area'] <= 0:
            messagebox.showerror("Lỗi", "Diện tích phải > 0")
            return
        if 'h' in inputs and inputs['h'] <= 0:
            messagebox.showerror("Lỗi", "Chiều cao (h) phải > 0")
            return
        
        # Validate inputs
        valid, msg = self.validate_inputs(inputs)
        if not valid:
            messagebox.showerror("Lỗi cạnh và góc nằm ngoài giá trị cho phép", msg)
            return
        
        # Choose network
        net, kind_msg = self.choose_network(inputs)
        if net is None:
            messagebox.showerror("Lỗi", kind_msg)
            return

        shape_sel = self.shape_var.get()

        # --- [FIX LOGIC] XÁC ĐỊNH LOẠI HÌNH (TAM GIÁC HAY TỨ GIÁC) ---
        tri_modes = {"triangle", "triangle_right", "triangle_equilateral", "triangle_isosceles"}
        quad_modes = {"square", "rectangle", "rhombus", "parallelogram", "trapezoid", "quadrilateral"}

        if shape_sel in tri_modes:
            is_triangle = True
        elif shape_sel in quad_modes:
            is_triangle = False
        else:  # auto
            is_triangle = "Tam giác" in kind_msg

        # --- Mapping tên tiếng Việt chuẩn để hiển thị ---
        expected_map = {
            "triangle": "Tam giác thường",
            "triangle_right": "Tam giác vuông",
            "triangle_equilateral": "Tam giác đều",
            "triangle_isosceles": "Tam giác cân",
            "square": "Hình vuông",
            "rectangle": "Hình chữ nhật",
            "rhombus": "Hình thoi",
            "parallelogram": "Hình bình hành",
            "trapezoid": "Hình thang",
            "quadrilateral": "Tứ giác thường"
        }
        expected_shape = expected_map.get(shape_sel)

        # --- SET INPUTS AND SOLVE NETWORK ---
        net.reset()
        for k, v in inputs.items():
            if k in net.vars:
                net.set_input(k, v, 'user')
        
        # Solve
        solve_result = net.solve()
        # Support both (ok, diagnostics) and just ok
        if isinstance(solve_result, tuple):
            ok, diagnostics = solve_result
        else:
            ok = solve_result
            diagnostics = None

        res = {k: net.vars[k].value if k in net.vars and net.vars[k].is_known() else None for k in net.vars}

        # --- Phân loại hình thực tế ---
        shape_name, inheritance = self.classify_shape(net, res, is_triangle)

        # --- [FIX HIỂN THỊ] Ưu tiên hình đã chọn thủ công ---
        manual_shapes = set(expected_map.keys())
        if shape_sel in manual_shapes:
            shape_name = expected_shape
            if expected_shape not in inheritance:
                inheritance.insert(0, expected_shape)
            inheritance = list(dict.fromkeys([expected_shape] + inheritance))

        # Display shape information prominently
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        self.results_text.insert(tk.END, f"📐 HÌNH DẠNG PHÁT HIỆN: {shape_name.upper()}\n")
        self.results_text.insert(tk.END, "=" * 50 + "\n")
        self.results_text.insert(tk.END, f"Phân loại: {' > '.join(inheritance)}\n\n")
        
        # Display results
        self.results_text.insert(tk.END, "Kết quả tính toán:\n")
        self.results_text.insert(tk.END, "-" * 40 + "\n")
        
        # Group results
        sides = {}
        angles = {}
        others = {}
        
        for name in sorted(res.keys()):
            value = res[name]
            if value is not None:
                if name in ('a', 'b', 'c', 'd'):
                    sides[name] = value
                elif name in ('A', 'B', 'C', 'D'):
                    angles[name] = value
                else:
                    others[name] = value
        
        if sides:
            self.results_text.insert(tk.END, "\nCạnh:\n")
            for name in sorted(sides.keys()):
                self.results_text.insert(tk.END, f"  {name} = {sides[name]:.6f}\n")
        
        if angles:
            self.results_text.insert(tk.END, "\nGóc (độ):\n")
            for name in sorted(angles.keys()):
                self.results_text.insert(tk.END, f"  {name} = {angles[name]:.6f}°\n")
        
        if others:
            self.results_text.insert(tk.END, "\nKhác:\n")
            priority_vars = ['perimeter', 'area', 'h']
            for name in priority_vars:
                if name in others:
                    label = "Chu vi" if name == 'perimeter' else ("Diện tích" if name == 'area' else "Chiều cao")
                    self.results_text.insert(tk.END, f"  {label} ({name}) = {others[name]:.6f}\n")
            for name in sorted(others.keys()):
                if name not in priority_vars:
                    self.results_text.insert(tk.END, f"  {name} = {others[name]:.6f}\n")
        
        # Validation checks
        if is_triangle:
            A, B, C = res.get('A'), res.get('B'), res.get('C')
            if A is not None and B is not None and C is not None:
                angle_sum = A + B + C
                if abs(angle_sum - 180.0) > 1e-3:
                    self.results_text.insert(tk.END, 
                        f"⚠ LỖI: Tổng góc tam giác = {angle_sum:.2f}° (phải = 180°)\n")
        else:
            A, B, C, D = res.get('A'), res.get('B'), res.get('C'), res.get('D')
            if A is not None and B is not None and C is not None and D is not None:
                angle_sum = A + B + C + D
                if abs(angle_sum - 360.0) > 1e-2:
                    self.results_text.insert(tk.END, 
                        f"⚠ CẢNH BÁO: Tổng góc tứ giác = {angle_sum:.2f}° (phải = 360°)\n")
        
        # Draw graph
        if is_triangle:
            a_val = res.get('a')
            b_val = res.get('b')
            c_val = res.get('c')
            A_val = res.get('A')
            B_val = res.get('B')
            C_val = res.get('C')
            self.draw_triangle(a_val, b_val, c_val, A_val, B_val, C_val)
        else:
            a_val = res.get('a')
            b_val = res.get('b')
            c_val = res.get('c')
            d_val = res.get('d')
            A_val = res.get('A')
            B_val = res.get('B')
            C_val = res.get('C')
            D_val = res.get('D')
            self.draw_rectangle(a_val, b_val, c_val, d_val, A_val, B_val, C_val, D_val)
        self.canvas.draw()

    def update_graph_view(self):
        """Cập nhật vùng đồ thị theo chế độ hiển thị"""
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        # Chỉ còn vẽ hình học
        if self.last_network is None or self.last_result is None:
            self.ax.text(0.5, 0.5, 'Nhập dữ liệu và nhấn "Tính toán"\nđể xem đồ thị', 
                         ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
        else:
            if self.last_is_triangle:
                a_val = self.last_result.get('a')
                b_val = self.last_result.get('b')
                c_val = self.last_result.get('c')
                A_val = self.last_result.get('A')
                B_val = self.last_result.get('B')
                C_val = self.last_result.get('C')
                self.draw_triangle(a_val, b_val, c_val, A_val, B_val, C_val)
            else:
                a_val = self.last_result.get('a')
                b_val = self.last_result.get('b')
                c_val = self.last_result.get('c')
                d_val = self.last_result.get('d')
                A_val = self.last_result.get('A')
                B_val = self.last_result.get('B')
                C_val = self.last_result.get('C')
                D_val = self.last_result.get('D')
                self.draw_rectangle(a_val, b_val, c_val, d_val, A_val, B_val, C_val, D_val)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = GeometryCalculatorGUI(root)
    root.mainloop()