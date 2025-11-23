import math
from engine import ConstraintNetwork, Constraint, safe_sqrt, clamp

# --- HÀM TẠO MẠNG NGỮ NGHĨA CHO TAM GIÁC ---
def create_triangle_network() -> ConstraintNetwork:
    net = ConstraintNetwork()
    # variables (degrees for angles) with descriptions
    net.add_variable('a', "Cạnh a (đơn vị chiều dài)")
    net.add_variable('b', "Cạnh b (đơn vị chiều dài)")
    net.add_variable('c', "Cạnh c (đơn vị chiều dài)")
    net.add_variable('d', "Cạnh d (không dùng trong tam giác, dành cho tứ giác)")  # thêm d
    net.add_variable('A', "Góc A (°), đối diện cạnh a")
    net.add_variable('B', "Góc B (°), đối diện cạnh b")
    net.add_variable('C', "Góc C (°), đối diện cạnh c")
    net.add_variable('D', "Góc D (không dùng trong tam giác, dành cho tứ giác)")  # thêm D
    net.add_variable('perimeter', "Chu vi = a + b + c")
    net.add_variable('area', "Diện tích tam giác")

    # --- MỚI: Nửa chu vi, bán kính trong/ngoại tiếp, exradii, medians, bisectors, heights ---
    net.add_variable('s', "Nửa chu vi (s = (a+b+c)/2)")
    net.add_variable('R', "Bán kính ngoại tiếp (circumradius)")
    net.add_variable('r', "Bán kính nội tiếp (inradius)")
    net.add_variable('r_a', "Exradius đối với a")
    net.add_variable('r_b', "Exradius đối với b")
    net.add_variable('r_c', "Exradius đối với c")
    net.add_variable('m_a', "Median từ A (độ dài trung tuyến tới a)")
    net.add_variable('m_b', "Median từ B")
    net.add_variable('m_c', "Median từ C")
    net.add_variable('l_a', "Angle bisector chiều dài từ A")
    net.add_variable('l_b', "Angle bisector chiều dài từ B")
    net.add_variable('l_c', "Angle bisector chiều dài từ C")
    net.add_variable('h_a', "Chiều cao ứng với cạnh a")
    net.add_variable('h_b', "Chiều cao ứng với cạnh b")
    net.add_variable('h_c', "Chiều cao ứng với cạnh c")
    # angle sum forward constraints
    def sum_A_consistency(vals):
        # Nếu cả 3 góc đã biết, kiểm tra tổng trước khi ghi đè
        if all(k in vals for k in ('A','B','C')):
            total = vals['A'] + vals['B'] + vals['C']
            if abs(total - 180.0) > 1e-2:
                return None
        return 180.0 - vals['B'] - vals['C']
    def sum_B_consistency(vals):
        if all(k in vals for k in ('A','B','C')):
            total = vals['A'] + vals['B'] + vals['C']
            if abs(total - 180.0) > 1e-2:
                return None
        return 180.0 - vals['A'] - vals['C']
    def sum_C_consistency(vals):
        if all(k in vals for k in ('A','B','C')):
            total = vals['A'] + vals['B'] + vals['C']
            if abs(total - 180.0) > 1e-2:
                return None
        return 180.0 - vals['A'] - vals['B']
    net.add_constraint(Constraint(
        name="sum_A",
        nodes=['A','B','C'],
        forward_func=sum_A_consistency,
        dependencies=['B','C'],
        target='A',
        description="A = 180 - B - C (with consistency check)"
    ))
    net.add_constraint(Constraint(
        name="sum_B",
        nodes=['A','B','C'],
        forward_func=sum_B_consistency,
        dependencies=['A','C'],
        target='B',
        description="B = 180 - A - C (with consistency check)"
    ))
    net.add_constraint(Constraint(
        name="sum_C",
        nodes=['A','B','C'],
        forward_func=sum_C_consistency,
        dependencies=['A','B'],
        target='C',
        description="C = 180 - A - B (with consistency check)"
    ))
    # law of sines as flexible (can produce many unknowns)
    def law_sines(netw, known, unknown):
        # if at least one side-angle pair known, compute others
        pairs = [('a','A'),('b','B'),('c','C')]
        ratio = None
        for s, ang in pairs:
            if netw.vars[s].is_known() and netw.vars[ang].is_known():
                a = netw.vars[s].value
                Adeg = netw.vars[ang].value
                if Adeg is None:
                    continue
                sinA = math.sin(math.radians(Adeg))
                if abs(sinA) < 1e-12:
                    continue
                ratio = a / sinA
                break
        if ratio is None:
            return None
        res = {}
        ambiguous_detected = False
        for s, ang in pairs:
            # compute side if angle known
            if not netw.vars[s].is_known() and netw.vars[ang].is_known():
                res[s] = ratio * math.sin(math.radians(netw.vars[ang].value))
            # compute angle if side known
            if not netw.vars[ang].is_known() and netw.vars[s].is_known():
                sinv = netw.vars[s].value / ratio
                if -1.0 <= sinv <= 1.0:
                    angle_acute = math.degrees(math.asin(clamp(sinv, -1, 1)))
                    # Check if obtuse angle is also valid
                    if abs(abs(sinv) - 1.0) > 1e-9:  # Not 90°
                        angle_obtuse = 180.0 - angle_acute
                        res[ang] = angle_acute
                        ambiguous_detected = True
                        # Store metadata for SSA detection
                        if not hasattr(netw, '_ssa_warning'):
                            netw._ssa_warning = True
                    else:
                        res[ang] = angle_acute
        return res or None

    net.add_constraint(Constraint(
        name="law_sines",
        nodes=['a','b','c','A','B','C'],
        flex_func=law_sines,
        description="law of sines flexible"
    ))

    # law of cosines forward for sides
    def cos_side(vals, side):
        if side == 'a':
            return safe_sqrt(vals['b']**2 + vals['c']**2 - 2*vals['b']*vals['c']*math.cos(math.radians(vals['A'])))
        if side == 'b':
            return safe_sqrt(vals['a']**2 + vals['c']**2 - 2*vals['a']*vals['c']*math.cos(math.radians(vals['B'])))
        return safe_sqrt(vals['a']**2 + vals['b']**2 - 2*vals['a']*vals['b']*math.cos(math.radians(vals['C'])))

    net.add_constraint(Constraint(
        name="cos_a",
        nodes=['a','b','c','A'],
        forward_func=lambda v: cos_side(v, 'a'),
        dependencies=['b','c','A'],
        target='a'
    ))
    net.add_constraint(Constraint(
        name="cos_b",
        nodes=['b','a','c','B'],
        forward_func=lambda v: cos_side(v, 'b'),
        dependencies=['a','c','B'],
        target='b'
    ))
    net.add_constraint(Constraint(
        name="cos_c",
        nodes=['c','a','b','C'],
        forward_func=lambda v: cos_side(v, 'c'),
        dependencies=['a','b','C'],
        target='c'
    ))

    # cos -> angles (safe clamp)
    def cos_angle(vals, angle):
        if angle == 'A':
            num = vals['b']**2 + vals['c']**2 - vals['a']**2
            den = 2*vals['b']*vals['c']
        elif angle == 'B':
            num = vals['a']**2 + vals['c']**2 - vals['b']**2
            den = 2*vals['a']*vals['c']
        else:
            num = vals['a']**2 + vals['b']**2 - vals['c']**2
            den = 2*vals['a']*vals['b']
        if den == 0:
            return None
        val = clamp(num/den, -1.0, 1.0)
        return math.degrees(math.acos(val))

    net.add_constraint(Constraint(
        name="angle_A_from_cos",
        nodes=['a','b','c','A'],
        forward_func=lambda v: cos_angle(v, 'A'),
        dependencies=['a','b','c'],
        target='A'
    ))
    net.add_constraint(Constraint(
        name="angle_B_from_cos",
        nodes=['a','b','c','B'],
        forward_func=lambda v: cos_angle(v, 'B'),
        dependencies=['a','b','c'],
        target='B'
    ))
    net.add_constraint(Constraint(
        name="angle_C_from_cos",
        nodes=['a','b','c','C'],
        forward_func=lambda v: cos_angle(v, 'C'),
        dependencies=['a','b','c'],
        target='C'
    ))

    # perimeter
    net.add_constraint(Constraint(
        name="perimeter",
        nodes=['a','b','c','perimeter'],
        forward_func=lambda v: v['a'] + v['b'] + v['c'],
        dependencies=['a','b','c'],
        target='perimeter'
    ))
    
    # Reverse perimeter: if perimeter and 2 sides known, compute third side
    def perimeter_reverse(netw, known, unknown):
        res = {}
        if 'perimeter' in known and 'perimeter' not in unknown:
            p = netw.vars['perimeter'].value
            if p is not None and p > 0:
                sides = ['a', 'b', 'c']
                known_sides = [s for s in sides if netw.vars[s].is_known()]
                unknown_sides = [s for s in sides if not netw.vars[s].is_known()]
                if len(known_sides) == 2 and len(unknown_sides) == 1:
                    known_sum = sum(netw.vars[s].value for s in known_sides)
                    computed_side = p - known_sum
                    # VALIDATION
                    if computed_side <= 0:
                        return None  # Invalid: side must be positive
                    # Triangle inequality pre-check
                    sides_values = {s: netw.vars[s].value for s in known_sides}
                    sides_values[unknown_sides[0]] = computed_side
                    a_val = sides_values.get('a', computed_side)
                    b_val = sides_values.get('b', computed_side)
                    c_val = sides_values.get('c', computed_side)
                    # Quick triangle inequality check
                    if not ((a_val + b_val > c_val + 1e-6) and 
                            (a_val + c_val > b_val + 1e-6) and 
                            (b_val + c_val > a_val + 1e-6)):
                        return None  # Would violate triangle inequality
                    res[unknown_sides[0]] = computed_side
        return res or None
    
    net.add_constraint(Constraint(
        name="perimeter_reverse",
        nodes=['a','b','c','perimeter'],
        flex_func=perimeter_reverse,
        description="Reverse perimeter: compute side from perimeter and 2 other sides"
    ))

    # semi-perimeter s = (a+b+c)/2
    net.add_constraint(Constraint(
        name="semi_perimeter",
        nodes=['a','b','c','s'],
        forward_func=lambda v: (v['a'] + v['b'] + v['c']) / 2.0,
        dependencies=['a','b','c'],
        target='s',
        description="s = (a+b+c)/2"
    ))

    # circumradius R = a*b*c / (4*Area)
    net.add_constraint(Constraint(
        name="circumradius",
        nodes=['a','b','c','area','R'],
        forward_func=lambda v: (v['a'] * v['b'] * v['c']) / (4.0 * v['area']) if v['area'] not in (None, 0) else None,
        dependencies=['a','b','c','area'],
        target='R',
        description="R = a*b*c/(4*Area)"
    ))

    # inradius r = Area / s
    net.add_constraint(Constraint(
        name="inradius",
        nodes=['area','s','r'],
        forward_func=lambda v: (v['area'] / v['s']) if v['s'] not in (None, 0) else None,
        dependencies=['area','s'],
        target='r',
        description="r = Area / s"
    ))

    # exradii r_a = Area / (s - a) etc.
    net.add_constraint(Constraint(
        name="exradius_a",
        nodes=['area','s','a','r_a'],
        forward_func=lambda v: (v['area'] / (v['s'] - v['a'])) if (v['s'] is not None and v['a'] is not None and abs(v['s'] - v['a']) > 1e-12) else None,
        dependencies=['area','s','a'],
        target='r_a',
        description="r_a = Area / (s - a)"
    ))
    net.add_constraint(Constraint(
        name="exradius_b",
        nodes=['area','s','b','r_b'],
        forward_func=lambda v: (v['area'] / (v['s'] - v['b'])) if (v['s'] is not None and v['b'] is not None and abs(v['s'] - v['b']) > 1e-12) else None,
        dependencies=['area','s','b'],
        target='r_b',
        description="r_b = Area / (s - b)"
    ))
    net.add_constraint(Constraint(
        name="exradius_c",
        nodes=['area','s','c','r_c'],
        forward_func=lambda v: (v['area'] / (v['s'] - v['c'])) if (v['s'] is not None and v['c'] is not None and abs(v['s'] - v['c']) > 1e-12) else None,
        dependencies=['area','s','c'],
        target='r_c',
        description="r_c = Area / (s - c)"
    ))

    # medians (Apollonius): m_a = 0.5*sqrt(2b^2 + 2c^2 - a^2)
    net.add_constraint(Constraint(
        name="median_a",
        nodes=['a','b','c','m_a'],
        forward_func=lambda v: safe_sqrt(0.25 * (2*(v['b']**2 + v['c']**2) - v['a']**2)),
        dependencies=['a','b','c'],
        target='m_a',
        description="Median m_a"
    ))
    net.add_constraint(Constraint(
        name="median_b",
        nodes=['a','b','c','m_b'],
        forward_func=lambda v: safe_sqrt(0.25 * (2*(v['a']**2 + v['c']**2) - v['b']**2)),
        dependencies=['a','b','c'],
        target='m_b',
        description="Median m_b"
    ))
    net.add_constraint(Constraint(
        name="median_c",
        nodes=['a','b','c','m_c'],
        forward_func=lambda v: safe_sqrt(0.25 * (2*(v['a']**2 + v['b']**2) - v['c']**2)),
        dependencies=['a','b','c'],
        target='m_c',
        description="Median m_c"
    ))

    # angle bisector length l_a = 2bc * cos(A/2) / (b + c)
    net.add_constraint(Constraint(
        name="bisector_a",
        nodes=['b','c','A','l_a'],
        forward_func=lambda v: (2.0 * v['b'] * v['c'] * math.cos(math.radians(v['A'] / 2.0)) / (v['b'] + v['c'])) if (v['b'] is not None and v['c'] is not None and (v['b'] + v['c']) != 0 and v['A'] is not None) else None,
        dependencies=['b','c','A'],
        target='l_a',
        description="Angle bisector l_a"
    ))
    net.add_constraint(Constraint(
        name="bisector_b",
        nodes=['a','c','B','l_b'],
        forward_func=lambda v: (2.0 * v['a'] * v['c'] * math.cos(math.radians(v['B'] / 2.0)) / (v['a'] + v['c'])) if (v['a'] is not None and v['c'] is not None and (v['a'] + v['c']) != 0 and v['B'] is not None) else None,
        dependencies=['a','c','B'],
        target='l_b',
        description="Angle bisector l_b"
    ))
    net.add_constraint(Constraint(
        name="bisector_c",
        nodes=['a','b','C','l_c'],
        forward_func=lambda v: (2.0 * v['a'] * v['b'] * math.cos(math.radians(v['C'] / 2.0)) / (v['a'] + v['b'])) if (v['a'] is not None and v['b'] is not None and (v['a'] + v['b']) != 0 and v['C'] is not None) else None,
        dependencies=['a','b','C'],
        target='l_c',
        description="Angle bisector l_c"
    ))

    # heights h_a = 2*area / a
    net.add_constraint(Constraint(
        name="height_a",
        nodes=['area','a','h_a'],
        forward_func=lambda v: (2.0 * v['area'] / v['a']) if (v['a'] is not None and v['a'] != 0 and v['area'] is not None) else None,
        dependencies=['area','a'],
        target='h_a',
        description="Height h_a"
    ))
    net.add_constraint(Constraint(
        name="height_b",
        nodes=['area','b','h_b'],
        forward_func=lambda v: (2.0 * v['area'] / v['b']) if (v['b'] is not None and v['b'] != 0 and v['area'] is not None) else None,
        dependencies=['area','b'],
        target='h_b',
        description="Height h_b"
    ))
    net.add_constraint(Constraint(
        name="height_c",
        nodes=['area','c','h_c'],
        forward_func=lambda v: (2.0 * v['area'] / v['c']) if (v['c'] is not None and v['c'] != 0 and v['area'] is not None) else None,
        dependencies=['area','c'],
        target='h_c',
        description="Height h_c"
    ))
    # --- end triangle extras ---

    # area flexible: heron or 0.5 ab sinC
    def area_flex(netw, known, unknown):
        if 'area' not in unknown:
            return None
        # heron
        if netw.vars['a'].is_known() and netw.vars['b'].is_known() and netw.vars['c'].is_known():
            a,b,c = netw.vars['a'].value, netw.vars['b'].value, netw.vars['c'].value
            s = (a+b+c)/2
            heron_expr = s*(s-a)*(s-b)*(s-c)
            if heron_expr < 0:
                return None  # Invalid: cannot take sqrt of negative
            her = safe_sqrt(heron_expr)
            if her is not None:
                return {'area': her}
        # sin formula
        if netw.vars['a'].is_known() and netw.vars['b'].is_known() and netw.vars['C'].is_known():
            return {'area': 0.5 * netw.vars['a'].value * netw.vars['b'].value * math.sin(math.radians(netw.vars['C'].value))}
        return None

    net.add_constraint(Constraint(
        name="area_flex",
        nodes=['a','b','c','A','B','C','area'],
        flex_func=area_flex,
        description="area flexible"
    ))
    
    # Reverse area: if area and 2 sides with included angle, compute third side (complex, skip for now)
    # Or if area and height known, compute base
    def area_reverse_triangle(netw, known, unknown):
        res = {}
        if 'area' in known and 'area' not in unknown:
            area_val = netw.vars['area'].value
            if area_val is not None and area_val > 0:
                # If area and height known, compute base: area = 0.5 * base * height
                if 'h_a' in known and 'a' in unknown:
                    h = netw.vars['h_a'].value
                    if h is not None and h > 0:
                        res['a'] = 2 * area_val / h
                if 'h_b' in known and 'b' in unknown:
                    h = netw.vars['h_b'].value
                    if h is not None and h > 0:
                        res['b'] = 2 * area_val / h
                if 'h_c' in known and 'c' in unknown:
                    h = netw.vars['h_c'].value
                    if h is not None and h > 0:
                        res['c'] = 2 * area_val / h
        return res or None
    
    net.add_constraint(Constraint(
        name="area_reverse_triangle",
        nodes=['a','b','c','area','h_a','h_b','h_c'],
        flex_func=area_reverse_triangle,
        description="Reverse area: compute side from area and height"
    ))

    # --- ADD: nếu tam giác đã biết 3 góc = 60° (tam giác đều) và perimeter thì suy ra 3 cạnh và diện tích
    def equilateral_from_perimeter(netw, known, unknown):
        # cần perimeter và Cả 3 góc đã biết và đều ~60°
        if 'perimeter' in known and all(netw.vars.get(ang) and netw.vars[ang].is_known() for ang in ('A','B','C')):
            A = netw.vars['A'].value; B = netw.vars['B'].value; C = netw.vars['C'].value
            if abs(A-60.0) < 1e-6 and abs(B-60.0) < 1e-6 and abs(C-60.0) < 1e-6:
                p = netw.vars['perimeter'].value
                if p is None:
                    return None
                a = p / 3.0
                area = (math.sqrt(3.0)/4.0) * a * a
                res = {}
                # chỉ ghi khi chưa biết
                for s in ('a','b','c'):
                    if not netw.vars[s].is_known():
                        res[s] = a
                if not netw.vars['area'].is_known():
                    res['area'] = area
                return res or None
        return None
    net.add_constraint(Constraint(
        name="equilateral_from_perimeter",
        nodes=['perimeter','A','B','C','a','b','c','area'],
        flex_func=equilateral_from_perimeter,
        description="If A=B=C=60 and perimeter known -> a=b=c=p/3 and area."
    ))

    # [NEW] Reverse height: compute area from height and base
    def triangle_area_from_height_base(netw, known, unknown):
        res = {}
        if 'area' in unknown:
            # area = 0.5 * base * height
            for base, height in [('a', 'h_a'), ('b', 'h_b'), ('c', 'h_c')]:
                if base in known and height in known:
                    res['area'] = 0.5 * netw.vars[base].value * netw.vars[height].value
                    break
        return res or None
    
    net.add_constraint(Constraint(
        name="triangle_area_from_height_base",
        nodes=['a','b','c','area','h_a','h_b','h_c'],
        flex_func=triangle_area_from_height_base,
        description="Area from base and height"
    ))

    # [NEW] Reverse height: compute base from area and height
    def triangle_base_from_area_height(netw, known, unknown):
        res = {}
        if 'area' in known:
            area_val = netw.vars['area'].value
            if area_val > 0:
                for base, height in [('a', 'h_a'), ('b', 'h_b'), ('c', 'h_c')]:
                    if base in unknown and height in known:
                        h = netw.vars[height].value
                        if h > 0:
                            res[base] = 2 * area_val / h
        return res or None
    
    net.add_constraint(Constraint(
        name="triangle_base_from_area_height",
        nodes=['a','b','c','area','h_a','h_b','h_c'],
        flex_func=triangle_base_from_area_height,
        description="Compute base from area and height"
    ))

    return net

