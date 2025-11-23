import math
import networkx as nx
import matplotlib.pyplot as plt
from typing import Callable, Dict, List, Optional, Any, Tuple

EPSILON = 1e-9
DEFAULT_ANGLE_TOL = 0.1  # degrees tolerance for 90°

def safe_sqrt(x: float) -> Optional[float]:
    if x is None:
        return None
    if x < 0 and x > -1e-12:
        x = 0.0
    if x < 0:
        return None
    return math.sqrt(x)

def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))

class Var:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.value: Optional[float] = None
        self.source: Optional[str] = None  # provenance: 'user' or constraint name
        self.constraints: List['Constraint'] = []

    def is_known(self) -> bool:
        return self.value is not None

    def set(self, v: Optional[float], source: Optional[str] = None) -> bool:
        """Set value with provenance. Returns True if value changed (beyond EPSILON)."""
        if v is None:
            return False
        try:
            v = float(v)
        except Exception:
            return False
        # Validation trước khi normalize
        if self.name in ('A', 'B', 'C'):  # Triangle angles
            if v <= 0 or v >= 180:
                raise ValueError(f"Triangle angle {self.name} must be in (0, 180)")
            # Không cần chuẩn hóa góc tam giác
        elif self.name == 'D':  # Quadrilateral angle
            if v <= 0 or v >= 360:
                raise ValueError(f"Quadrilateral angle {self.name} must be in (0, 360)")
            v = v % 360.0  # Chỉ chuẩn hóa góc tứ giác
        if self.value is None or abs(self.value - v) > EPSILON:
            self.value = v
            self.source = source
            return True
        # if same within EPSILON, still update source if previously None
        if self.source is None and source is not None:
            self.source = source
        return False

    def __repr__(self):
        val = self.value if self.value is not None else 'Unknown'
        src = f" ({self.source})" if self.source else ""
        return f"{self.name}: {val}{src}"

class Constraint:
    """
    Two supported forms:
    1) forward_func(values_dict) with dependencies list and single target name -> returns numeric
    2) flex_func(network, known_list, unknown_list) -> returns dict{name: value} or None
    """
    def __init__(self, name: str, nodes: List[str], *,
                 forward_func: Optional[Callable[[Dict[str, float]], Optional[float]]] = None,
                 dependencies: Optional[List[str]] = None,
                 target: Optional[str] = None,
                 flex_func: Optional[Callable[['ConstraintNetwork', List[str], List[str]], Optional[Dict[str,float]]]] = None,
                 description: str = ""):
        self.name = name
        self.nodes = nodes
        self.forward_func = forward_func
        self.dependencies = dependencies or []
        self.target = target
        self.flex_func = flex_func
        self.description = description

    def try_apply(self, net: 'ConstraintNetwork') -> Dict[str, float]:
        updates: Dict[str, float] = {}
        # Flex function path: allow computing multiple unknowns
        if self.flex_func:
            known = [n for n in self.nodes if net.vars[n].is_known()]
            unknown = [n for n in self.nodes if not net.vars[n].is_known()]
            if not unknown:
                return {}
            try:
                res = self.flex_func(net, known, unknown)
                if isinstance(res, dict):
                    for k, v in res.items():
                        if k in net.vars and v is not None:
                            updates[k] = float(v)
                return updates
            except Exception:
                if net.debug:
                    net.log(f"[Constraint {self.name}] flex_func exception")
                return {}

        # Forward path: single target, dependencies must be known
        if self.forward_func and self.target:
            if net.vars[self.target].is_known():
                return {}
            for dep in self.dependencies:
                if dep not in net.vars or not net.vars[dep].is_known():
                    return {}
            values = {d: net.vars[d].value for d in self.dependencies}
            try:
                res = self.forward_func(values)
                if res is None:
                    return {}
                res = float(res)
                updates[self.target] = res
            except Exception:
                if net.debug:
                    net.log(f"[Constraint {self.name}] forward_func exception with values={values}")
                return {}
        return updates

