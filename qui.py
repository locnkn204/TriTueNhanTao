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
        ttk.Radiobutton(shape_frame, text="Tam giác thường", variable=self.shape_var, 
                       value="triangle").grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tam giác vuông", variable=self.shape_var, 
                       value="triangle_right").grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Quadrilateral options
        ttk.Label(shape_frame, text="Tứ giác:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5,2))
        ttk.Radiobutton(shape_frame, text="Hình vuông", variable=self.shape_var, 
                       value="square").grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Hình chữ nhật", variable=self.shape_var, 
                       value="rectangle").grid(row=2, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(shape_frame, text="Tứ giác thường", variable=self.shape_var, 
                       value="quadrilateral").grid(row=2, column=3, sticky=tk.W, padx=5)
        
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
        
        return True, ""
    
    def choose_network(self, inputs: Dict[str, float]) -> Tuple[Optional[ConstraintNetwork], str]:
        """Choose which network to use based on shape selection or auto-detect"""
        shape = self.shape_var.get()
        
        if shape == "triangle" or shape == "triangle_right":
            msg = "Tam giác vuông (đã chọn)" if shape == "triangle_right" else "Tam giác (đã chọn)"
            net = kb.create_triangle_network()
            # If triangle_right, set one angle to 90 if not provided
            if shape == "triangle_right" and 'A' not in inputs and 'B' not in inputs and 'C' not in inputs:
                # Will be handled by constraints, but we can hint
                pass
            return net, msg
        elif shape == "square":
            net = kb.create_rectangle_network()
            # For square, we can set constraints: a=b=c=d, A=B=C=D=90
            # But let the solver handle it based on inputs
            return net, "Hình vuông (đã chọn)"
        elif shape == "rectangle":
            return kb.create_rectangle_network(), "Hình chữ nhật (đã chọn)"
        elif shape == "quadrilateral":
            return kb.create_rectangle_network(), "Tứ giác (đã chọn)"
        
        # Auto-detect
        tri_side_names = {'a', 'b', 'c'}
        rect_side_names = {'a', 'b', 'c', 'd'}
        tri_angle_names = {'A', 'B', 'C'}
        rect_angle_names = {'A', 'B', 'C', 'D'}
        
        tri_side_count = sum(1 for n in inputs if n in tri_side_names)
        rect_side_count = sum(1 for n in inputs if n in rect_side_names)
        tri_angle_count = sum(1 for n in inputs if n in tri_angle_names)
        rect_angle_count = sum(1 for n in inputs if n in rect_angle_names)
        has_d = ('d' in inputs) or ('D' in inputs)
        
        if has_d:
            return kb.create_rectangle_network(), "Tứ giác (có cạnh/góc d)"
        
        # If 3 sides or 3 angles -> triangle
        if tri_side_count >= 3 or tri_angle_count >= 3:
            a = inputs.get('a')
            b = inputs.get('b')
            c = inputs.get('c')
            if a is not None and b is not None and c is not None:
                if not ((a + b > c) and (a + c > b) and (b + c > a)):
                    return kb.create_triangle_network(), "Tam giác (cảnh báo: có thể vi phạm bất đẳng thức tam giác)"
            return kb.create_triangle_network(), "Tam giác (tự động)"
        
        # If 4 sides or 4 angles -> quadrilateral
        if rect_side_count >= 4 or rect_angle_count >= 4:
            return kb.create_rectangle_network(), "Tứ giác (tự động)"
        
        # Check for right angle + adjacent sides -> rectangle
        right_angles = [name for name, val in inputs.items()
                       if name in rect_angle_names and abs(val - 90.0) <= 0.1]
        if right_angles:
            assigned_sides = set(n for n in inputs if n in rect_side_names)
            adjacent_pairs = [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')]
            has_adjacent = any(p[0] in assigned_sides and p[1] in assigned_sides for p in adjacent_pairs)
            if has_adjacent and tri_side_count < 3:
                return kb.create_rectangle_network(), "Tứ giác (góc vuông + cạnh kề)"
            if len(assigned_sides) >= 2 and tri_side_count < 3:
                return kb.create_rectangle_network(), "Tứ giác (góc vuông, ưu tiên tránh gán tam giác)"
        
        if rect_side_count >= 2 and rect_angle_count >= 2:
            return kb.create_rectangle_network(), "Tứ giác (dữ liệu hỗn hợp)"
        if rect_side_count >= 2 and tri_side_count == 0:
            return kb.create_rectangle_network(), "Tứ giác (ưu tiên)"
        
        # Default: prefer triangle if has any triangle data
        if tri_side_count > 0 or tri_angle_count > 0:
            return kb.create_triangle_network(), "Tam giác (mặc định)"
        elif rect_side_count > 0 or rect_angle_count > 0:
            return kb.create_rectangle_network(), "Tứ giác (mặc định)"
        
        return None, "Không đủ dữ liệu"
    
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
        
        # Ưu tiên vẽ hình bình hành khi biết góc khác 90°, sau đó tới chữ nhật
        if a is not None and b is not None and A is not None and abs(A - 90) > 0.1:
            # Parallelogram with angle A
            angle_A_rad = math.radians(A)
            A_coord = (0, 0)
            B_coord = (a, 0)
            D_coord = (b * math.cos(angle_A_rad), b * math.sin(angle_A_rad))
            C_coord = (B_coord[0] + D_coord[0], B_coord[1] + D_coord[1])
        elif a is not None and b is not None:
            # Rectangle case - use a and b as adjacent sides
            A_coord = (0, 0)
            B_coord = (a, 0)
            C_coord = (a, b)
            D_coord = (0, b)
        elif a is not None and c is not None and b is not None:
            # Parallelogram: a opposite c, b opposite d, assume 90 degrees
            A_coord = (0, 0)
            B_coord = (a, 0)
            D_coord = (0, b)
            C_coord = (a, b)
        else:
            self.ax.text(0.5, 0.5, 'Không đủ dữ liệu để vẽ tứ giác\n(Cần ít nhất 2 cạnh kề nhau)', 
                        ha='center', va='center', fontsize=12, transform=self.ax.transAxes)
            return
        
        # Draw quadrilateral
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
        
        # Validate perimeter and area if provided
        if 'perimeter' in inputs and inputs['perimeter'] <= 0:
            messagebox.showerror("Lỗi", "Chu vi phải > 0")
            return
        if 'area' in inputs and inputs['area'] <= 0:
            messagebox.showerror("Lỗi", "Diện tích phải > 0")
            return
        
        # Validate inputs
        valid, msg = self.validate_inputs(inputs)
        if not valid:
            messagebox.showerror("Lỗi", msg)
            return
        
        # Choose network
        net, kind_msg = self.choose_network(inputs)
        if net is None:
            messagebox.showerror("Lỗi", kind_msg)
            return
        
        # Determine if triangle
        shape_sel = self.shape_var.get()
        is_triangle = (shape_sel in ("triangle", "triangle_right") or 
                      (shape_sel == "auto" and kind_msg.startswith("Tam giác")))
        
        # Early triangle inequality check
        if is_triangle:
            a = inputs.get('a')
            b = inputs.get('b')
            c = inputs.get('c')
            if a is not None and b is not None and c is not None:
                if not ((a + b > c) and (a + c > b) and (b + c > a)):
                    self.results_text.insert(tk.END, 
                        f"⚠ CẢNH BÁO: Bất đẳng thức tam giác có thể bị vi phạm!\n"
                        f"  a={a}, b={b}, c={c}\n"
                        f"  (a+b > c, a+c > b, b+c > a phải đúng)\n\n")
        
        # Check for SSA ambiguous case (only for triangles)
        if is_triangle:
            ssa_solutions = self.detect_ssa_cases(inputs)
            if ssa_solutions and len(ssa_solutions) > 1:
                self.results_text.insert(tk.END, 
                    f"⚠ Phát hiện trường hợp SSA mơ hồ: {len(ssa_solutions)} nghiệm có thể.\n\n")
                # Process each SSA candidate
                for idx, sol_assign in enumerate(ssa_solutions, start=1):
                    self.results_text.insert(tk.END, f"--- Nghiệm SSA #{idx} ---\n")
                    tri_candidate = kb.create_triangle_network()
                    tri_candidate.reset()
                    for k, v in sol_assign.items():
                        if v is not None:
                            tri_candidate.set_input(k, v, source='user')
                    ok, diagnostics = tri_candidate.solve()
                    res = tri_candidate.get_results()
                    
                    # Display candidate results
                    for name in sorted(res.keys()):
                        value = res[name]
                        if value is not None:
                            if name in ('a', 'b', 'c'):
                                self.results_text.insert(tk.END, f"  {name} = {value:.6f}\n")
                            elif name in ('A', 'B', 'C'):
                                self.results_text.insert(tk.END, f"  {name} = {value:.6f}°\n")
                    self.results_text.insert(tk.END, "\n")
                    
                    # Draw first candidate
                    if idx == 1:
                        a_val = res.get('a')
                        b_val = res.get('b')
                        c_val = res.get('c')
                        if a_val is not None and b_val is not None and c_val is not None:
                            self.draw_triangle(a_val, b_val, c_val, 
                                             res.get('A'), res.get('B'), res.get('C'))
                
                self.canvas.draw()
                self.results_text.see(tk.END)
                return  # Don't process normal solve for SSA cases
        
        # Set inputs to network (including perimeter and area)
        net.reset()
        
        # Handle special shape constraints
        shape_sel = self.shape_var.get()
        if shape_sel == "triangle_right":
            # For right triangle, if no angle is 90, set one (prefer C)
            if 'A' not in inputs and 'B' not in inputs and 'C' not in inputs:
                inputs['C'] = 90.0
        elif shape_sel == "square":
            # For square, if one side is given, set all equal
            # If one angle is 90, set all to 90
            sides = [inputs.get('a'), inputs.get('b'), inputs.get('c'), inputs.get('d')]
            sides_given = [s for s in sides if s is not None]
            if len(sides_given) == 1:
                val = sides_given[0]
                if 'a' not in inputs: inputs['a'] = val
                if 'b' not in inputs: inputs['b'] = val
                if 'c' not in inputs: inputs['c'] = val
                if 'd' not in inputs: inputs['d'] = val
            angles = [inputs.get('A'), inputs.get('B'), inputs.get('C'), inputs.get('D')]
            angles_given = [a for a in angles if a is not None]
            if len(angles_given) == 1 and abs(angles_given[0] - 90) < 0.1:
                if 'A' not in inputs: inputs['A'] = 90.0
                if 'B' not in inputs: inputs['B'] = 90.0
                if 'C' not in inputs: inputs['C'] = 90.0
                if 'D' not in inputs: inputs['D'] = 90.0
        elif not is_triangle:
            # Heuristic cho tứ giác: nếu có góc vuông và thiếu cạnh đối, copy đối xứng
            right_angle_any = any(name in ('A','B','C','D') and abs(val-90) <= 0.1 for name,val in inputs.items())
            if right_angle_any:
                if 'a' in inputs and 'c' not in inputs:
                    inputs['c'] = inputs['a']
                if 'c' in inputs and 'a' not in inputs:
                    inputs['a'] = inputs['c']
                if 'b' in inputs and 'd' not in inputs:
                    inputs['d'] = inputs['b']
                if 'd' in inputs and 'b' not in inputs:
                    inputs['b'] = inputs['d']
                # nếu chỉ 1 cạnh được nhập, giả định hình vuông
                known_sides = [inputs[s] for s in ('a','b','c','d') if s in inputs]
                if len(known_sides) == 1:
                    val = known_sides[0]
                    for s in ('a','b','c','d'):
                        if s not in inputs:
                            inputs[s] = val
        
        for name, value in inputs.items():
            if name in net.vars:  # Only set if variable exists in network
                net.set_input(name, value, source='user')
        
        # Solve
        self.results_text.insert(tk.END, f"Đang tính toán ({kind_msg})...\n\n")
        ok, diagnostics = net.solve()
        
        if not ok:
            self.results_text.insert(tk.END, 
                "⚠ Solver đạt giới hạn vòng lặp; kết quả có thể không đầy đủ.\n")
            if diagnostics:
                rounds = diagnostics.get('rounds', '?')
                blocked = diagnostics.get('blocked_constraints', [])
                self.results_text.insert(tk.END, f"  Vòng lặp: {rounds}, Ràng buộc bị chặn: {blocked}\n\n")
        
        # Get results
        res = net.get_results()

        # Validation & thiếu dữ liệu
        if is_triangle:
            for ang_name in ('A','B','C'):
                ang_val = res.get(ang_name)
                if ang_val is not None and (ang_val <= 0 or ang_val >= 180):
                    self.results_text.insert(tk.END, f"\n⚠ Lỗi: Góc {ang_name} không hợp lệ cho tam giác (0 < góc < 180).\n")
                    return
            angs = [res.get('A'), res.get('B'), res.get('C')]
            if all(a is not None for a in angs):
                if abs(sum(angs) - 180.0) > 1e-3:
                    self.results_text.insert(tk.END, "\n⚠ Lỗi: Tổng 3 góc tam giác phải = 180°.\n")
                    return
            known_basic = [k for k in ('a','b','c','A','B','C') if res.get(k) is not None]
            if len(known_basic) < 3:
                self.results_text.insert(tk.END, "\n⚠ Dữ liệu chưa đủ để xác định tam giác. Cần thêm ít nhất 3 giá trị cạnh/góc.\n")
                return
            # cảnh báo góc nhập sai so với tính toán
            for ang_name in ('A','B','C'):
                if ang_name in inputs and res.get(ang_name) is not None and abs(inputs[ang_name] - res[ang_name]) > 0.5:
                    self.results_text.insert(tk.END, f"\n⚠ Góc {ang_name} nhập ({inputs[ang_name]}°) lệch so với tính toán ({res[ang_name]:.2f}°). Dùng giá trị tính.\n")
            a_val,b_val,c_val = res.get('a'), res.get('b'), res.get('c')
            if all(x is not None for x in (a_val,b_val,c_val)):
                avg = (a_val+b_val+c_val)/3.0
                if avg > 0:
                    max_dev = max(abs(a_val-avg), abs(b_val-avg), abs(c_val-avg))/avg
                    if max_dev < 0.001:
                        self.results_text.insert(tk.END, "\nGhi chú: Tam giác gần đều (sai số <0.1%).\n")
        else:
            quads = [res.get('A'), res.get('B'), res.get('C'), res.get('D')]
            if all(a is not None for a in quads):
                if abs(sum(quads) - 360.0) > 1e-2:
                    self.results_text.insert(tk.END, "\n⚠ Lỗi: Tổng 4 góc tứ giác phải = 360°.\n")
                    return
        
        # Classify shape
        shape_name, inheritance = self.classify_shape(net, res, is_triangle)
        
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
            # Prioritize perimeter and area
            priority_vars = ['perimeter', 'area']
            for name in priority_vars:
                if name in others:
                    label = "Chu vi" if name == 'perimeter' else "Diện tích"
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
                        f"\n⚠ LỖI: Tổng góc tam giác = {angle_sum:.2f}° (phải = 180°)\n")
        else:
            A, B, C, D = res.get('A'), res.get('B'), res.get('C'), res.get('D')
            if A is not None and B is not None and C is not None and D is not None:
                angle_sum = A + B + C + D
                if abs(angle_sum - 360.0) > 1e-2:
                    self.results_text.insert(tk.END, 
                        f"\n⚠ CẢNH BÁO: Tổng góc tứ giác = {angle_sum:.2f}° (phải = 360°)\n")
        
        # Draw graph
        if is_triangle:
            a_val = res.get('a')
            b_val = res.get('b')
            c_val = res.get('c')
            A_val = res.get('A')
            B_val = res.get('B')
            C_val = res.get('C')
            if a_val is not None and b_val is not None and c_val is not None:
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
        self.results_text.see(tk.END)


def main():
    root = tk.Tk()
    app = GeometryCalculatorGUI(root)  # Initialize GUI application
    root.mainloop()


if __name__ == "__main__":
    main()
