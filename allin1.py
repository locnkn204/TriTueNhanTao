from engine import ConstraintNetwork
import geometry_kb as kb
import networkx as nx
import math
from typing import Tuple

def score_network(net: ConstraintNetwork, other: ConstraintNetwork) -> int:
    known = sum(1 for v in net.vars.values() if v.is_known())
    unique_known = sum(1 for n, v in net.vars.items() if n not in other.vars and v.is_known())
    return known + unique_known * 2

def print_status(tri, rect):
    print("\n[STATUS] Triangle known vars:")
    for n, v in tri.get_results().items():
        src = tri.get_provenance().get(n)
        print(f"  {n}: {v}  (source={src})")
    print("[STATUS] Rectangle known vars:")
    for n, v in rect.get_results().items():
        src = rect.get_provenance().get(n)
        print(f"  {n}: {v}  (source={src})")

def validate_triangle(net: ConstraintNetwork) -> bool:
    # check triangle inequality when a,b,c known (use is not None to allow 0.0)
    a = net.vars.get('a').value if 'a' in net.vars else None
    b = net.vars.get('b').value if 'b' in net.vars else None
    c = net.vars.get('c').value if 'c' in net.vars else None
    if a is not None and b is not None and c is not None:
        return (a + b > c + 1e-9) and (a + c > b + 1e-9) and (b + c > a + 1e-9)
    return True

