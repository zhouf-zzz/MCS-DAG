from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Iterable, Any
import itertools
import math

EPS = 1e-12


class SimulationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MCCTTemplate:
    cid: str
    delta: float
    state: str  # "NS" or "CS"


@dataclass(frozen=True)
class VertexSpec:
    vid: str
    wcet_n: float
    wcet_o: float
    predecessors: Tuple[str, ...] = ()
    successors: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    crit: str  # "LO" or "HI"
    period: float
    deadline: float
    virtual_deadline: float
    vertices: Tuple[VertexSpec, ...]


@dataclass(frozen=True)
class MappedTask:
    task: TaskSpec
    normal_mccts: Tuple[MCCTTemplate, ...]
    critical_mccts: Tuple[MCCTTemplate, ...]
    S_N: float
    S_O: float


@dataclass
class VertexRuntime:
    vid: str
    base_vid: str
    wcet_n_total: float
    wcet_o_total: float
    remaining_n: float
    remaining_o: float
    predecessors: Set[str]
    successors: Set[str]
    finished_n: bool = False
    finished_o: bool = False

    def is_complete_in_mode(self, mode: str) -> bool:
        return self.remaining_n <= EPS if mode == "NS" else self.remaining_o <= EPS

    def current_remaining(self, mode: str) -> float:
        return self.remaining_n if mode == "NS" else self.remaining_o

    def consume(self, mode: str, amount: float) -> None:
        if mode == "NS":
            self.remaining_n = max(0.0, self.remaining_n - amount)
        else:
            self.remaining_o = max(0.0, self.remaining_o - amount)


@dataclass
class MCCTRuntime:
    cid: str
    task_id: str
    job_id: str
    state: str
    delta: float
    busy: bool = False
    current_vid: Optional[str] = None
    abs_deadline: float = math.inf
    remaining_exec: float = 0.0

    def clear(self) -> None:
        self.busy = False
        self.current_vid = None
        self.abs_deadline = math.inf
        self.remaining_exec = 0.0


@dataclass
class JobRuntime:
    job_id: str
    task_id: str
    crit: str
    release_time: float
    abs_deadline: float
    virtual_deadline: float
    vertices: Dict[str, VertexRuntime]
    topo_vids: List[str]
    normal_mccts: List[MCCTRuntime]
    critical_mccts: List[MCCTRuntime]
    completed: bool = False
    failed: bool = False

    def ready_vertices(self, mode: str) -> List[VertexRuntime]:
        out: List[VertexRuntime] = []
        for vid in self.topo_vids:
            v = self.vertices[vid]
            if mode == "NS" and v.finished_n:
                continue
            if mode == "CS" and v.finished_o:
                continue
            if not v.predecessors:
                out.append(v)
        return out

    def active_mccts(self, mode: str) -> List[MCCTRuntime]:
        return self.normal_mccts if mode == "NS" else self.critical_mccts

    def all_mccts(self) -> List[MCCTRuntime]:
        return self.normal_mccts + self.critical_mccts

    def fully_complete(self, mode: str) -> bool:
        return all(v.is_complete_in_mode(mode) for v in self.vertices.values())


@dataclass
class SimulationResult:
    schedulable: bool
    reason: str
    finish_time: float
    jobs_released: int
    jobs_completed: int
    state_switch_time: Optional[float]
    traces: List[str] = field(default_factory=list)


def topo_sort(vertices: Iterable[VertexSpec]) -> List[str]:
    verts = list(vertices)
    indeg = {v.vid: len(v.predecessors) for v in verts}
    succ = {v.vid: list(v.successors) for v in verts}
    q = sorted([vid for vid, d in indeg.items() if d == 0])
    out: List[str] = []
    while q:
        vid = q.pop(0)
        out.append(vid)
        for s in succ[vid]:
            indeg[s] -= 1
            if indeg[s] == 0:
                q.append(s)
                q.sort()
    if len(out) != len(verts):
        raise SimulationError("DAG contains a cycle")
    return out