# --- CÁC HÀM BỔ TRỢ ---
def get_rad(deg):
    return math.radians(deg) if deg is not None else None

def get_deg(rad):
    return math.degrees(rad) if rad is not None else None

# --- 1. BASE: TỨ GIÁC THƯỜNG ---
def create_quadrilateral_network() -> ConstraintNetwork:
    net = ConstraintNetwork()
    # Biến cơ bản
    for v in ['a', 'b', 'c', 'd', 'perimeter', 'area']:
        net.add_variable(v)
    for ang in ['A', 'B', 'C', 'D']:
        net.add_variable(ang, f"Góc {ang} (độ)")
    net.add_variable('d1', "Đường chéo AC (nối góc A-C)")
    net.add_variable('d2', "Đường chéo BD (nối góc B-D)")
    net.add_variable('s', "Nửa chu vi")
    net.add_variable('h', "Chiều cao (nếu có)")

    # Chu vi & Nửa chu vi
    net.add_constraint(Constraint(
        name="quad_perimeter",
        nodes=['a', 'b', 'c', 'd', 'perimeter'],
        forward_func=lambda v: v['a'] + v['b'] + v['c'] + v['d'],
        dependencies=['a', 'b', 'c', 'd'],
        target='perimeter',
        description="Chu vi = a + b + c + d"
    ))
    
    # Reverse chu vi: tính cạnh từ chu vi và 3 cạnh khác
    def quad_perimeter_reverse(netw, known, unknown):
        res = {}
        if 'perimeter' in known and 'perimeter' not in unknown:
            p = netw.vars['perimeter'].value
            if p is not None and p > 0:
                sides = ['a', 'b', 'c', 'd']
                known_sides = [s for s in sides if netw.vars[s].is_known()]
                unknown_sides = [s for s in sides if not netw.vars[s].is_known()]
                if len(known_sides) == 3 and len(unknown_sides) == 1:
                    known_sum = sum(netw.vars[s].value for s in known_sides)
                    computed_side = p - known_sum
                    if computed_side > 0:
                        res[unknown_sides[0]] = computed_side
        return res or None
    
    net.add_constraint(Constraint(
        name="quad_perimeter_reverse",
        nodes=['a', 'b', 'c', 'd', 'perimeter'],
        flex_func=quad_perimeter_reverse,
        description="Reverse chu vi: tính cạnh từ chu vi và 3 cạnh khác"
    ))
    
    # Nửa chu vi từ chu vi
    net.add_constraint(Constraint(
        name="quad_semi_perimeter_from_perimeter",
        nodes=['perimeter', 's'],
        forward_func=lambda v: v['perimeter'] / 2.0,
        dependencies=['perimeter'],
        target='s',
        description="s = perimeter / 2"
    ))
    
    # Nửa chu vi từ 4 cạnh
    net.add_constraint(Constraint(
        name="quad_semi_perimeter_from_sides",
        nodes=['a', 'b', 'c', 'd', 's'],
        forward_func=lambda v: (v['a'] + v['b'] + v['c'] + v['d']) / 2.0,
        dependencies=['a', 'b', 'c', 'd'],
        target='s',
        description="s = (a + b + c + d) / 2"
    ))

    # Tổng 4 góc = 360
    def sum_angles_quad(netw, known, unknown):
        angles = ['A', 'B', 'C', 'D']
        vals = [netw.vars[x].value for x in angles]
        if sum(1 for x in vals if x is not None) == 3:
            res = 360.0 - sum(x for x in vals if x is not None)
            for i, name in enumerate(angles):
                if vals[i] is None:
                    return {name: res}
        return None
    net.add_constraint(Constraint(
        name="quad_angle_sum",
        nodes=['A', 'B', 'C', 'D'],
        flex_func=sum_angles_quad
    ))

    # Đường chéo d1 (AC)
    def diagonal_AC_calc(netw, known, unknown):
        res = {}
        # Tam giác ABC: d1^2 = a^2 + b^2 - 2ab*cos(B)
        if 'a' in known and 'b' in known and 'B' in known:
            val = netw.vars['a'].value**2 + netw.vars['b'].value**2 - \
                  2*netw.vars['a'].value*netw.vars['b'].value*math.cos(get_rad(netw.vars['B'].value))
            res['d1'] = safe_sqrt(val)
        # Tam giác CDA: d1^2 = c^2 + d^2 - 2cd*cos(D)
        elif 'c' in known and 'd' in known and 'D' in known:
            val = netw.vars['c'].value**2 + netw.vars['d'].value**2 - \
                  2*netw.vars['c'].value*netw.vars['d'].value*math.cos(get_rad(netw.vars['D'].value))
            res['d1'] = safe_sqrt(val)
        return res
    net.add_constraint(Constraint(
        name="calc_diagonal_AC",
        nodes=['a', 'b', 'c', 'd', 'B', 'D', 'd1'],
        flex_func=diagonal_AC_calc
    ))

    # Đường chéo d2 (BD)
    def diagonal_BD_calc(netw, known, unknown):
        res = {}
        # Tam giác BAD: d2^2 = a^2 + d^2 - 2ad*cos(A)
        if 'a' in known and 'd' in known and 'A' in known:
            val = netw.vars['a'].value**2 + netw.vars['d'].value**2 - \
                  2*netw.vars['a'].value*netw.vars['d'].value*math.cos(get_rad(netw.vars['A'].value))
            res['d2'] = safe_sqrt(val)
        # Tam giác BCD: d2^2 = b^2 + c^2 - 2bc*cos(C)
        elif 'b' in known and 'c' in known and 'C' in known:
            val = netw.vars['b'].value**2 + netw.vars['c'].value**2 - \
                  2*netw.vars['b'].value*netw.vars['c'].value*math.cos(get_rad(netw.vars['C'].value))
            res['d2'] = safe_sqrt(val)
        return res
    net.add_constraint(Constraint(
        name="calc_diagonal_BD",
        nodes=['a', 'b', 'c', 'd', 'A', 'C', 'd2'],
        flex_func=diagonal_BD_calc
    ))

    # Diện tích Bretschneider (tứ giác tổng quát)
    def bretschneider_area(netw, known, unknown):
        if 'area' in unknown and all(netw.vars[k].is_known() for k in ['a','b','c','d','A','C']):
            a, b = netw.vars['a'].value, netw.vars['b'].value
            c, d = netw.vars['c'].value, netw.vars['d'].value
            s = (a + b + c + d) / 2.0
            A, C = netw.vars['A'].value, netw.vars['C'].value
            term1 = (s-a)*(s-b)*(s-c)*(s-d)
            term2 = a*b*c*d * (math.cos(get_rad((A+C)/2)))**2
            if term1 - term2 >= 0:
                return {'area': safe_sqrt(term1 - term2)}
        return None
    net.add_constraint(Constraint(
        name="bretschneider_area",
        nodes=['a','b','c','d','A','C','area'],
        flex_func=bretschneider_area
    ))

    # Diện tích tứ giác khi biết 2 đường chéo và góc giữa chúng (tùy chọn, nâng cao)
    # S = 0.5 * d1 * d2 * sin(theta), theta là góc giữa 2 đường chéo (chưa thêm biến này)

    # Diện tích tứ giác lồi khi biết chiều cao (h) và 2 đáy (a,c): S = (a+c)/2 * h
    def quad_area_height(netw, known, unknown):
        if 'area' in unknown and 'a' in known and 'c' in known and 'h' in known:
            a_val = netw.vars['a'].value
            c_val = netw.vars['c'].value
            h_val = netw.vars['h'].value
            return {'area': 0.5 * (a_val + c_val) * h_val}
        return None
    net.add_constraint(Constraint(
        name="quad_area_height",
        nodes=['a','c','h','area'],
        flex_func=quad_area_height
    ))

    # Suy ra chiều cao từ diện tích và 2 đáy
    def quad_height_from_area(netw, known, unknown):
        if 'h' in unknown and 'area' in known and 'a' in known and 'c' in known:
            area_val = netw.vars['area'].value
            a_val = netw.vars['a'].value
            c_val = netw.vars['c'].value
            if (a_val + c_val) != 0:
                return {'h': 2.0 * area_val / (a_val + c_val)}
        return None
    net.add_constraint(Constraint(
        name="quad_height_from_area",
        nodes=['a','c','h','area'],
        flex_func=quad_height_from_area
    ))

    # [NEW] Diagonal computation from sides using Bretschneider
    def quad_diagonal_from_sides(netw, known, unknown):
        res = {}
        # d1^2 = a^2 + b^2 - 2ab*cos(B)
        if 'd1' in unknown and all(k in known for k in ['a', 'b', 'B']):
            a, b = netw.vars['a'].value, netw.vars['b'].value
            B = netw.vars['B'].value
            val = a**2 + b**2 - 2*a*b*math.cos(math.radians(B))
            if val >= 0:
                res['d1'] = safe_sqrt(val)
        
        # d2^2 = a^2 + d^2 - 2ad*cos(A)
        if 'd2' in unknown and all(k in known for k in ['a', 'd', 'A']):
            a, d = netw.vars['a'].value, netw.vars['d'].value
            A = netw.vars['A'].value
            val = a**2 + d**2 - 2*a*d*math.cos(math.radians(A))
            if val >= 0:
                res['d2'] = safe_sqrt(val)
        
        return res or None
    
    net.add_constraint(Constraint(
        name="quad_diagonal_from_sides",
        nodes=['a','b','c','d','A','B','C','D','d1','d2'],
        flex_func=quad_diagonal_from_sides,
        description="Compute diagonals from sides and angles"
    ))

    return net

