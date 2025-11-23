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

    # 6. Góc kề bù: A+D=180, B+C=180
    def trapezoid_angles(netw, known, unknown):
        res = {}
        if 'A' in known and 'D' not in known: res['D'] = 180.0 - netw.vars['A'].value
        elif 'D' in known and 'A' not in known: res['A'] = 180.0 - netw.vars['D'].value
        if 'B' in known and 'C' not in known: res['C'] = 180.0 - netw.vars['B'].value
        elif 'C' in known and 'B' not in known: res['B'] = 180.0 - netw.vars['C'].value
        return res if res else None
    net.add_constraint(Constraint(
        name="trap_parallel_angles",
        nodes=['A', 'B', 'C', 'D'],
        flex_func=trapezoid_angles
    ))

    return net

# --- 3. HÌNH BÌNH HÀNH ---
def create_parallelogram_network() -> ConstraintNetwork:
    net = create_quadrilateral_network()
    # Cạnh đối bằng nhau (a=c, b=d)
    def para_sides(netw, known, unknown):
        res = {}
        if 'a' in known and 'c' not in known: res['c'] = netw.vars['a'].value
        if 'c' in known and 'a' not in known: res['a'] = netw.vars['c'].value
        if 'b' in known and 'd' not in known: res['d'] = netw.vars['b'].value
        if 'd' in known and 'b' not in known: res['b'] = netw.vars['d'].value
        return res
    net.add_constraint(Constraint(name="para_opp_sides", nodes=['a','b','c','d'], flex_func=para_sides))
    # Góc đối bằng nhau & Góc kề bù
    def para_angles(netw, known, unknown):
        res = {}
        if 'A' in known and 'C' not in known: res['C'] = netw.vars['A'].value
        if 'B' in known and 'D' not in known: res['D'] = netw.vars['B'].value
        if 'A' in known and 'B' not in known: res['B'] = 180 - netw.vars['A'].value
        if 'B' in known and 'A' not in known: res['A'] = 180 - netw.vars['B'].value
        return res
    net.add_constraint(Constraint(name="para_opp_angles", nodes=['A','B','C','D'], flex_func=para_angles))
    # Diện tích = a * h (hoặc a * b * sinA)
    net.add_constraint(Constraint(
        name="para_area_base_height",
        nodes=['area', 'a', 'h'],
        forward_func=lambda v: v['a'] * v['h'],
        target='area'
    ))
    net.add_constraint(Constraint(
        name="para_area_sine",
        nodes=['area', 'a', 'b', 'A'],
        forward_func=lambda v: v['a'] * v['b'] * math.sin(get_rad(v['A'])),
        target='area'
    ))
    # Định lý đường chéo HBH: d1^2 + d2^2 = 2(a^2 + b^2)
    def para_diagonals_law(netw, known, unknown):
        res = {}
        if 'a' in known and 'b' in known:
            a, b = netw.vars['a'].value, netw.vars['b'].value
            sum_sq = 2 * (a**2 + b**2)
            if 'd1' in known and 'd2' not in unknown:
                res['d2'] = safe_sqrt(sum_sq - netw.vars['d1'].value**2)
            elif 'd2' in known and 'd1' not in unknown:
                res['d1'] = safe_sqrt(sum_sq - netw.vars['d2'].value**2)
        return res
    net.add_constraint(Constraint(name="para_diag_law", nodes=['a','b','d1','d2'], flex_func=para_diagonals_law))
    # FLEX: từ perimeter tính cạnh còn lại cho parallelogram (p = 2*(a+b))
    def para_perimeter_flex(netw, known, unknown):
        res = {}
        if 'perimeter' not in known:
            return None
        p = netw.vars['perimeter'].value
        if p is None:
            return None
        # nếu biết c hoặc d, đồng bộ về a/b nếu cần (a=c, b=d)
        if netw.vars.get('c') and netw.vars['c'].is_known() and not netw.vars['a'].is_known():
            res['a'] = netw.vars['c'].value
        if netw.vars.get('d') and netw.vars['d'].is_known() and not netw.vars['b'].is_known():
            res['b'] = netw.vars['d'].value
        # nếu biết a, tính b = p/2 - a
        if netw.vars['a'].is_known() and not netw.vars['b'].is_known():
            b_val = p/2.0 - netw.vars['a'].value
            if b_val > 0:
                res['b'] = b_val
                if not netw.vars['d'].is_known(): res['d'] = b_val
                if not netw.vars['c'].is_known(): res['c'] = netw.vars['a'].value
        # nếu biết b, tính a = p/2 - b
        if netw.vars['b'].is_known() and not netw.vars['a'].is_known():
            a_val = p/2.0 - netw.vars['b'].value
            if a_val > 0:
                res['a'] = a_val
                if not netw.vars['c'].is_known(): res['c'] = a_val
                if not netw.vars['d'].is_known(): res['d'] = netw.vars['b'].value
        return res or None
    net.add_constraint(Constraint(
        name="para_perimeter_flex",
        nodes=['perimeter','a','b','c','d'],
        flex_func=para_perimeter_flex,
        description="Flex: compute a/b (and mirror c/d) from perimeter for parallelogram"
    ))
    return net