class SFMCRuntimeSimulator:
    def __init__(self, mapped_tasks: List[MappedTask], m: int, debug: bool = True) -> None:
        if m <= 0:
            raise ValueError("m must be positive")
        self.mapped_tasks = {mt.task.task_id: mt for mt in mapped_tasks}
        self.m = m
        self.debug = debug

        self.now = 0.0
        self.system_mode = "NS"
        self.state_switch_time: Optional[float] = None
        self.traces: List[str] = []

        self._release_counter = itertools.count(1)
        self.active_jobs: Dict[str, JobRuntime] = {}
        self.completed_jobs: Dict[str, JobRuntime] = {}
        self.all_releases: List[Tuple[float, str]] = []

    def log(self, msg: str) -> None:
        if self.debug:
            self.traces.append(f"[{self.now:10.6f}] {msg}")

    def plan_releases(self, horizon: float) -> None:
        self.all_releases.clear()
        for task_id, mt in self.mapped_tasks.items():
            t = 0.0
            while t < horizon - EPS:
                self.all_releases.append((t, task_id))
                t += mt.task.period
        self.all_releases.sort(key=lambda x: (x[0], x[1]))

    def instantiate_job(self, mt: MappedTask, release_time: float) -> JobRuntime:
        task = mt.task
        seq = next(self._release_counter)
        job_id = f"{task.task_id}#{seq}"
        topo = topo_sort(task.vertices)

        vertices: Dict[str, VertexRuntime] = {}
        for v in task.vertices:
            vertices[v.vid] = VertexRuntime(
                vid=v.vid,
                base_vid=v.vid,
                wcet_n_total=v.wcet_n,
                wcet_o_total=v.wcet_o,
                remaining_n=v.wcet_n,
                remaining_o=v.wcet_o,
                predecessors=set(v.predecessors),
                successors=set(v.successors),
            )

        normal_mccts = [MCCTRuntime(t.cid, task.task_id, job_id, "NS", t.delta) for t in mt.normal_mccts]
        critical_mccts = [MCCTRuntime(t.cid, task.task_id, job_id, "CS", t.delta) for t in mt.critical_mccts]

        job = JobRuntime(
            job_id=job_id,
            task_id=task.task_id,
            crit=task.crit,
            release_time=release_time,
            abs_deadline=release_time + task.deadline,
            virtual_deadline=release_time + task.virtual_deadline,
            vertices=vertices,
            topo_vids=topo,
            normal_mccts=normal_mccts,
            critical_mccts=critical_mccts,
        )
        self.log(f"release {job_id} crit={job.crit} D={job.abs_deadline:.3f} D'={job.virtual_deadline:.3f}")
        return job

    def release_jobs_at(self, t: float) -> None:
        remain: List[Tuple[float, str]] = []
        for rt, tid in self.all_releases:
            if abs(rt - t) <= EPS:
                j = self.instantiate_job(self.mapped_tasks[tid], rt)
                self.active_jobs[j.job_id] = j
            else:
                remain.append((rt, tid))
        self.all_releases = remain

    def choose_empty_mcct(self, job: JobRuntime, mode: str) -> Optional[MCCTRuntime]:
        idle = [c for c in job.active_mccts(mode) if not c.busy]
        if not idle:
            return None
        idle.sort(key=lambda c: (-c.delta, c.cid))
        return idle[0]

    def try_dispatch_vertex(self, job: JobRuntime, v: VertexRuntime, mode: str) -> bool:
        mcct = self.choose_empty_mcct(job, mode)
        if mcct is None:
            return False
        work = v.current_remaining(mode)
        finish = self.now + work / mcct.delta
        mcct.busy = True
        mcct.current_vid = v.vid
        mcct.abs_deadline = finish
        mcct.remaining_exec = work / mcct.delta
        self.log(f"dispatch {job.job_id}:{v.vid} -> {mcct.cid} ({mode}, d={finish:.3f})")
        return True

    def dispatch_ready_vertices(self) -> None:
        progressed = True
        while progressed:
            progressed = False
            for jid in list(self.active_jobs.keys()):
                job = self.active_jobs[jid]
                if job.completed or job.failed:
                    continue
                ready = job.ready_vertices(self.system_mode)
                if not ready:
                    continue
                ready.sort(key=lambda v: (job.topo_vids.index(v.vid), -v.current_remaining(self.system_mode), v.vid))
                for v in ready:
                    if self.try_dispatch_vertex(job, v, self.system_mode):
                        progressed = True
                        break

    def busy_mccts(self) -> List[MCCTRuntime]:
        out: List[MCCTRuntime] = []
        for job in self.active_jobs.values():
            if job.completed or job.failed:
                continue
            out.extend([c for c in job.active_mccts(self.system_mode) if c.busy])
        return out

    def currently_running_mccts(self) -> List[MCCTRuntime]:
        b = self.busy_mccts()
        b.sort(key=lambda c: (c.abs_deadline, -c.delta, c.cid))
        return b[: self.m]

    def next_release_time(self) -> Optional[float]:
        return self.all_releases[0][0] if self.all_releases else None

    def next_virtual_deadline_time(self) -> Optional[float]:
        if self.system_mode != "NS":
            return None
        vals = [j.virtual_deadline for j in self.active_jobs.values() if j.crit == "HI" and not j.completed and not j.failed]
        return min(vals) if vals else None

    def next_real_deadline_time(self) -> Optional[float]:
        vals = [j.abs_deadline for j in self.active_jobs.values() if not j.completed and not j.failed]
        return min(vals) if vals else None

    def next_completion_time(self) -> Optional[float]:
        running = self.currently_running_mccts()
        if not running:
            return None
        return self.now + min(c.remaining_exec for c in running)

    def next_event_time(self) -> Optional[float]:
        cand = [self.next_release_time(), self.next_virtual_deadline_time(), self.next_real_deadline_time(), self.next_completion_time()]
        finite = [t for t in cand if t is not None and t >= self.now - EPS]
        return min(finite) if finite else None

    def advance(self, t_next: float) -> None:
        if t_next < self.now - EPS:
            raise SimulationError("time cannot go backwards")
        dt = t_next - self.now
        if dt <= EPS:
            self.now = t_next
            return

        for c in self.currently_running_mccts():
            c.remaining_exec = max(0.0, c.remaining_exec - dt)
            j = self.active_jobs[c.job_id]
            if c.current_vid is None:
                raise SimulationError("busy MCCT without current vertex")
            j.vertices[c.current_vid].consume(c.state, dt * c.delta)
        self.now = t_next

    def handle_completed_mccts(self) -> None:
        for job in list(self.active_jobs.values()):
            for c in job.all_mccts():
                if not c.busy or c.remaining_exec > EPS:
                    continue
                if c.current_vid is None:
                    raise SimulationError("completed MCCT without vertex")
                v = job.vertices[c.current_vid]
                if c.state == "NS":
                    v.finished_n = True
                else:
                    v.finished_o = True
                self.log(f"complete {job.job_id}:{v.vid} on {c.cid} ({c.state})")
                for succ_id in list(v.successors):
                    if succ_id in job.vertices:
                        job.vertices[succ_id].predecessors.discard(v.vid)
                c.clear()

            if self.system_mode == "NS" and job.fully_complete("NS"):
                job.completed = True
                self.completed_jobs[job.job_id] = job
                del self.active_jobs[job.job_id]
                self.log(f"job {job.job_id} completed in NS")
            elif self.system_mode == "CS" and job.crit == "HI" and job.fully_complete("CS"):
                job.completed = True
                self.completed_jobs[job.job_id] = job
                del self.active_jobs[job.job_id]
                self.log(f"job {job.job_id} completed in CS")

    def switch_to_cs(self) -> None:
        if self.system_mode == "CS":
            return
        self.system_mode = "CS"
        self.state_switch_time = self.now
        self.log("SYSTEM SWITCH NS -> CS")
        for job in self.active_jobs.values():
            if job.crit == "LO":
                job.failed = True
                self.log(f"drop LO job {job.job_id} after switch to CS")
            for c in job.normal_mccts:
                c.clear()
        for jid in [jid for jid, j in self.active_jobs.items() if j.crit == "LO"]:
            del self.active_jobs[jid]

    def check_virtual_deadline_events(self) -> None:
        if self.system_mode != "NS":
            return
        for job in list(self.active_jobs.values()):
            if job.crit == "HI" and self.now + EPS >= job.virtual_deadline and not job.fully_complete("NS"):
                self.switch_to_cs()
                return

    def check_real_deadline_misses(self) -> Optional[str]:
        for job in self.active_jobs.values():
            if self.now + EPS < job.abs_deadline:
                continue
            done = job.fully_complete("NS") if self.system_mode == "NS" else (job.fully_complete("CS") if job.crit == "HI" else True)
            if not done:
                job.failed = True
                return f"job {job.job_id} missed real deadline at t={self.now:.6f}"
        return None

    def run(self, horizon: float) -> SimulationResult:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        self.plan_releases(horizon)
        self.release_jobs_at(0.0)
        self.dispatch_ready_vertices()

        while True:
            reason = self.check_real_deadline_misses()
            if reason is not None:
                return SimulationResult(False, reason, self.now, next(self._release_counter) - 1, len(self.completed_jobs), self.state_switch_time, self.traces)
            t_next = self.next_event_time()
            if t_next is None or t_next > horizon + EPS:
                break
            self.advance(t_next)
            self.handle_completed_mccts()
            self.release_jobs_at(self.now)
            self.check_virtual_deadline_events()
            self.dispatch_ready_vertices()

        self.now = horizon
        reason = self.check_real_deadline_misses()
        if reason is not None:
            return SimulationResult(False, reason, self.now, next(self._release_counter) - 1, len(self.completed_jobs), self.state_switch_time, self.traces)

        if self.active_jobs:
            return SimulationResult(True, "no deadline miss observed up to horizon; active jobs remain", self.now, next(self._release_counter) - 1, len(self.completed_jobs), self.state_switch_time, self.traces)
        return SimulationResult(True, "all jobs completed without deadline miss", self.now, next(self._release_counter) - 1, len(self.completed_jobs), self.state_switch_time, self.traces)