# --- 2. HÌNH THANG ---
def create_trapezoid_network() -> ConstraintNetwork:
    net = create_quadrilateral_network()
    net.add_variable('h', "Chiều cao")
    # Góc kề bù: A+D=180, B+C=180
    def trapezoid_angles(netw, known, unknown):
        res = {}
        if 'A' in known and 'D' not in known: res['D'] = 180.0 - netw.vars['A'].value
        elif 'D' in known and 'A' not in known: res['A'] = 180.0 - netw.vars['D'].value
        if 'B' in known and 'C' not in known: res['C'] = 180.0 - netw.vars['B'].value
        elif 'C' in known and 'B' not in known: res['B'] = 180.0 - netw.vars['C'].value
        return res
    net.add_constraint(Constraint(
        name="trap_parallel_angles",
        nodes=['A', 'B', 'C', 'D'],
        flex_func=trapezoid_angles
    ))
    # Diện tích hình thang: S = (a + c)/2 * h
    def trap_area_height(netw, known, unknown):
        res = {}
        if 'area' in unknown and 'a' in known and 'c' in known and 'h' in known:
            res['area'] = (netw.vars['a'].value + netw.vars['c'].value) / 2.0 * netw.vars['h'].value
        elif 'h' in unknown and 'area' in known and 'a' in known and 'c' in known:
            sum_bases = netw.vars['a'].value + netw.vars['c'].value
            if sum_bases > 0:
                res['h'] = 2.0 * netw.vars['area'].value / sum_bases
        return res if res else None
    net.add_constraint(Constraint(
        name="trap_area_formula",
        nodes=['area', 'a', 'c', 'h'],
        flex_func=trap_area_height
    ))

    # 2. Chiều cao từ cạnh bên và góc: h = b * sin(B), h = d * sin(D)
    def trap_height_from_sides_angles(netw, known, unknown):
        res = {}
        if 'h' in unknown and 'b' in known and 'B' in known:
            res['h'] = netw.vars['b'].value * math.sin(math.radians(netw.vars['B'].value))
        if 'h' in unknown and 'd' in known and 'D' in known:
            res['h'] = netw.vars['d'].value * math.sin(math.radians(netw.vars['D'].value))
        return res if res else None
    net.add_constraint(Constraint(
        name="trap_height_from_sides_angles",
        nodes=['h', 'b', 'd', 'B', 'D'],
        flex_func=trap_height_from_sides_angles
    ))

    # 3. Độ dài cạnh bên khi biết chiều cao và góc: b = h / sin(B), d = h / sin(D)
    def trap_side_from_height_angle(netw, known, unknown):
        res = {}
        if 'b' in unknown and 'h' in known and 'B' in known and abs(math.sin(math.radians(netw.vars['B'].value))) > 1e-8:
            res['b'] = netw.vars['h'].value / math.sin(math.radians(netw.vars['B'].value))
        if 'd' in unknown and 'h' in known and 'D' in known and abs(math.sin(math.radians(netw.vars['D'].value))) > 1e-8:
            res['d'] = netw.vars['h'].value / math.sin(math.radians(netw.vars['D'].value))
        return res if res else None
    net.add_constraint(Constraint(
        name="trap_side_from_height_angle",
        nodes=['h', 'b', 'd', 'B', 'D'],
        flex_func=trap_side_from_height_angle
    ))

    # 4. Đường chéo: d1 = sqrt(a^2 + b^2 - 2ab*cos(B)), d2 = sqrt(c^2 + d^2 - 2cd*cos(D))
    def trap_diagonals(netw, known, unknown):
        res = {}
        if 'd1' in unknown and 'a' in known and 'b' in known and 'B' in known:
            val = netw.vars['a'].value**2 + netw.vars['b'].value**2 - \
                  2*netw.vars['a'].value*netw.vars['b'].value*math.cos(math.radians(netw.vars['B'].value))
            res['d1'] = safe_sqrt(val)
        if 'd2' in unknown and 'c' in known and 'd' in known and 'D' in known:
            val = netw.vars['c'].value**2 + netw.vars['d'].value**2 - \
                  2*netw.vars['c'].value*netw.vars['d'].value*math.cos(math.radians(netw.vars['D'].value))
            res['d2'] = safe_sqrt(val)
        return res if res else None
    net.add_constraint(Constraint(
        name="trap_diagonals_formula",
        nodes=['a', 'b', 'c', 'd', 'B', 'D', 'd1', 'd2'],
        flex_func=trap_diagonals
    ))

    # 5. Công thức chiều cao hình thang thường từ 4 cạnh:
    # h = sqrt(b^2 - (( (c-a) + (a^2 - d^2)/(c-a) )/2 )^2 ) (chỉ khi a != c)
    def trap_height_from_sides(netw, known, unknown):
        if 'h' in unknown and all(k in known for k in ['a','b','c','d']):
            a, b, c, d = netw.vars['a'].value, netw.vars['b'].value, netw.vars['c'].value, netw.vars['d'].value
            if abs(c-a) > 1e-8:
                try:
                    expr = ((c-a) + (a**2 - d**2)/(c-a)) / 2.0
                    val = b**2 - expr**2
                    if val > 0:
                        return {'h': math.sqrt(val)}
                except ZeroDivisionError:
                    pass
        return None
    net.add_constraint(Constraint(
        name="trap_height_from_sides",
        nodes=['a','b','c','d','h'],
        flex_func=trap_height_from_sides
    ))

    return net