# --- 4. HÌNH THOI ---
def create_rhombus_network() -> ConstraintNetwork:
    net = create_parallelogram_network()
    # Tất cả cạnh bằng nhau (a=b=c=d)
    def rhombus_sides(netw, known, unknown):
        res = {}
        val = None
        for k in ['a','b','c','d']:
            if k in known:
                val = netw.vars[k].value
                break
        if val is not None:
            for k in ['a','b','c','d']:
                if k not in known:
                    res[k] = val
        return res
    net.add_constraint(Constraint(name="rhombus_equal_sides", nodes=['a','b','c','d'], flex_func=rhombus_sides))
    # Diện tích qua đường chéo: S = 0.5 * d1 * d2
    net.add_constraint(Constraint(
        name="rhombus_area_diags",
        nodes=['area', 'd1', 'd2'],
        forward_func=lambda v: 0.5 * v['d1'] * v['d2'],
        target='area'
    ))
    # Quan hệ cạnh và đường chéo: (d1/2)^2 + (d2/2)^2 = a^2
    def rhombus_side_diag(netw, known, unknown):
        res = {}
        if 'd1' in known and 'd2' in known:
            val = safe_sqrt((netw.vars['d1'].value/2)**2 + (netw.vars['d2'].value/2)**2)
            for k in ['a','b','c','d']:
                if k not in known:
                    res[k] = val
        return res
    net.add_constraint(Constraint(name="rhombus_pythagoras", nodes=['a','b','c','d','d1','d2'], flex_func=rhombus_side_diag))
    # Perimeter -> side for rhombus: a = p / 4
    net.add_constraint(Constraint(
        name="rhombus_perimeter_to_side",
        nodes=['perimeter', 'a', 'b', 'c', 'd'],
        forward_func=lambda v: (v['perimeter'] / 4.0) if (v.get('perimeter') is not None) else None,
        dependencies=['perimeter'],
        target='a',
        description="Compute side a = perimeter/4 for rhombus (then rhombus_equal_sides copies to others)"
    ))
    return net