def make_chain_task(
    *,
    task_id: str,
    crit: str,
    period: float,
    deadline: float,
    virtual_deadline: float,
    wcets_n: List[float],
    wcets_o: List[float],
    normal_deltas: List[float],
    critical_deltas: List[float],
) -> MappedTask:
    if len(wcets_n) != len(wcets_o):
        raise ValueError("wcets_n and wcets_o must match in length")
    vertices: List[VertexSpec] = []
    n = len(wcets_n)
    for i in range(n):
        vid = f"v{i + 1}"
        preds = () if i == 0 else (f"v{i}",)
        succs = () if i == n - 1 else (f"v{i + 2}",)
        vertices.append(VertexSpec(vid=vid, wcet_n=wcets_n[i], wcet_o=wcets_o[i], predecessors=preds, successors=succs))

    task = TaskSpec(task_id=task_id, crit=crit, period=period, deadline=deadline, virtual_deadline=virtual_deadline, vertices=tuple(vertices))
    normal_mccts = tuple(MCCTTemplate(cid=f"{task_id}_NS_{i}", delta=d, state="NS") for i, d in enumerate(normal_deltas))
    critical_mccts = tuple(MCCTTemplate(cid=f"{task_id}_CS_{i}", delta=d, state="CS") for i, d in enumerate(critical_deltas))
    return MappedTask(task=task, normal_mccts=normal_mccts, critical_mccts=critical_mccts, S_N=sum(normal_deltas), S_O=sum(critical_deltas))