# --- 3. HÌNH BÌNH HÀNH ---
def create_parallelogram_network() -> ConstraintNetwork:
    net = create_quadrilateral_network()
    
    # 1. Cạnh đối, Góc đối
    def para_props(netw, known, unknown):
        res = {}
        # Đồng bộ cạnh
        if 'a' in known and 'c' not in known: res['c'] = netw.vars['a'].value
        if 'c' in known and 'a' not in known: res['a'] = netw.vars['c'].value
        if 'b' in known and 'd' not in known: res['d'] = netw.vars['b'].value
        if 'd' in known and 'b' not in known: res['b'] = netw.vars['d'].value
        # Đồng bộ góc
        if 'A' in known and 'C' not in known: res['C'] = netw.vars['A'].value
        if 'B' in known and 'D' not in known: res['D'] = netw.vars['B'].value
        # Góc kề bù
        if 'A' in known and 'B' not in known: res['B'] = 180 - netw.vars['A'].value
        if 'B' in known and 'A' not in known: res['A'] = 180 - netw.vars['B'].value
        return res
    net.add_constraint(Constraint(name="para_props", nodes=['a','b','c','d','A','B','C','D'], flex_func=para_props))

    # 2. Diện tích S = a*h (và ngược lại)
    def para_area_h_flex(netw, known, unknown):
        if 'area' in known:
            s = netw.vars['area'].value
            if 'a' in known and 'h' not in known: return {'h': s / netw.vars['a'].value}
            if 'h' in known and 'a' not in known: return {'a': s / netw.vars['h'].value}
        else:
            if 'a' in known and 'h' in known: return {'area': netw.vars['a'].value * netw.vars['h'].value}
        return None
    net.add_constraint(Constraint(name="para_area_h", nodes=['area','a','h'], flex_func=para_area_h_flex))

    # 3. Diện tích S = a*b*sinA
    net.add_constraint(Constraint(
        name="para_area_sine", nodes=['area', 'a', 'b', 'A'],
        forward_func=lambda v: v['a'] * v['b'] * math.sin(get_rad(v['A'])),
        dependencies=['a','b','A'], target='area'
    ))

    # 4. Tính cạnh từ CHU VI (P = 2(a+b))
    # Chỉ chạy khi biết P và 1 cạnh -> Ra cạnh kia. KHÔNG tự chia đôi P.
    def para_perimeter_flex(netw, known, unknown):
        res = {}
        if 'perimeter' in known:
            p = netw.vars['perimeter'].value
            # Biết a -> tính b
            if 'a' in known and 'b' not in known:
                b_val = p/2.0 - netw.vars['a'].value
                if b_val > 0: 
                    res['b'] = b_val; res['d'] = b_val
            # Biết b -> tính a
            elif 'b' in known and 'a' not in known:
                a_val = p/2.0 - netw.vars['b'].value
                if a_val > 0: 
                    res['a'] = a_val; res['c'] = a_val
        return res
    net.add_constraint(Constraint(name="para_perimeter_flex", nodes=['perimeter','a','b','c','d'], flex_func=para_perimeter_flex))

    # 5. Giải hệ: Biết P, Area, Góc A -> Tìm a, b
    def para_solve_system(netw, known, unknown):
        if {'perimeter','area','A'}.issubset(known) and not (netw.vars['a'].is_known() and netw.vars['b'].is_known()):
            p = netw.vars['perimeter'].value
            s = netw.vars['area'].value
            sinA = math.sin(get_rad(netw.vars['A'].value))
            if sinA > 1e-9:
                prod = s / sinA # a*b
                sum_val = p / 2.0 # a+b
                delta = sum_val**2 - 4*prod
                if delta >= 0:
                    a = (sum_val + math.sqrt(delta))/2
                    b = (sum_val - math.sqrt(delta))/2
                    return {'a':a, 'b':b, 'c':a, 'd':b}
        return None
    net.add_constraint(Constraint(name="para_solve_system", nodes=['perimeter','area','A','a','b'], flex_func=para_solve_system))

    return net