# --- 5. HÌNH CHỮ NHẬT ---
def create_rectangle_network() -> ConstraintNetwork:
    net = create_parallelogram_network()
    # Góc vuông 90 độ (cố định)
    def rect_force_90(netw, known, unknown):
        res = {}
        for ang in ['A', 'B', 'C', 'D']:
            if ang not in known:
                res[ang] = 90.0
        return res
    net.add_constraint(Constraint(name="rect_angles_90", nodes=['A','B','C','D'], flex_func=rect_force_90))
    # Đường chéo bằng nhau: d1 = d2 = sqrt(a^2 + b^2)
    net.add_constraint(Constraint(
        name="rect_diag_equal",
        nodes=['d1', 'd2'],
        flex_func=lambda n, k, u: {'d2': n.vars['d1'].value} if 'd1' in k else ({'d1': n.vars['d2'].value} if 'd2' in k else None)
    ))
    net.add_constraint(Constraint(
        name="rect_pythagoras",
        nodes=['a', 'b', 'd1'],
        forward_func=lambda v: safe_sqrt(v['a']**2 + v['b']**2),
        target='d1'
    ))
    net.add_constraint(Constraint(
        name="rect_area_simple",
        nodes=['area', 'a', 'b'],
        forward_func=lambda v: v['a'] * v['b'],
        target='area'
    ))
    # Reverse area -> compute missing side: if area and a known -> b = area / a
    net.add_constraint(Constraint(
        name="rect_area_compute_b",
        nodes=['area', 'a', 'b'],
        forward_func=lambda v: (v['area'] / v['a']) if (v['a'] is not None and v['a'] != 0 and v['area'] is not None) else None,
        dependencies=['area', 'a'],
        target='b',
        description="Compute b from area and a"
    ))
    # Reverse area -> compute missing side: if area and b known -> a = area / b
    net.add_constraint(Constraint(
        name="rect_area_compute_a",
        nodes=['area', 'a', 'b'],
        forward_func=lambda v: (v['area'] / v['b']) if (v['b'] is not None and v['b'] != 0 and v['area'] is not None) else None,
        dependencies=['area', 'b'],
        target='a',
        description="Compute a from area and b"
    ))
    # FLEX: từ perimeter tính cạnh còn lại cho rectangle (perimeter = 2*(a + b))
    def rect_perimeter_flex(netw, known, unknown):
        res = {}
        if 'perimeter' not in known:
            return None
        p = netw.vars['perimeter'].value
        if p is None:
            return None
        # đồng bộ các cạnh đối nếu có
        if netw.vars.get('c') and netw.vars['c'].is_known() and not netw.vars['a'].is_known():
            res['a'] = netw.vars['c'].value
        if netw.vars.get('d') and netw.vars['d'].is_known() and not netw.vars['b'].is_known():
            res['b'] = netw.vars['d'].value
        # nếu biết a -> b = p/2 - a
        if netw.vars['a'].is_known() and not netw.vars['b'].is_known():
            b_val = p/2.0 - netw.vars['a'].value
            if b_val > 0:
                res['b'] = b_val
                if not netw.vars['c'].is_known(): res['c'] = netw.vars['a'].value
                if not netw.vars['d'].is_known(): res['d'] = b_val
        # nếu biết b -> a = p/2 - b
        if netw.vars['b'].is_known() and not netw.vars['a'].is_known():
            a_val = p/2.0 - netw.vars['b'].value
            if a_val > 0:
                res['a'] = a_val
                if not netw.vars['c'].is_known(): res['c'] = a_val
                if not netw.vars['d'].is_known(): res['d'] = netw.vars['b'].value
        return res or None
    net.add_constraint(Constraint(
        name="rect_perimeter_flex",
        nodes=['perimeter','a','b','c','d'],
        flex_func=rect_perimeter_flex,
        description="Flex: compute a/b and mirror c/d from perimeter for rectangle"
    ))
    return net

def create_square_network() -> ConstraintNetwork:
    """
    Square network built on rectangle network:
    - inherit rectangle constraints (right angles, diag, area)
    - enforce a = b = c = d (flex)
    - area = a^2 (forward)
    - diagonal = a * sqrt(2) (forward)
    """
    net = create_rectangle_network()

    # Flex constraint: copy any known side to all others
    def square_sides_equal(netw, known, unknown):
        res = {}
        val = None
        # find a known side value
        for k in ['a', 'b', 'c', 'd']:
            if k in known:
                val = netw.vars[k].value
                break
        if val is not None:
            for k in ['a', 'b', 'c', 'd']:
                if k not in known:
                    res[k] = val
        return res or None

    net.add_constraint(Constraint(
        name="square_sides_equal",
        nodes=['a', 'b', 'c', 'd'],
        flex_func=square_sides_equal,
        description="Enforce all sides equal for square"
    ))

    # area = a^2
    net.add_constraint(Constraint(
        name="square_area",
        nodes=['area', 'a'],
        forward_func=lambda v: (v['a']**2) if (v.get('a') is not None) else None,
        dependencies=['a'],
        target='area',
        description="Square area = a^2"
    ))

    # diagonal d1 = a * sqrt(2)
    net.add_constraint(Constraint(
        name="square_diag",
        nodes=['d1', 'a'],
        forward_func=lambda v: (v['a'] * math.sqrt(2.0)) if (v.get('a') is not None) else None,
        dependencies=['a'],
        target='d1',
        description="Square diagonal = a * sqrt(2)"
    ))

    return net