def main():
    tri = kb.create_triangle_network()
    rect = kb.create_rectangle_network()
    # enable debug on networks for tracing if needed
    tri.debug = False
    rect.debug = False

    # --- Names / canonical sets used for classification and input resolution ---
    tri_side_names = {'a', 'b', 'c'}
    rect_side_names = {'a', 'b', 'c', 'd'}
    tri_angle_names = {'A', 'B', 'C'}
    rect_angle_names = {'A', 'B', 'C', 'D'}

    # Build combined mapping early so resolve_name can use it
    combined = {}
    for n, v in tri.vars.items():
        combined[n] = v.description or n
    for n, v in rect.vars.items():
        if n not in combined:
            combined[n] = v.description or n
    # --- end names setup ---

    # track what the user actually assigned
    assigned_inputs = {}  # name -> value
    autosolve = False     # toggle for auto compute after assignment

    # build canonical name map (case-insensitive resolution)
    canonical_names = {}
    for n in list(tri.vars.keys()) + list(rect.vars.keys()):
        lower = n.lower()
        canonical_names.setdefault(lower, []).append(n)

    def resolve_name(input_name: str) -> str:
        if input_name in combined:
            return input_name
        key = input_name.strip()
        if key in combined:
            return key
        low = key.lower()
        if low in canonical_names:
            candidates = canonical_names[low]
            if len(candidates) == 1:
                return candidates[0]
            # prefer exact case match if exists
            for c in candidates:
                if c == key:
                    return c
            # ambiguous: return first (but warn)
            return candidates[0]
        return key

    # input validation
    def validate_input_name_value(name: str, value: float) -> Tuple[bool, str]:
        # sides must be > 0
        if name in ('a','b','c','d') and (value is None or value <= 0.0):
            return False, "Side values must be > 0"
        # angles should be in (0,360)
        if name in ('A','B','C','D') and (value is None or value <= 0.0 or value >= 360.0):
            return False, "Angle must be between 0 and 360 (exclusive)"
        return True, ""

    # --- helper to pick network (reuse classification + fallback) ---
    def choose_network():
        # classification rules (priority)
        # Use exact name matching (case-sensitive): sides are lowercase, angles uppercase.
        tri_side_count = sum(1 for n in assigned_inputs if n in tri_side_names)
        rect_side_count = sum(1 for n in assigned_inputs if n in rect_side_names)
        tri_angle_count = sum(1 for n in assigned_inputs if n in tri_angle_names)
        rect_angle_count = sum(1 for n in assigned_inputs if n in rect_angle_names)
        has_d = ('d' in assigned_inputs) or ('D' in assigned_inputs)

        # If user explicitly provided edge/angle d => chắc chắn tứ giác
        if has_d:
            return rect, "Quadrilateral (d provided)"

        # If user explicitly provided 3 sides or 3 angles -> classify as triangle (verify inequality if possible)
        if tri_side_count >= 3:
            # quick triangle inequality check using assigned inputs if all three provided
            a = assigned_inputs.get('a'); b = assigned_inputs.get('b'); c = assigned_inputs.get('c')
            if a is not None and b is not None and c is not None:
                if (a + b > c) and (a + c > b) and (b + c > a):
                    return tri, f"Triangle (by 3 sides)"
                else:
                    # If three sides incompatible, still prefer triangle but warn
                    return tri, f"Triangle (3 sides provided — but may violate triangle inequality)"
            return tri, f"Triangle (>=3 sides provided)"
        if tri_angle_count >= 3:
            return tri, f"Triangle (by 3 angles provided)"

        # If 4 sides or 4 angles -> quadrilateral
        if rect_side_count >= 4 or rect_angle_count >= 4:
            return rect, f"Quadrilateral (by 4 sides/angles provided)"

        # NEW RULE: If there is a right angle (≈90°) among assigned angle names AND
        # at least two adjacent sides (a&b, b&c, c&d, d&a) are provided, prefer rectangle.
        # Use exact-name checks to avoid treating 'A' as 'a'.
        right_angles = [name for name, val in assigned_inputs.items()
                        if name in rect_angle_names and isinstance(val, (int, float)) and abs(val - 90.0) <= 0.1]
        if right_angles:
            assigned_sides = set(n for n in assigned_inputs if n in rect_side_names)
            adjacent_pairs = [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'a')]
            has_adjacent = any(p[0] in assigned_sides and p[1] in assigned_sides for p in adjacent_pairs)
            # only prefer rectangle if we do not already have strong triangle evidence (3 sides)
            if has_adjacent and tri_side_count < 3:
                return rect, f"Rectangle (right angle {right_angles[0]} and adjacent sides provided)"
            # nếu có góc vuông + >=2 cạnh bất kỳ (kể cả chưa biết kề), ưu tiên tứ giác để tránh gán nhầm tam giác
            if len(assigned_sides) >= 2 and tri_side_count < 3:
                return rect, f"Quadrilateral (right angle {right_angles[0]} present)"

        # Nếu đã nhập >=2 cạnh nhưng có cả dữ liệu tứ giác (góc D hoặc cạnh d) ưu tiên tứ giác
        if rect_side_count >= 2 and rect_angle_count >= 2:
            return rect, "Quadrilateral (mixed quad data)"
        if rect_side_count >= 2 and tri_side_count == 0:
            return rect, "Quadrilateral (only quad sides given)"

        # fallback to scoring if no clear structural rule matched
        tscore = score_network(tri, rect)
        rscore = score_network(rect, tri)
        if tscore == 0 and rscore == 0:
            return None, None
        chosen = tri if tscore >= rscore else rect
        kind = "Triangle" if chosen is tri else "Rectangle"
        return chosen, f"{kind} (scores tri={tscore}, rect={rscore})"
    # --- end helper ---

    # --- helper to solve and display computed results (no graph) ---
    def display_solution(chosen, kind):
        if chosen is None:
            print("No network could be selected.")
            return

        # If triangle chosen, check SSA ambiguous pattern in assigned inputs
        if chosen is tri:
            ssa_solutions = detect_ssa_cases(assigned_inputs)
            if ssa_solutions:
                print(f"[SSA] Detected ambiguous case: {len(ssa_solutions)} candidate solution(s).")
                # For each candidate, create fresh triangle network, apply values and solve/display
                for idx, sol_assign in enumerate(ssa_solutions, start=1):
                    print(f"\n--- SSA candidate #{idx} ---")
                    tri_candidate = kb.create_triangle_network()
                    # set user-provided values from original assigned_inputs and computed ones
                    for k, v in sol_assign.items():
                        if v is not None:
                            tri_candidate.set_input(k, v, source='user')
                    # solve candidate
                    ok, diagnostics = tri_candidate.solve()
                    res = tri_candidate.get_results()
                    print(f"Candidate #{idx} results:")
                    for k, vv in sorted(res.items()):
                        print(f"  {k}: {vv}")
                    if not ok:
                        blocked = diagnostics.get('blocked_constraints') if diagnostics else None
                        rounds = diagnostics.get('rounds') if diagnostics else None
                        print(f"  (Solver diagnostics: rounds={rounds}, blocked={blocked})")
                # After showing SSA candidates, return (do not run normal solve on ambiguous original)
                return

        # Heuristic support cho tứ giác: nếu có góc vuông và thiếu cạnh đối, điền vào để tính chu vi/diagonal
        if chosen is rect:
            right_angle_any = any(name in rect_angle_names and isinstance(val, (int,float)) and abs(val-90.0) <= 0.1
                                  for name, val in assigned_inputs.items())
            if right_angle_any:
                # copy opposite sides nếu thiếu (giả định hình bình hành/ chữ nhật)
                if rect.vars.get('a') and rect.vars['a'].is_known() and rect.vars.get('c') and not rect.vars['c'].is_known():
                    rect.set_input('c', rect.vars['a'].value, source='rect_assume')
                if rect.vars.get('c') and rect.vars['c'].is_known() and rect.vars.get('a') and not rect.vars['a'].is_known():
                    rect.set_input('a', rect.vars['c'].value, source='rect_assume')
                if rect.vars.get('b') and rect.vars['b'].is_known() and rect.vars.get('d') and not rect.vars['d'].is_known():
                    rect.set_input('d', rect.vars['b'].value, source='rect_assume')
                if rect.vars.get('d') and rect.vars['d'].is_known() and rect.vars.get('b') and not rect.vars['b'].is_known():
                    rect.set_input('b', rect.vars['d'].value, source='rect_assume')
                # nếu chỉ có 1 cạnh biết -> giả định hình vuông tối thiểu
                side_values = [rect.vars[s].value for s in ('a','b','c','d') if rect.vars.get(s) and rect.vars[s].is_known()]
                if len(side_values) == 1:
                    val = side_values[0]
                    for s in ('a','b','c','d'):
                        if rect.vars.get(s) and not rect.vars[s].is_known():
                            rect.set_input(s, val, source='rect_assume')

        # Solve first to get derived values, then classify using computed values.
        print(f"Solving ({kind})...")
        ok, diagnostics = chosen.solve()
        if not ok:
            print("Solver reached iteration limit; partial results available.")
            # print diagnostics if available
            if diagnostics:
                blocked = diagnostics.get('blocked_constraints')
                rounds = diagnostics.get('rounds')
                print(f"  Diagnostics: rounds={rounds}, blocked_constraints={blocked}")
        res = chosen.get_results()

        # Basic validation of numeric inputs / computed values
        def any_negative_sides(ns):
            for side in ('a','b','c','d'):
                v = ns.get(side)
                if v is not None and v <= 0:
                    return True, side
            return False, None
        neg, neg_name = any_negative_sides(res)
        if neg:
            print(f"ERROR: Side {neg_name} <= 0. All sides must be > 0.")
            return
        # Sum-of-angles check for triangles/quads if angles present
        def check_angle_sum_triangle(ns):
            vals = [ns.get('A'), ns.get('B'), ns.get('C')]
            if all(v is not None for v in vals):
                if abs(sum(vals) - 180.0) > 1e-3:
                    return False
            return True
        def check_angle_sum_quad(ns):
            vals = [ns.get('A'), ns.get('B'), ns.get('C'), ns.get('D')]
            if all(v is not None for v in vals):
                if abs(sum(vals) - 360.0) > 1e-2:
                    return False
            return True

        # Classification helpers (use computed/res values)
        def classify_triangle_from_res(ns):
            # Returns (type_name, inheritance_list)
            a,b,c = ns.get('a'), ns.get('b'), ns.get('c')
            A,B,C = ns.get('A'), ns.get('B'), ns.get('C')
            eps = 1e-6
            # helpers
            def close(x,y,thr=1e-6):
                return x is not None and y is not None and abs(x-y) < thr
            # compute flags (use is not None checks)
            equilateral = (a is not None and b is not None and c is not None and close(a,b) and close(b,c))
            isos = ((a is not None and b is not None and close(a,b))
                    or (a is not None and c is not None and close(a,c))
                    or (b is not None and c is not None and close(b,c)))
            right_angle_by_val = ((A is not None and abs(A-90) < 0.1)
                                  or (B is not None and abs(B-90) < 0.1)
                                  or (C is not None and abs(C-90) < 0.1))
            right_by_pyth = False
            if a is not None and b is not None and c is not None:
                if abs(a*a + b*b - c*c) < 1e-3 or abs(a*a + c*c - b*b) < 1e-3 or abs(b*b + c*c - a*a) < 1e-3:
                    right_by_pyth = True
            right = right_angle_by_val or right_by_pyth

            # Decide most specific -> general, and inheritance chain
            if equilateral:
                return "Equilateral", ["Equilateral", "Isosceles", "Triangle"]
            if right and isos:
                return "Right Isosceles", ["Right Isosceles", "Right", "Isosceles", "Triangle"]
            if right:
                return "Right", ["Right", "Triangle"]
            if isos:
                return "Isosceles", ["Isosceles", "Triangle"]
            # default
            if any(x is not None for x in (a,b,c,A,B,C)):
                return "Scalene", ["Scalene", "Triangle"]
            return "Unknown Triangle", ["Triangle"]

        def classify_quad_from_res(ns):
            # Returns (type_name, inheritance_list)
            a,b,c,d = ns.get('a'), ns.get('b'), ns.get('c'), ns.get('d')
            A,B,C,D = ns.get('A'), ns.get('B'), ns.get('C'), ns.get('D')
            eps = 1e-6
            def close(x,y,thr=1e-6):
                return x is not None and y is not None and abs(x-y) < thr
            # flags
            all_sides_known = all(x is not None for x in (a,b,c,d))
            all_sides_equal = all_sides_known and close(a,b) and close(b,c) and close(c,d)
            all_angles_known = all(x is not None for x in (A,B,C,D))
            all_angles_90 = all_angles_known and all((x is not None and abs(x-90) < 0.1) for x in (A,B,C,D))
            right_any = any(x is not None and abs(x-90) < 0.1 for x in (A,B,C,D))
            opp_sides_equal = (a is not None and c is not None and close(a,c)) and (b is not None and d is not None and close(b,d))
            opp_angles_equal = (A is not None and C is not None and close(A,C,1e-3)) and (B is not None and D is not None and close(B,D,1e-3))
            # detect square
            if (all_sides_equal or (right_any and all_sides_known and close(a,b) and close(b,c) and close(c,d))) or (right_any and a is not None and b is not None and c is not None and d is not None and close(a,b) and close(b,d) and close(d,c)):
                if right_any:
                    return "Square", ["Square", "Rectangle", "Parallelogram", "Quadrilateral"]
            # rectangle
            if (all_angles_90 or right_any) and (opp_sides_equal or (a is not None and b is not None)):
                return "Rectangle", ["Rectangle", "Parallelogram", "Quadrilateral"]
            # rhombus (all sides equal but angles not necessarily 90)
            if all_sides_equal and (opp_angles_equal or opp_sides_equal):
                return "Rhombus", ["Rhombus", "Parallelogram", "Quadrilateral"]
            # parallelogram
            if opp_sides_equal or opp_angles_equal:
                return "Parallelogram", ["Parallelogram", "Quadrilateral"]
            # trapezoid detection heuristic: if a||c or b||d approximated by adjacent angle sums = 180
            def adjacent_sum_180(x,y):
                return x is not None and y is not None and abs((x + y) - 180.0) < 0.1
            trapezoid = False
            if (A is not None and B is not None and adjacent_sum_180(A,B)) or (B is not None and C is not None and adjacent_sum_180(B,C)) or (C is not None and D is not None and adjacent_sum_180(C,D)) or (D is not None and A is not None and adjacent_sum_180(D,A)):
                trapezoid = True
            if trapezoid:
                # isosceles trapezoid heuristic: non-parallel sides equal
                is_isos_trap = (b is not None and d is not None and close(b,d)) or (a is not None and c is not None and close(a,c))
                if is_isos_trap:
                    return "Isosceles Trapezoid", ["Isosceles Trapezoid", "Trapezoid", "Quadrilateral"]
                return "Trapezoid", ["Trapezoid", "Quadrilateral"]
            # fallback
            if any(x is not None for x in (a,b,c,d,A,B,C,D)):
                return "Quadrilateral (general)", ["Quadrilateral"]
            return "Unknown Quadrilateral", ["Quadrilateral"]

        # run specific checks & classification
        if chosen is tri:
            # angle bounds for triangle
            for ang_name in ('A','B','C'):
                ang_val = res.get(ang_name)
                if ang_val is not None and (ang_val <= 0 or ang_val >= 180):
                    print(f"ERROR: Angle {ang_name} invalid for triangle (must be between 0 and 180).")
                    return
            if not check_angle_sum_triangle(res):
                print("ERROR: Sum of triangle angles != 180° (inconsistent data).")
                return
            if not validate_triangle(chosen):
                print("ERROR: Triangle inequality may be violated for provided sides.")
                return
            # require at least 3 known basic attributes to conclude
            known_basic = [k for k in ('a','b','c','A','B','C') if res.get(k) is not None]
            if len(known_basic) < 3:
                print("Insufficient data to determine triangle fully. Need at least 3 values among sides/angles.")
                return
            # warn if provided angle inconsistent with side-based computation
            for ang_name in ('A','B','C'):
                if ang_name in assigned_inputs and res.get(ang_name) is not None:
                    if abs(assigned_inputs[ang_name] - res[ang_name]) > 0.5:
                        print(f"WARNING: Input angle {ang_name}={assigned_inputs[ang_name]} differs from computed {res[ang_name]:.2f}. Using computed value.")
            kind_name, inheritance = classify_triangle_from_res(res)
            # near-equilateral hint
            a,b,c = res.get('a'), res.get('b'), res.get('c')
            if all(x is not None for x in (a,b,c)):
                avg = (a+b+c)/3.0
                if avg > 0:
                    max_dev = max(abs(a-avg), abs(b-avg), abs(c-avg)) / avg
                    if max_dev < 0.001 and kind_name != "Equilateral":
                        print("Note: Triangle is nearly equilateral (deviation <0.1%).")
            print(f"\nDetected shape: {kind_name} (Triangle)")
            print("Inheritance:", " > ".join(inheritance))
        else:
            if not check_angle_sum_quad(res):
                print("ERROR: Sum of 4 angles != 360° (invalid quadrilateral angles).")
                return
            kind_name, inheritance = classify_quad_from_res(res)
            print(f"\nDetected shape: {kind_name} (Quadrilateral)")
            print("Inheritance:", " > ".join(inheritance))

        # print computed results
        print("\nComputed results:")
        for k, v in sorted(res.items()):
            print(f"  {k}: {v}")
        # perimeter/area hints
        if chosen is tri:
            a,b,c = res.get('a'), res.get('b'), res.get('c')
            if all(x is not None for x in (a,b,c)):
                print(f"  Perimeter: {a+b+c}")
        else:
            a,b,c,d = res.get('a'), res.get('b'), res.get('c'), res.get('d')
            if a is not None and b is not None:
                print(f"  Perimeter (approx): {2*(a+b)} (if a,b adjacent)")
            elif all(x is not None for x in (a,b,c,d)):
                print(f"  Perimeter: {a+b+c+d}")
        print("")  # spacer
    # --- end helper ---

    # --- NEW: SSA ambiguous case detection for triangle ---
    def detect_ssa_cases(assigned: dict):
        """
        Detect SSA pattern and return list of possible solution assignments (each a dict of vars).
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
            # third_side_name opposite third_angle_name
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
    # --- end SSA support ---

    # Print available variables using the combined mapping already built earlier
    print("Available variables (tên : mô tả):")
    for name in sorted(combined.keys()):
        print(f"  {name} : {combined[name]}")
    # Print supported shapes summary
    print("\nSupported shapes (detected by system):")
    print("  Triangles: Equilateral, Isosceles, Right, Right Isosceles, Scalene (general Triangle)")
    print("  Quadrilaterals: Square, Rectangle, Rhombus, Parallelogram, Isosceles Trapezoid, Trapezoid, General Quadrilateral")

    # Restore the interactive loop and finalization (was accidentally removed)
    print("Commands: 'status', 'reset', 'show', 'compute', 'autosolve on/off', 'debug on/off', 'done'. Input: a 3 or a=3")

    while True:
        line = input(">> ").strip()
        if not line:
            continue
        if line.lower() == 'autosolve on':
            autosolve = True
            print("autosolve enabled")
            continue
        if line.lower() == 'autosolve off':
            autosolve = False
            print("autosolve disabled")
            continue
        if line.lower() == 'debug on':
            tri.debug = rect.debug = True
            print("debug enabled")
            continue
        if line.lower() == 'debug off':
            tri.debug = rect.debug = False
            print("debug disabled")
            continue
        if line.lower() == 'compute':
            chosen, kind = choose_network()
            display_solution(chosen, kind)
            continue
        if line.lower() == 'done':
            break
        if line.lower() == 'status':
            print_status(tri, rect); continue
        if line.lower() == 'reset':
            tri.reset(); rect.reset(); assigned_inputs.clear(); print("Reset done."); continue
        if line.lower() == 'show':
            print("Triangle adjacency:", nx.adjacency_matrix(tri.graph).shape)
            print("Rectangle adjacency:", nx.adjacency_matrix(rect.graph).shape)
            continue

        # parse assignment (allow expressions like 2*3? minimal: eval safe numeric)
        try:
            if '=' in line:
                name_raw, val_raw = line.split('=', 1)
            else:
                parts = line.split()
                if len(parts) != 2:
                    print("Bad input")
                    continue
                name_raw, val_raw = parts
            name_candidate = name_raw.strip()
            # resolve to canonical
            name = resolve_name(name_candidate)
            # safe eval simple numeric expression (digits, ., + - * / parentheses)
            import re
            if not re.match(r'^[0-9\.\+\-\*\/\(\)\s]+$', val_raw.strip()):
                # try plain float parse if expression not allowed
                val = float(val_raw.strip())
            else:
                val = float(eval(val_raw.strip(), {"__builtins__":{}}))
        except Exception:
            print("Parse error")
            continue

        if name not in combined:
            print("Unknown var")
            continue

        ok, msg = validate_input_name_value(name, val)
        if not ok:
            print("Invalid input:", msg)
            continue

        # assign to networks that contain the var (use provenance 'user')
        if name in tri.vars:
            tri.set_input(name, val, source='user')
        if name in rect.vars:
            rect.set_input(name, val, source='user')

        # record assigned inputs for later classification
        assigned_inputs[name] = val

        # Early triangle inequality check: if we now have 3 sides, validate immediately
        if name in tri_side_names:
            a = assigned_inputs.get('a')
            b = assigned_inputs.get('b')
            c = assigned_inputs.get('c')
            if a is not None and b is not None and c is not None:
                if not ((a + b > c) and (a + c > b) and (b + c > a)):
                    print(f"WARNING: Triangle inequality may be violated: a={a}, b={b}, c={c}")
                    print("  (a+b > c, a+c > b, b+c > a must all be true)")

        print(f"Set {name} = {val}")

        if autosolve:
            chosen, kind = choose_network()
            display_solution(chosen, kind)
        else:
            print("Assigned. Use command 'compute' to auto-detect shape and compute results when ready.")

    # final compute if user wants
    if assigned_inputs:
        chosen, kind = choose_network()
        if chosen is None:
            print("No network selected; exiting.")
        else:
            print(f"Final auto-detected: {kind}")
            display_solution(chosen, kind)
    else:
        print("No input; exiting.")
if __name__ == "__main__":
    main()