# =============================================================================
# 5. HÌNH CHỮ NHẬT (RECTANGLE) - ĐÃ SỬA LỖI & BỔ SUNG
# =============================================================================
def create_rectangle_network() -> ConstraintNetwork:
    net = create_parallelogram_network()

    # 1. Góc vuông 90 độ (Cố định)
    def rect_90(netw, known, unknown):
        return {k: 90.0 for k in ['A','B','C','D'] if k not in known}
    net.add_constraint(Constraint(name="rect_90", nodes=['A','B','C','D'], flex_func=rect_90))

    # 2. [QUAN TRỌNG] Liên kết Chiều cao h với Cạnh b
    # Trong HCN, chiều cao ứng với đáy a chính là cạnh b.
    # Điều này giúp các công thức diện tích cũ (S = a*h) tự động hiểu là S = a*b.
    def rect_h_is_b(netw, known, unknown):
        res = {}
        if 'b' in known and 'h' not in known: res['h'] = netw.vars['b'].value
        if 'h' in known and 'b' not in known: res['b'] = netw.vars['h'].value
        return res
    net.add_constraint(Constraint(name="rect_h_equals_b", nodes=['h', 'b'], flex_func=rect_h_is_b))

    # 3. Đường chéo bằng nhau & Pytago (2 chiều)
    def rect_pytago_flex(netw, known, unknown):
        res = {}
        # Xuôi: a,b -> d1
        if 'a' in known and 'b' in known and 'd1' not in known:
            res['d1'] = safe_sqrt(netw.vars['a'].value**2 + netw.vars['b'].value**2)
        # Ngược: d1, a -> b
        elif 'd1' in known and 'a' in known and 'b' not in known:
            val = netw.vars['d1'].value**2 - netw.vars['a'].value**2
            if val > 0: res['b'] = math.sqrt(val)
        # Ngược: d1, b -> a
        elif 'd1' in known and 'b' in known and 'a' not in known:
            val = netw.vars['d1'].value**2 - netw.vars['b'].value**2
            if val > 0: res['a'] = math.sqrt(val)
        return res
    net.add_constraint(Constraint(name="rect_pytago_flex", nodes=['a','b','d1'], flex_func=rect_pytago_flex))
    
    # Đồng bộ d1 = d2
    net.add_constraint(Constraint(
        name="rect_diag_equal", nodes=['d1','d2'],
        flex_func=lambda n,k,u: {'d2': n.vars['d1'].value} if 'd1' in k else ({'d1': n.vars['d2'].value} if 'd2' in k else None)))

    # 4. [FIXED] Ràng buộc Diện tích Đa năng (Unified Area Constraint)
    # Gom cả tính xuôi (S=ab) và tính ngược (a=S/b, b=S/a) vào một chỗ để đảm bảo luôn chạy.
    def rect_area_unified(netw, known, unknown):
        res = {}
        # Forward: a, b -> area
        if 'a' in known and 'b' in known and 'area' not in known:
            res['area'] = netw.vars['a'].value * netw.vars['b'].value
        
        # Reverse: area -> side
        elif 'area' in known:
            s = netw.vars['area'].value
            if s is not None and s > 0:
                if 'a' in known and 'b' not in known:
                    a_val = netw.vars['a'].value
                    if a_val > 1e-9: 
                        res['b'] = s / a_val
                        res['d'] = s / a_val  # b = d in rectangle
                elif 'b' in known and 'a' not in known:
                    b_val = netw.vars['b'].value
                    if b_val > 1e-9: 
                        res['a'] = s / b_val
                        res['c'] = s / b_val  # a = c in rectangle
        return res or None
    
    net.add_constraint(Constraint(
        name="rect_area_unified", 
        nodes=['area', 'a', 'b', 'c', 'd'], 
        flex_func=rect_area_unified,
        description="Bidirectional area = a * b"
    ))

    # 5. [MỚI] Giải hệ phương trình: Biết Chu vi (P) và Diện tích (S) -> Tìm a, b
    # Hệ: 2(a+b) = P  và  a*b = S
    # -> a, b là nghiệm của phương trình: X^2 - (P/2)X + S = 0
    def rect_solve_P_S(netw, known, unknown):
        # Chỉ chạy khi biết P và S, nhưng chưa biết a và b
        if 'perimeter' in known and 'area' in known and not (netw.vars['a'].is_known() or netw.vars['b'].is_known()):
            p = netw.vars['perimeter'].value
            s = netw.vars['area'].value
            
            if p is not None and s is not None:
                half_p = p / 2.0 # Tổng hai cạnh (a+b)
                delta = half_p**2 - 4*s # Delta = (a+b)^2 - 4ab = (a-b)^2
                
                if delta >= -1e-9: # Delta không âm
                    delta = max(0.0, delta)
                    sqrt_delta = math.sqrt(delta)
                    
                    # Hai nghiệm
                    x1 = (half_p + sqrt_delta) / 2.0
                    x2 = (half_p - sqrt_delta) / 2.0
                    
                    if x1 > 0 and x2 > 0:
                        # Gán a là cạnh dài, b là cạnh ngắn (hoặc ngược lại, không quan trọng)
                        return {'a': x1, 'b': x2, 'c': x1, 'd': x2}
        return None

    net.add_constraint(Constraint(
        name="rect_solve_P_S",
        nodes=['perimeter', 'area', 'a', 'b', 'c', 'd'],
        flex_func=rect_solve_P_S,
        description="Giải hệ P và S để tìm cạnh"
    ))

    return net
