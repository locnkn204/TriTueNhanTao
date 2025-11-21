import math
from engine import ConstraintNetwork, Constraint, safe_sqrt, clamp

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
    net.add_constraint(Constraint(
        name="sum_A",
        nodes=['A','B','C'],
        forward_func=lambda vals: 180.0 - vals['B'] - vals['C'],
        dependencies=['B','C'],
        target='A',
        description="A = 180 - B - C"
    ))
    net.add_constraint(Constraint(
        name="sum_B",
        nodes=['A','B','C'],
        forward_func=lambda vals: 180.0 - vals['A'] - vals['C'],
        dependencies=['A','C'],
        target='B',
        description="B = 180 - A - C"
    ))
    net.add_constraint(Constraint(
        name="sum_C",
        nodes=['A','B','C'],
        forward_func=lambda vals: 180.0 - vals['A'] - vals['B'],
        dependencies=['A','B'],
        target='C',
        description="C = 180 - A - B"
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
        for s, ang in pairs:
            # compute side if angle known
            if not netw.vars[s].is_known() and netw.vars[ang].is_known():
                res[s] = ratio * math.sin(math.radians(netw.vars[ang].value))
            # compute angle if side known
            if not netw.vars[ang].is_known() and netw.vars[s].is_known():
                sinv = netw.vars[s].value / ratio
                if -1.0 <= sinv <= 1.0:
                    res[ang] = math.degrees(math.asin(clamp(sinv, -1, 1)))
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
            if p is not None:
                # Compute missing side from perimeter
                sides = ['a', 'b', 'c']
                known_sides = [s for s in sides if netw.vars[s].is_known()]
                unknown_sides = [s for s in sides if not netw.vars[s].is_known()]
                if len(known_sides) == 2 and len(unknown_sides) == 1:
                    known_sum = sum(netw.vars[s].value for s in known_sides)
                    res[unknown_sides[0]] = p - known_sum
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
            her = safe_sqrt(s*(s-a)*(s-b)*(s-c))
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

def create_rectangle_network() -> ConstraintNetwork:
    net = ConstraintNetwork()
    # Sử dụng a,b,c,d và A,B,C,D để dễ mở rộng
    net.add_variable('a', "Cạnh a (đơn vị chiều dài) - cạnh cạnh 1")
    net.add_variable('b', "Cạnh b (đơn vị chiều dài) - cạnh cạnh 2 (kề a)")
    net.add_variable('c', "Cạnh c (đơn vị chiều dài) - đối diện a")
    net.add_variable('d', "Cạnh d (đơn vị chiều dài) - đối diện b")
    net.add_variable('A', "Góc A (°) tại đỉnh giữa a và b")
    net.add_variable('B', "Góc B (°) tại đỉnh giữa b và c")
    net.add_variable('C', "Góc C (°) tại đỉnh giữa c và d")
    net.add_variable('D', "Góc D (°) tại đỉnh giữa d và a")
    net.add_variable('area', "Diện tích tứ giác (nếu là hình chữ nhật, area = a*b)")
    net.add_variable('perimeter', "Chu vi = a + b + c + d")
    net.add_variable('diagonal', "Đường chéo (nếu là chữ nhật: sqrt(a^2 + b^2))")
    net.add_variable('h', "Chiều cao (dùng cho hình thang / hình bình hành)")


    # Area cho chữ nhật (adjacent a,b, yêu cầu góc vuông đã biết)
    net.add_constraint(Constraint(
        name="rect_area",
        nodes=['a','b','A','B','area'],
        forward_func=lambda vals: vals['a'] * vals['b'] if ((vals['A'] is not None and abs(vals['A']-90) < 0.1) or (vals['B'] is not None and abs(vals['B']-90) < 0.1)) else None,
        dependencies=['a','b','A','B'],
        target='area',
        description="Area = a * b (for rectangle)"
    ))
    # Perimeter
    net.add_constraint(Constraint(
        name="rect_perimeter",
        nodes=['a','b','c','d','perimeter'],
        forward_func=lambda vals: vals['a'] + vals['b'] + vals['c'] + vals['d'],
        dependencies=['a','b','c','d'],
        target='perimeter',
        description="Perimeter = a + b + c + d"
    ))
    
    # Reverse perimeter for quadrilateral
    def perimeter_reverse_quad(netw, known, unknown):
        res = {}
        if 'perimeter' in known and 'perimeter' not in unknown:
            p = netw.vars['perimeter'].value
            if p is not None:
                sides = ['a', 'b', 'c', 'd']
                known_sides = [s for s in sides if netw.vars[s].is_known()]
                unknown_sides = [s for s in sides if not netw.vars[s].is_known()]
                if len(known_sides) == 3 and len(unknown_sides) == 1:
                    known_sum = sum(netw.vars[s].value for s in known_sides)
                    res[unknown_sides[0]] = p - known_sum
        return res or None
    
    net.add_constraint(Constraint(
        name="perimeter_reverse_quad",
        nodes=['a','b','c','d','perimeter'],
        flex_func=perimeter_reverse_quad,
        description="Reverse perimeter: compute side from perimeter and 3 other sides"
    ))
    # Pythagoras for rectangle diagonal when a and b are adjacent
    net.add_constraint(Constraint(
        name="pythagoras",
        nodes=['a','b','diagonal'],
        forward_func=lambda vals: safe_sqrt(vals['a']**2 + vals['b']**2),
        dependencies=['a','b'],
        target='diagonal',
        description="Diagonal = sqrt(a^2 + b^2) (if rectangle)"
    ))

    # reverse diagonal -> sides (flex) (giữ nguyên)
    def diag_to_sides(netw, known, unknown):
        res = {}
        if 'a' in unknown and netw.vars['diagonal'].is_known() and netw.vars['b'].is_known():
            val = safe_sqrt(netw.vars['diagonal'].value**2 - netw.vars['b'].value**2)
            if val is not None:
                res['a'] = val
        if 'b' in unknown and netw.vars['diagonal'].is_known() and netw.vars['a'].is_known():
            val = safe_sqrt(netw.vars['diagonal'].value**2 - netw.vars['a'].value**2)
            if val is not None:
                res['b'] = val
        return res or None

    net.add_constraint(Constraint(
        name="diag_reverse",
        nodes=['a','b','diagonal'],
        flex_func=diag_to_sides,
        description="Reverse diag -> sides"
    ))

    # --- NEW: Parallelogram area (if a, b and included angle A known) ---
    def parallelogram_area(netw, known, unknown):
        if 'area' not in unknown:
            return None
        if netw.vars['a'].is_known() and netw.vars['b'].is_known() and netw.vars['A'].is_known():
            return {'area': netw.vars['a'].value * netw.vars['b'].value * math.sin(math.radians(netw.vars['A'].value))}
        return None

    net.add_constraint(Constraint(
        name="parallelogram_area",
        nodes=['a','b','A','area'],
        flex_func=parallelogram_area,
        description="Area = a * b * sin(A) (useful for parallelogram)"
    ))

    # Diện tích hình thang: S = (a + c)/2 * h (a,c là đáy; h chiều cao)
    def trapezoid_area(netw, known, unknown):
        if 'area' not in unknown:
            return None
        if netw.vars['a'].is_known() and netw.vars['c'].is_known() and netw.vars['h'].is_known():
            a_val = netw.vars['a'].value
            c_val = netw.vars['c'].value
            h_val = netw.vars['h'].value
            return {'area': 0.5 * (a_val + c_val) * h_val}
        return None

    net.add_constraint(Constraint(
        name="trapezoid_area",
        nodes=['a','c','h','area'],
        flex_func=trapezoid_area,
        description="Area = (a+c)/2 * h (trapezoid)"
    ))

    # Suy ra chiều cao từ diện tích và 2 đáy
    def height_from_trapezoid_area(netw, known, unknown):
        if 'h' not in unknown:
            return None
        if netw.vars['area'].is_known() and netw.vars['a'].is_known() and netw.vars['c'].is_known():
            area_val = netw.vars['area'].value
            a_val = netw.vars['a'].value
            c_val = netw.vars['c'].value
            if (a_val + c_val) != 0:
                return {'h': 2.0 * area_val / (a_val + c_val)}
        return None

    net.add_constraint(Constraint(
        name="trapezoid_height_from_area",
        nodes=['a','c','h','area'],
        flex_func=height_from_trapezoid_area,
        description="h = 2*area/(a+c) (trapezoid)"
    ))
    
    # Reverse area for rectangle: if area and one side known, compute other side
    def area_reverse_rect(netw, known, unknown):
        res = {}
        if 'area' in known and 'area' not in unknown:
            area_val = netw.vars['area'].value
            if area_val is not None and area_val > 0:
                # Rectangle: area = a * b
                if 'a' in known and 'b' in unknown:
                    a = netw.vars['a'].value
                    if a is not None and a > 0:
                        res['b'] = area_val / a
                if 'b' in known and 'a' in unknown:
                    b = netw.vars['b'].value
                    if b is not None and b > 0:
                        res['a'] = area_val / b
        return res or None
    
    net.add_constraint(Constraint(
        name="area_reverse_rect",
        nodes=['a','b','area'],
        flex_func=area_reverse_rect,
        description="Reverse area: compute side from area and other side (rectangle)"
    ))

    # --- MỚI: Tổng 4 góc = 360° (các ràng buộc tính từng góc nếu biết 3 góc)
    net.add_constraint(Constraint(
        name="sum_angle_A_quad",
        nodes=['A','B','C','D'],
        forward_func=lambda vals: 360.0 - vals['B'] - vals['C'] - vals['D'],
        dependencies=['B','C','D'],
        target='A',
        description="A = 360 - B - C - D"
    ))
    net.add_constraint(Constraint(
        name="sum_angle_B_quad",
        nodes=['A','B','C','D'],
        forward_func=lambda vals: 360.0 - vals['A'] - vals['C'] - vals['D'],
        dependencies=['A','C','D'],
        target='B',
        description="B = 360 - A - C - D"
    ))
    net.add_constraint(Constraint(
        name="sum_angle_C_quad",
        nodes=['A','B','C','D'],
        forward_func=lambda vals: 360.0 - vals['A'] - vals['B'] - vals['D'],
        dependencies=['A','B','D'],
        target='C',
        description="C = 360 - A - B - D"
    ))
    net.add_constraint(Constraint(
        name="sum_angle_D_quad",
        nodes=['A','B','C','D'],
        forward_func=lambda vals: 360.0 - vals['A'] - vals['B'] - vals['C'],
        dependencies=['A','B','C'],
        target='D',
        description="D = 360 - A - B - C"
    ))

    return net