def build_mapped_task_from_offline(
    *,
    task_id: str,
    crit: str,
    period: float,
    deadline: float,
    virtual_deadline: float,
    vertices: Iterable[Dict[str, Any]],
    normal_mccts: Iterable[Dict[str, Any]],
    critical_mccts: Iterable[Dict[str, Any]],
) -> MappedTask:
    """Adapter: convert offline mapper output dictionaries to runtime objects."""
    v_specs: List[VertexSpec] = []
    for v in vertices:
        v_specs.append(
            VertexSpec(
                vid=str(v["vid"]),
                wcet_n=float(v["wcet_n"]),
                wcet_o=float(v["wcet_o"]),
                predecessors=tuple(v.get("predecessors", ())),
                successors=tuple(v.get("successors", ())),
            )
        )
    ns = tuple(MCCTTemplate(cid=str(c.get("cid", f"{task_id}_NS_{i}")), delta=float(c["delta"]), state="NS") for i, c in enumerate(normal_mccts))
    cs = tuple(MCCTTemplate(cid=str(c.get("cid", f"{task_id}_CS_{i}")), delta=float(c["delta"]), state="CS") for i, c in enumerate(critical_mccts))
    t = TaskSpec(task_id=task_id, crit=crit, period=period, deadline=deadline, virtual_deadline=virtual_deadline, vertices=tuple(v_specs))
    return MappedTask(task=t, normal_mccts=ns, critical_mccts=cs, S_N=sum(c.delta for c in ns), S_O=sum(c.delta for c in cs))