# =============================================================================
# 6. HÌNH VUÔNG (SQUARE) - ĐÃ CẬP NHẬT ĐẦY ĐỦ
# =============================================================================
def create_square_network() -> ConstraintNetwork:
    net = create_rectangle_network()

    # 1. Cạnh bằng nhau
    def sq_sides(netw, known, unknown):
        val = None
        for k in ['a','b','c','d']:
            if k in known: val = netw.vars[k].value; break
        if val: return {k: val for k in ['a','b','c','d'] if k not in known}
        return None
    net.add_constraint(Constraint(name="sq_sides", nodes=['a','b','c','d'], flex_func=sq_sides))

    # 2. [RIÊNG HÌNH VUÔNG] Tính cạnh từ CHU VI: a = P/4
    net.add_constraint(Constraint(
        name="sq_side_from_P", nodes=['perimeter','a'],
        forward_func=lambda v: v['perimeter']/4.0 if v.get('perimeter') else None,
        dependencies=['perimeter'], target='a', description="a = P/4"))

    # 3. [RIÊNG HÌNH VUÔNG] Tính cạnh từ DIỆN TÍCH: a = sqrt(S)
    net.add_constraint(Constraint(
        name="sq_side_from_S", nodes=['area','a'],
        forward_func=lambda v: safe_sqrt(v['area']) if v.get('area') is not None else None,
        dependencies=['area'], target='a', description="a = sqrt(S)"))

    # 4. Chéo a -> d
    net.add_constraint(Constraint(
        name="sq_diag", nodes=['a','d1'],
        forward_func=lambda v: v['a']*math.sqrt(2) if v.get('a') else None,
        dependencies=['a'], target='d1'))

    return net