class ConstraintNetwork:
    def __init__(self, *, debug: bool = False):
        self.vars: Dict[str, Var] = {}
        self.constraints: List[Constraint] = []
        self.graph = nx.Graph()
        self.debug = debug
        self.diagnostics: Dict[str, Any] = {}

    def log(self, msg: str):
        if self.debug:
            print("[DEBUG]", msg)

    def add_variable(self, name: str, description: str = ""):
        if name in self.vars:
            return
        v = Var(name, description)
        self.vars[name] = v
        self.graph.add_node(name, type='var', label=name)

    def add_constraint(self, constraint: Constraint):
        self.constraints.append(constraint)
        for n in constraint.nodes:
            if n in self.vars:
                self.vars[n].constraints.append(constraint)
            else:
                self.add_variable(n)
                self.vars[n].constraints.append(constraint)
        self.graph.add_node(constraint.name, type='constraint', label=constraint.name)
        for n in constraint.nodes:
            self.graph.add_edge(constraint.name, n)

    def set_input(self, name: str, value: float, source: str = 'user', tolerance: float = 1e-2) -> Tuple[bool, str]:
        """
        Gán giá trị đầu vào với cơ chế kiểm tra tính nhất quán (Consistency Check).
        Trả về: (Thành công: bool, Thông báo: str)
        """
        if name not in self.vars:
            self.add_variable(name)
        
        var = self.vars[name]
        
        # 1. KIỂM TRA XUNG ĐỘT TRỰC TIẾP
        # Nếu biến đã có giá trị (do máy tính đã tính ra từ trước), kiểm tra xem giá trị mới nhập có khớp không.
        if var.is_known():
            current_val = var.value
            # Nếu chênh lệch quá lớn -> Báo lỗi mâu thuẫn
            if abs(current_val - value) > tolerance:
                return False, (f"Xung đột dữ liệu! Giá trị '{name}' bạn nhập ({value}) "
                               f"mâu thuẫn với giá trị đã tính toán trước đó ({current_val:.4f}).\n"
                               f"Chênh lệch: {abs(current_val - value):.4f}")
            else:
                # Nếu chênh lệch nhỏ (sai số làm tròn), cập nhật lại để giao diện hiện đúng số user nhập
                var.set(value, source=source)
                return True, "Updated (refinement)"

        # 2. GÁN GIÁ TRỊ VÀ LAN TRUYỀN (PROPAGATE)
        # Lưu trạng thái cũ để Rollback (hoàn tác) nếu phát hiện lỗi sau khi tính toán
        prev_states = {n: (v.value, v.source) for n, v in self.vars.items()}
        
        changed = var.set(value, source=source)
        if changed:
            if self.debug:
                self.log(f"Input set {name}={value} (source={source})")
            
            # Kích hoạt lan truyền để tính ra các biến phụ thuộc
            self.propagate_from(name)

            # 3. KIỂM TRA TỔNG QUÁT: CHU VI (PERIMETER CHECK)
            # Logic này sửa lỗi "Dương tính giả" khi mạng lưới có biến thừa (như biến 'd' trong tam giác)
            tol = 1e-4
            if 'perimeter' in self.vars and self.vars['perimeter'].is_known() and self.vars['perimeter'].source == 'user':
                p = self.vars['perimeter'].value

                # [FIX THÔNG MINH] Lọc danh sách cạnh: Chỉ lấy những cạnh THỰC SỰ liên kết với Chu vi
                # Thay vì lấy tất cả a,b,c,d, ta quét xem biến perimeter dính dáng đến ai.
                relevant_sides = set()
                perimeter_var = self.vars['perimeter']
                
                # Quét tất cả các ràng buộc (constraints) dính vào biến perimeter
                for cons in perimeter_var.constraints:
                    # Nếu ràng buộc đó có chứa các biến cạnh a,b,c,d -> Đó là cạnh liên quan
                    for node in cons.nodes:
                        if node in ('a', 'b', 'c', 'd'):
                            relevant_sides.add(node)
                
                # Danh sách cạnh cần kiểm tra (Ví dụ Tam giác chỉ còn a,b,c. Biến d bị loại bỏ)
                sides_in_net = list(relevant_sides)

                # Tính tổng các cạnh ĐÃ BIẾT trong danh sách lọc
                known_sides_vals = [self.vars[s].value for s in sides_in_net if self.vars[s].is_known()]
                sum_known_sides = sum(known_sides_vals)

                # Kiểm tra xem đã biết đủ hết các cạnh liên quan chưa
                all_relevant_sides_known = (len(known_sides_vals) == len(sides_in_net))

                if all_relevant_sides_known:
                    # TRƯỜNG HỢP 1: Đã biết đủ cạnh -> Tổng phải BẰNG chu vi (cho phép sai số)
                    if abs(sum_known_sides - p) > tol:
                        # Có lỗi -> Hoàn tác (Rollback)
                        for n, (val, src) in prev_states.items():
                            self.vars[n].value = val
                            self.vars[n].source = src
                        return False, (f"Mâu thuẫn toán học: Tổng các cạnh tính được ({sum_known_sides:.4f}) "
                                       f"khác với Chu vi bạn nhập ({p}).")
                else:
                    # TRƯỜNG HỢP 2: Chưa biết đủ cạnh -> Tổng hiện tại phải NHỎ HƠN chu vi
                    # (Phải chừa chỗ cho cạnh chưa biết > 0)
                    if sum_known_sides >= p - tol:
                        # Có lỗi -> Hoàn tác
                        for n, (val, src) in prev_states.items():
                            self.vars[n].value = val
                            self.vars[n].source = src
                        return False, (f"Giá trị không hợp lệ: Chu vi = {p} nhỏ hơn hoặc bằng tổng các cạnh đã biết ({sum_known_sides:.4f}). "
                                       "Không còn dư địa cho cạnh còn thiếu.")
        
        return True, "Success"

    def propagate_from(self, start_name: str):
        """Queue-based incremental propagation with provenance logging."""
        queue = [start_name]
        processed = set()
        while queue:
            cur = queue.pop(0)
            if cur not in self.vars:
                continue
            var = self.vars[cur]
            for cons in var.constraints:
                updates = cons.try_apply(self)
                for uname, uval in updates.items():
                    if uname in self.vars and self.vars[uname].set(uval, source=cons.name):
                        if self.debug:
                            self.log(f"  {uname} = {uval:.6g} (from {cons.name})")
                        queue.append(uname)
            processed.add(cur)

    def solve(self, max_rounds: int = 100) -> Tuple[bool, Dict[str, Any]]:
        """Queue-based full solve. Returns (converged, diagnostics)."""
        # initialize queue with all known vars
        queue = [n for n, v in self.vars.items() if v.is_known()]
        rounds = 0
        changed = True
        while rounds < max_rounds and changed:
            changed = False
            rounds += 1
            # process constraints in a deterministic order but use queue to prioritize affected
            # collect candidate constraints from variables in queue
            cons_to_run = set()
            while queue:
                vn = queue.pop(0)
                if vn not in self.vars:
                    continue
                for c in self.vars[vn].constraints:
                    cons_to_run.add(c)
            if not cons_to_run:
                break
            # attempt each constraint
            for cons in sorted(cons_to_run, key=lambda c: c.name):
                updates = cons.try_apply(self)
                for uname, uval in updates.items():
                    if uname in self.vars and self.vars[uname].set(uval, source=cons.name):
                        changed = True
                        queue.append(uname)
            # next round
        converged = not changed
        diagnostics = {}
        if not converged:
            # gather unsatisfied constraints: target unknown but dependencies known (couldn't compute)
            blocked = []
            for cons in self.constraints:
                if cons.flex_func:
                    # skip detailed check for flex constraints
                    continue
                if cons.target and not self.vars[cons.target].is_known():
                    if all(self.vars[d].is_known() for d in cons.dependencies):
                        blocked.append(cons.name)
            diagnostics['blocked_constraints'] = blocked
            diagnostics['rounds'] = rounds
            self.diagnostics = diagnostics
        else:
            self.diagnostics = {'rounds': rounds}
        return converged, self.diagnostics

    def get_results(self) -> Dict[str, Optional[float]]:
        return {n: v.value for n, v in self.vars.items()}

    def get_provenance(self) -> Dict[str, Optional[str]]:
        return {n: v.source for n, v in self.vars.items()}

    def reset(self):
        for v in self.vars.values():
            v.value = None
            v.source = None

    def show_graph(self):
        pos = nx.spring_layout(self.graph)
        plt.figure(figsize=(10, 8))
        var_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'var']
        cons_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'constraint']
        nx.draw_networkx_nodes(self.graph, pos, nodelist=var_nodes, node_color='lightblue', node_size=1200)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=cons_nodes, node_color='lightgreen', node_shape='s', node_size=800)
        nx.draw_networkx_edges(self.graph, pos)
        labels = {n: d.get('label', n) for n, d in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos, labels)
        plt.title("Constraint Network Graph")
        plt.axis('off')
        plt.show()
