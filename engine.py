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

    def set_input(self, name: str, value: float, source: str = 'user'):
        if name not in self.vars:
            self.add_variable(name)
        changed = self.vars[name].set(value, source=source)
        if changed:
            if self.debug:
                self.log(f"Input set {name}={value} (source={source})")
            self.propagate_from(name)

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