def build_mapped_task_from_project_task(task: Any, mapped: Dict[str, Any]) -> MappedTask:
    """Adapter for this repository's task schema (`task_set.MCTask`).

    Required task fields:
    - id, cri, pLO (or dLO), dLO, D_vir
    - internal_dag.nodes where each node has:
      node_id, eLO, eHI, predecessors, successors

    Required mapped fields (from `SFMC.map_task`):
    - normal_mccts / critical_mccts with `delta`
    """
    if not hasattr(task, "internal_dag") or task.internal_dag is None:
        raise SimulationError("project task missing internal_dag")
    if not hasattr(task, "D_vir"):
        raise SimulationError("project task missing D_vir for virtual deadline")

    crit = "HI" if int(getattr(task, "cri", 1)) == 0 else "LO"
    period = float(getattr(task, "pLO", getattr(task, "dLO")))
    deadline = float(getattr(task, "dLO"))
    virtual_deadline = float(getattr(task, "D_vir"))
    task_id = str(getattr(task, "id"))

    vertices: List[VertexSpec] = []
    nodes = task.internal_dag.nodes
    for node_id in sorted(nodes.keys()):
        n = nodes[node_id]
        wcet_n = float(getattr(n, "eLO", 0.0))
        wcet_o_raw = float(getattr(n, "eHI", 0.0))
        wcet_o = wcet_o_raw if crit == "HI" else 0.0
        preds = tuple(str(p) for p in sorted(getattr(n, "predecessors", set())))
        succs = tuple(str(s) for s in sorted(getattr(n, "successors", set())))
        vertices.append(
            VertexSpec(
                vid=str(node_id),
                wcet_n=wcet_n,
                wcet_o=wcet_o,
                predecessors=preds,
                successors=succs,
            )
        )

    ns_list = list(mapped.get("normal_mccts", []))
    cs_list = list(mapped.get("critical_mccts", []))
    normal_mccts = tuple(
        MCCTTemplate(
            cid=str(c.get("cid", f"{task_id}_NS_{i}")),
            delta=float(c["delta"]),
            state="NS",
        )
        for i, c in enumerate(ns_list)
    )
    critical_mccts = tuple(
        MCCTTemplate(
            cid=str(c.get("cid", f"{task_id}_CS_{i}")),
            delta=float(c["delta"]),
            state="CS",
        )
        for i, c in enumerate(cs_list)
    )
    spec = TaskSpec(
        task_id=task_id,
        crit=crit,
        period=period,
        deadline=deadline,
        virtual_deadline=virtual_deadline,
        vertices=tuple(vertices),
    )
    return MappedTask(
        task=spec,
        normal_mccts=normal_mccts,
        critical_mccts=critical_mccts,
        S_N=float(mapped.get("S_N", sum(c.delta for c in normal_mccts))),
        S_O=float(mapped.get("S_O", sum(c.delta for c in critical_mccts))),
    )


def build_runtime_input_from_project_taskset(taskset: Any, mapped_taskset_result: Dict[str, Any]) -> List[MappedTask]:
    """Bridge: convert project taskset + `SFMC.map_taskset` output to runtime inputs."""
    if not hasattr(taskset, "HI") or not hasattr(taskset, "LO"):
        raise SimulationError("taskset must provide HI and LO sets")
    mapped_by_id = {
        str(entry["task_id"]): entry
        for entry in mapped_taskset_result.get("tasks", [])
    }
    out: List[MappedTask] = []
    for task in taskset.HI.union(taskset.LO):
        tid = str(getattr(task, "id"))
        if tid not in mapped_by_id:
            raise SimulationError(f"missing mapped result for task {tid}")
        out.append(build_mapped_task_from_project_task(task, mapped_by_id[tid]))
    return out


if __name__ == "__main__":
    mt = make_chain_task(
        task_id="tau_hi",
        crit="HI",
        period=13.0,
        deadline=13.0,
        virtual_deadline=5.0,
        wcets_n=[2.0, 2.0, 2.0],
        wcets_o=[3.0, 6.0, 7.0],
        normal_deltas=[1.0, 0.5],
        critical_deltas=[1.0, 0.5],
    )
    sim = SFMCRuntimeSimulator([mt], m=2, debug=True)
    result = sim.run(horizon=26.0)
    print("schedulable:", result.schedulable)
    print("reason:", result.reason)
    print("finish_time:", result.finish_time)
    print("state_switch_time:", result.state_switch_time)
    print("jobs_released:", result.jobs_released)
    print("jobs_completed:", result.jobs_completed)