def create_equilateral_triangle_network() -> ConstraintNetwork:
    """
    Equilateral triangle network:
    - built on triangle network
    - enforce a=b=c (flex)
    - set angles A=B=C=60 (for unknown angles)
    - area = sqrt(3)/4 * a^2
    - perimeter = 3 * a
    """
    net = create_triangle_network()

    # Flex: copy any known side to all others
    def eq_sides(netw, known, unknown):
        val = None
        for k in ('a','b','c'):
            if k in known:
                val = netw.vars[k].value
                break
        if val is None:
            return None
        res = {}
        for k in ('a','b','c'):
            if k not in known:
                res[k] = val
        return res or None
    net.add_constraint(Constraint(
        name="equilateral_sides_equal",
        nodes=['a','b','c'],
        flex_func=eq_sides,
        description="Enforce a=b=c for equilateral triangle"
    ))

    # Flex: set unknown angles to 60° (do not override known angles)
    def eq_angles(netw, known, unknown):
        res = {}
        for ang in ('A','B','C'):
            if ang not in known:
                res[ang] = 60.0
        return res or None
    net.add_constraint(Constraint(
        name="equilateral_angles_60",
        nodes=['A','B','C'],
        flex_func=eq_angles,
        description="Set angles A=B=C=60 for equilateral triangle"
    ))

    # area = sqrt(3)/4 * a^2
    net.add_constraint(Constraint(
        name="equilateral_area",
        nodes=['a','area'],
        forward_func=lambda v: (math.sqrt(3.0)/4.0) * v['a']**2 if (v.get('a') is not None) else None,
        dependencies=['a'],
        target='area',
        description="Area for equilateral triangle"
    ))

    # perimeter = 3 * a
    net.add_constraint(Constraint(
        name="equilateral_perimeter",
        nodes=['a','perimeter'],
        forward_func=lambda v: (3.0 * v['a']) if (v.get('a') is not None) else None,
        dependencies=['a'],
        target='perimeter',
        description="Perimeter for equilateral triangle"
    ))

    # --- [MỚI] Tính cạnh từ CHU VI: a = P / 3 ---
    net.add_constraint(Constraint(
        name="eq_side_from_perimeter",
        nodes=['perimeter','a'],
        forward_func=lambda v: (v['perimeter'] / 3.0) if (v.get('perimeter') is not None) else None,
        dependencies=['perimeter'],
        target='a',
        description="a = P/3 for equilateral"
    ))

    # --- [MỚI] Tính cạnh từ DIỆN TÍCH: a = sqrt(4S / sqrt(3)) ---
    net.add_constraint(Constraint(
        name="eq_side_from_area",
        nodes=['area','a'],
        forward_func=lambda v: safe_sqrt(v['area'] * 4.0 / math.sqrt(3)) if (v.get('area') is not None) else None,
        dependencies=['area'],
        target='a',
        description="a = sqrt(4S/sqrt(3)) for equilateral"
    ))

    return net
