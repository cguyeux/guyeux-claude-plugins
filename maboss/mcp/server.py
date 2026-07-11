"""
maboss_mcp - an MCP server exposing the MaBoSS Boolean stochastic simulator.

Tools let an agent load a model, run a stochastic simulation, apply mutations and
compare, evaluate a CCT/MCCT assertion (Oscar Dufossez's MaBoSSEvaluator), import
a Boolean model from BioModels, and convert SBML-qual / BoolNet to MaBoSS format.

Requires pyMaBoSS + the compiled MaBoSS engine, so it is meant to run inside the
bundled Docker image (Dockerfile alongside this file), which is FROM the project's
backend image (pyMaBoSS already installed). Transport: stdio.

Tool logic lives in plain `_functions` (unit/smoke-testable without the MCP
protocol); the `@mcp.tool` wrappers take FLAT parameters so the generated schema
is agent-friendly (no nested `params` object).
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("maboss_mcp")

# The bundled sample model ships in the base image at this path.
_SAMPLE_DIR = "/app/app/data/sample_model"
_BIOMODELS = "https://www.ebi.ac.uk/biomodels"


# --------------------------------------------------------------------- helpers
def _write_pair(tmp: str, bnd_text: str, cfg_text: str) -> tuple[str, str]:
    bnd, cfg = os.path.join(tmp, "m.bnd"), os.path.join(tmp, "m.cfg")
    with open(bnd, "w") as fh:
        fh.write(bnd_text)
    with open(cfg, "w") as fh:
        fh.write(cfg_text)
    return bnd, cfg


def _last_node_probs(result, observe: list[str] | None = None) -> dict:
    # get_last_nodes_probtraj OMITS nodes whose P(ON)=0. When the caller asks for
    # specific nodes, project onto them and fill absent ones with 0.0 so an "off"
    # node is reported as 0.0 rather than silently missing.
    row = result.get_last_nodes_probtraj().iloc[-1]
    d = {str(n): round(float(v), 4) for n, v in row.items()}
    if observe:
        return {n: d.get(n, 0.0) for n in observe}
    return d


def _parse_bnd_nodes(bnd_text: str) -> list[str]:
    import re
    return re.findall(r"[Nn]ode\s+([A-Za-z_]\w*)", bnd_text)


# --------------------------------------------------------------------- logic
def _run_simulation(bnd_text: str, cfg_text: str, mutations: list[str],
                    output_nodes: list[str] | None = None,
                    random_istate: bool = False,
                    istate_off: list[str] | None = None,
                    istate_on: list[str] | None = None) -> dict:
    import maboss
    with tempfile.TemporaryDirectory(prefix="mcp_") as tmp:
        bnd, cfg = _write_pair(tmp, bnd_text, cfg_text)
        sim = maboss.load(bnd, cfg)
        # Initial conditions: random 0.5/0.5 for every node when asked, then force
        # specific nodes to start OFF / ON. Applied to `sim` before the copy so the
        # mutated model inherits them.
        if random_istate:
            for n in list(sim.network):
                sim.network.set_istate(n, {0: 0.5, 1: 0.5})
        for n in (istate_off or []):
            if n:
                sim.network.set_istate(n, {0: 1.0, 1: 0.0})
        for n in (istate_on or []):
            if n:
                sim.network.set_istate(n, {0: 0.0, 1: 1.0})
        # get_last_nodes_probtraj only lists nodes ever active; to report a chosen
        # set (e.g. EMT markers, incl. those that stay off) we project onto it.
        observe = [n for n in (output_nodes or []) if n] or None
        baseline = _last_node_probs(sim.run(), observe)
        perturbed = None
        applied = []
        pairs = []
        for m in mutations or []:
            if ":" not in m:
                continue
            node, state = m.split(":", 1)
            pairs.append((node.strip(), "ON" if state.strip().upper() in ("ON", "1") else "OFF"))
        if pairs:
            psim = maboss.copy_and_mutate(sim, [pairs[0][0]], pairs[0][1])
            for node, st in pairs[1:]:
                psim.mutate(node, st)
            perturbed = _last_node_probs(psim.run(), observe)
            applied = [f"{n}:{s}" for n, s in pairs]
    return {"baseline": baseline, "perturbed": perturbed, "mutations": applied,
            "note": "Continuous-time stochastic MaBoSS; seed-reproducible if the .cfg fixes seed_pseudorandom."}


def _attractors(bnd_text: str, cfg_text: str, observe: list[str] | None = None) -> dict:
    import maboss
    import mpbn
    with tempfile.TemporaryDirectory(prefix="mcp_att_") as tmp:
        bnd, cfg = _write_pair(tmp, bnd_text, cfg_text)
        sim = maboss.load(bnd, cfg)
        bn = maboss.to_minibn(sim)  # colomoto minibn (pure Python, no Java)
    m = mpbn.MPBooleanNetwork(bn)
    out = []
    for a in m.attractors():
        active = sorted(k for k, v in a.items() if v == 1)
        oscillating = sorted(k for k, v in a.items() if v == "*")
        entry = {"active": active, "oscillating": oscillating, "n_active": len(active)}
        if observe:
            entry["observed"] = {n: a.get(n) for n in observe}
        out.append(entry)
    return {"n_attractors": len(out), "attractors": out,
            "note": "Most-Permissive attractors (mpbn) from the MaBoSS model. '*' = free/oscillating node. "
                    "Label each attractor by its active-node signature (e.g. epithelial vs mesenchymal)."}


def _query_cct(assertion: str, bnd_text: str, cfg_text: str) -> dict:
    import maboss.temporal_logic as tl
    with tempfile.TemporaryDirectory(prefix="mcp_cct_") as tmp:
        bnd, cfg = _write_pair(tmp, bnd_text, cfg_text)
        res = tl.MaBoSSEvaluator.querying([assertion], sim_cfg=cfg, sim_bnd=bnd)
    if not res:
        return {"assertion": assertion, "result": None,
                "note": "No evaluation returned (grammar error or unknown node)."}
    df = res[0]
    return {"assertion": assertion, "columns": list(df.columns),
            "rows": df.astype(str).to_dict("records")}


def _model_nodes(bnd_text: str) -> dict:
    nodes = _parse_bnd_nodes(bnd_text)
    return {"node_count": len(nodes), "nodes": nodes}


_LOGIC_RE = re.compile(r"^\s*logic\s*=", re.MULTILINE)
_BLOCK_RE = re.compile(r"^[ \t]*[Nn]ode\s+([A-Za-z_]\w*)\s*\{([^}]*)\}", re.MULTILINE)


def _check_model(bnd_text: str) -> dict:
    """
    Detect a DEGENERATE .bnd before wasting a simulation on it.

    A GINsim -> MaBoSS export can silently drop node logic, emitting
    `rate_up = 0; rate_down = $u_X;` with no `logic =` line: the node can never
    turn on and decays to 0 forever. A model where most nodes are frozen has no
    dynamics, and every simulation on it is meaningless (seen for real on the
    MET model, 43/50 nodes frozen).

    Do NOT confuse a frozen node with a free INPUT, whose canonical shape is
    `rate_up = 0; rate_down = 0;` (it simply holds its .cfg istate).
    """
    blocks = _BLOCK_RE.findall(bnd_text or "")
    if not blocks:
        return {"node_count": 0, "degenerate": False, "severity": "ok",
                "note": "No node declarations found."}

    def rate(body, which):
        m = re.search(rf"^\s*{which}\s*=\s*(.+?);", body, re.MULTILINE)
        return m.group(1).strip() if m else None

    def is_zero(e):
        return e is not None and re.fullmatch(r"0(\.0*)?", e) is not None

    with_logic, frozen, inputs = 0, [], []
    for name, body in blocks:
        if _LOGIC_RE.search(body):
            with_logic += 1
        elif is_zero(rate(body, "rate_up")) and is_zero(rate(body, "rate_down")):
            inputs.append(name)
        elif is_zero(rate(body, "rate_up")):
            frozen.append(name)

    n = len(blocks)
    ratio = len(frozen) / n
    degenerate = ratio >= 0.30
    note = "Model looks healthy."
    if degenerate:
        note = (f"DEGENERATE: {ratio:.0%} of nodes lost their logic and are frozen OFF. "
                "Simulations and attractors on this file are meaningless. Re-export from "
                "GINsim (Export -> MaBoSS) or convert the SBML-qual version instead.")
    elif frozen:
        note = f"{len(frozen)} node(s) are frozen OFF; check whether that is intended."
    return {"node_count": n, "with_logic": with_logic, "frozen_off": frozen,
            "input_like": inputs, "degenerate": degenerate,
            "severity": "degenerate" if degenerate else ("warning" if frozen else "ok"),
            "note": note}


def _sample_model() -> dict:
    with open(os.path.join(_SAMPLE_DIR, "cancer_signaling.bnd")) as fh:
        bnd = fh.read()
    with open(os.path.join(_SAMPLE_DIR, "cancer_signaling.cfg")) as fh:
        cfg = fh.read()
    return {"name": "cancer_signaling (bundled sample)", "bnd": bnd, "cfg": cfg,
            "nodes": _parse_bnd_nodes(bnd)}


def _convert_model(source_text: str, kind: str) -> dict:
    import maboss
    suffix = ".bnet" if kind == "bnet" else ".xml"
    with tempfile.TemporaryDirectory(prefix="mcp_conv_") as tmp:
        src = os.path.join(tmp, "in" + suffix)
        with open(src, "w") as fh:
            fh.write(source_text)
        bnd, cfg = os.path.join(tmp, "o.bnd"), os.path.join(tmp, "o.cfg")
        if kind == "bnet":
            maboss.bnet_to_bnd_and_cfg(src, bnd, cfg)
        else:
            maboss.sbml_to_bnd_and_cfg(src, bnd, cfg)
        bnd_text, cfg_text = open(bnd).read(), open(cfg).read()
    return {"kind": kind, "bnd": bnd_text, "cfg": cfg_text, "nodes": _parse_bnd_nodes(bnd_text)}


def _import_biomodels(model_id: str) -> dict:
    def getj(u):
        return json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"Accept": "application/json"}), timeout=40))

    def getb(u):
        return urllib.request.urlopen(urllib.request.Request(u), timeout=40).read()

    mid = model_id.strip()
    files = getj(f"{_BIOMODELS}/model/files/{mid}?format=json")
    entries = (files.get("main") or []) + (files.get("additional") or [])
    names = [e.get("name", "") for e in entries]
    dl = lambda name: f"{_BIOMODELS}/model/download/{mid}?filename={urllib.parse.quote(name)}"
    bnd_name = next((n for n in names if n.lower().endswith(".bnd")), None)
    cfg_name = next((n for n in names if n.lower().endswith(".cfg")), None)
    if bnd_name and cfg_name:
        bnd_text = getb(dl(bnd_name)).decode("utf-8", "replace")
        cfg_text = getb(dl(cfg_name)).decode("utf-8", "replace")
        return {"model_id": mid, "kind": "maboss-native", "bnd": bnd_text, "cfg": cfg_text,
                "nodes": _parse_bnd_nodes(bnd_text)}
    main = files.get("main") or []
    if not main:
        raise ValueError(f"BioModels id '{mid}' has no main model file.")
    main_name = main[0]["name"]
    with tempfile.TemporaryDirectory(prefix="mcp_bm_") as tmp:
        src = os.path.join(tmp, "m.xml")
        with open(src, "wb") as fh:
            fh.write(getb(dl(main_name)))
        conv = _convert_model(open(src).read(), "sbml")
    conv["model_id"] = mid
    return conv


# --------------------------------------------------------------------- tools
_RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


@mcp.tool(name="maboss_sample_model", annotations={"title": "Get the bundled sample model", **_RO})
def maboss_sample_model() -> str:
    """Return the bundled cancer_signaling .bnd/.cfg so an agent can try the other
    tools without supplying a model."""
    return json.dumps(_sample_model(), ensure_ascii=False)


@mcp.tool(name="maboss_model_nodes", annotations={"title": "List model nodes", **_RO})
def maboss_model_nodes(
    bnd: Annotated[str, Field(description="MaBoSS .bnd text.")],
) -> str:
    """Return the node names declared in a .bnd model."""
    return json.dumps(_model_nodes(bnd), ensure_ascii=False)


@mcp.tool(name="maboss_check_model", annotations={"title": "Check a .bnd for lost logic", **_RO})
def maboss_check_model(
    bnd: Annotated[str, Field(description="MaBoSS .bnd text to inspect.")],
) -> str:
    """Check a .bnd for DEGENERACY before simulating it. A broken GINsim export drops
    node logic, freezing most nodes OFF, and every simulation then collapses to the
    same meaningless attractor. ALWAYS run this on a model you did not produce
    yourself, especially before interpreting an attractor count as biology."""
    return json.dumps(_check_model(bnd), ensure_ascii=False)


@mcp.tool(name="maboss_run_simulation", annotations={"title": "Run a MaBoSS simulation", **_RO})
def maboss_run_simulation(
    bnd: Annotated[str, Field(description="MaBoSS .bnd text (node logic).")],
    cfg: Annotated[str, Field(description="MaBoSS .cfg text (rates + istate + sim params).")],
    mutations: Annotated[list[str], Field(description="Forced node states 'NODE:ON'/'NODE:OFF'. Empty = baseline only.")] = [],
    output_nodes: Annotated[list[str], Field(description="Nodes to observe. Empty = only nodes ever active; pass names to also see nodes that stay off (reported 0.0).")] = [],
    random_istate: Annotated[bool, Field(description="Start every node from a random 0.5/0.5 initial state (explore attractors).")] = False,
    istate_off: Annotated[list[str], Field(description="Nodes forced to START off (P(ON)=0), e.g. input signals held at 0.")] = [],
    istate_on: Annotated[list[str], Field(description="Nodes forced to START on (P(ON)=1).")] = [],
) -> str:
    """Run the real MaBoSS engine on a .bnd/.cfg model and return P(node active) at
    steady state, for the baseline and (if mutations are given) the mutated model.
    Initial conditions are controllable (random_istate + istate_off/istate_on)."""
    return json.dumps(_run_simulation(bnd, cfg, mutations, output_nodes,
                                      random_istate, istate_off, istate_on), ensure_ascii=False)


@mcp.tool(name="maboss_attractors", annotations={"title": "Compute the model's attractors", **_RO})
def maboss_attractors(
    bnd: Annotated[str, Field(description="MaBoSS .bnd text.")],
    cfg: Annotated[str, Field(description="MaBoSS .cfg text.")],
    output_nodes: Annotated[list[str], Field(description="Nodes to report per attractor (e.g. phenotype markers). Empty = only active nodes listed.")] = [],
) -> str:
    """Compute the model's attractors (Most-Permissive semantics, via mpbn on the
    MaBoSS model). Each attractor is a stable configuration = a 'state'/phenotype;
    label it by its active-node signature. This is how you find the epithelial /
    hybrid / mesenchymal states that a single MaBoSS run only reports as probabilities."""
    return json.dumps(_attractors(bnd, cfg, [n for n in output_nodes if n] or None), ensure_ascii=False)


@mcp.tool(name="maboss_query_cct", annotations={"title": "Evaluate a CCT assertion", **_RO})
def maboss_query_cct(
    assertion: Annotated[str, Field(description="CCT assertion, e.g. 'Inc(node:EGFR) / [] [ BRAF:OFF ] [ 5% digits:3 ]'.")],
    bnd: Annotated[str, Field(description="MaBoSS .bnd text.")],
    cfg: Annotated[str, Field(description="MaBoSS .cfg text.")],
) -> str:
    """Evaluate a CCT/MCCT assertion with MaBoSSEvaluator.querying (Oscar Dufossez's
    coherency checker). For Inc/Dec it returns master vs mutation probability, the
    difference, and the Increase/Decrease/Stable verdict."""
    return json.dumps(_query_cct(assertion, bnd, cfg), ensure_ascii=False)


@mcp.tool(name="maboss_convert_model", annotations={"title": "Convert SBML-qual / BoolNet to MaBoSS", **_RO})
def maboss_convert_model(
    source: Annotated[str, Field(description="Model source text: SBML-qual XML or a BoolNet .bnet.")],
    kind: Annotated[str, Field(description="'sbml' (SBML-qual) or 'bnet' (BoolNet).")] = "sbml",
) -> str:
    """Convert an SBML-qual or BoolNet model to MaBoSS .bnd/.cfg via pyMaBoSS.
    Non-Boolean / multivalued models raise an error."""
    return json.dumps(_convert_model(source, kind), ensure_ascii=False)


@mcp.tool(name="maboss_import_biomodels",
          annotations={"title": "Import a model from BioModels", **{**_RO, "openWorldHint": True}})
def maboss_import_biomodels(
    model_id: Annotated[str, Field(description="BioModels id, e.g. 'MODEL1611180000'.")],
) -> str:
    """Fetch a Boolean model from BioModels by id and return it as MaBoSS .bnd/.cfg
    (preferring a native pair when the deposit ships one, else converting the SBML)."""
    return json.dumps(_import_biomodels(model_id), ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