def create_rhombus_network() -> ConstraintNetwork:
    """
    Rhombus network (đảm bảo hàm tồn tại để GUI gọi):
    - kế thừa từ parallelogram
    - tất cả các cạnh bằng nhau (flex)
    - diện tích có thể từ d1,d2: area = 0.5 * d1 * d2
    - quan hệ cạnh-đường chéo: (d1/2)^2 + (d2/2)^2 = a^2
    - perimeter -> a (a = perimeter/4)
    """
    net = create_parallelogram_network()

    # 1) Tất cả cạnh bằng nhau (flex)
    def rhombus_sides(netw, known, unknown):
        res = {}
        val = None
        for k in ('a','b','c','d'):
            if k in known:
                val = netw.vars[k].value
                break
        if val is not None:
            for k in ('a','b','c','d'):
                if k not in known:
                    res[k] = val
        return res or None
    net.add_constraint(Constraint(name="rhombus_equal_sides", nodes=['a','b','c','d'], flex_func=rhombus_sides,
                                  description="All sides equal for rhombus"))

    # 2) Area from diagonals
    net.add_constraint(Constraint(
        name="rhombus_area_diags",
        nodes=['area','d1','d2'],
        forward_func=lambda v: 0.5 * v['d1'] * v['d2'] if (v.get('d1') is not None and v.get('d2') is not None) else None,
        dependencies=['d1','d2'],
        target='area',
        description="Area = 0.5 * d1 * d2"
    ))

    # 3) Relationship between sides and diagonals: (d1/2)^2 + (d2/2)^2 = a^2
    def rhombus_side_from_diags(netw, known, unknown):
        # if both diagonals known, compute side
        if 'd1' in known and 'd2' in known:
            d1 = netw.vars['d1'].value
            d2 = netw.vars['d2'].value
            val = safe_sqrt((d1/2.0)**2 + (d2/2.0)**2)
            if val is None:
                return None
            res = {}
            for k in ('a','b','c','d'):
                if k not in known:
                    res[k] = val
            return res or None
        return None
    net.add_constraint(Constraint(name="rhombus_side_from_diags", nodes=['a','b','c','d','d1','d2'], flex_func=rhombus_side_from_diags,
                                  description="Compute side from diagonals for rhombus"))

    # 4) Perimeter -> side (forward)
    net.add_constraint(Constraint(
        name="rhombus_perimeter_to_side",
        nodes=['perimeter','a','b','c','d'],
        forward_func=lambda v: (v['perimeter'] / 4.0) if (v.get('perimeter') is not None) else None,
        dependencies=['perimeter'],
        target='a',
        description="a = perimeter / 4 for rhombus"
    ))

    return net
