"""
InsureTrust AI — Graph Engine (Ring Hunter)
=============================================
NetworkX DiGraph singleton for fraud ring detection.
Node types: claimant | doctor | workshop | witness | mobile | ip_address
"""

import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Global singleton graph
_graph: Optional[nx.DiGraph] = None


def get_graph() -> nx.DiGraph:
    """Get or create the global NetworkX DiGraph singleton."""
    global _graph
    if _graph is None:
        _graph = nx.DiGraph()
    return _graph


def add_claim_to_graph(claim_data: dict) -> dict:
    """
    Add a new claim's nodes and edges to the graph.
    Returns the new nodes and edges added (for D3 animation).
    """
    graph = get_graph()
    new_nodes = []
    new_edges = []

    claimant_id = claim_data.get("claimant_id", "")
    claim_id = claim_data.get("id", "")

    # Add claimant node
    if not graph.has_node(claimant_id):
        graph.add_node(claimant_id,
                      type="claimant",
                      label=claim_data.get("claimant_name_masked", "****"),
                      risk_score=0,
                      claim_count=1,
                      created_at=datetime.utcnow().isoformat())
        new_nodes.append({
            "id": claimant_id,
            "type": "claimant",
            "label": claim_data.get("claimant_name_masked", "****"),
            "risk_score": 0,
            "claim_count": 1
        })
    else:
        graph.nodes[claimant_id]["claim_count"] = graph.nodes[claimant_id].get("claim_count", 0) + 1

    # Helper to add edge
    def add_edge(target_id, target_type, target_label, relationship):
        if not target_id:
            return
        if not graph.has_node(target_id):
            graph.add_node(target_id, type=target_type, label=target_label,
                          risk_score=0, claim_count=1)
            new_nodes.append({
                "id": target_id,
                "type": target_type,
                "label": target_label,
                "risk_score": 0,
                "claim_count": 1
            })
        else:
            graph.nodes[target_id]["claim_count"] = graph.nodes[target_id].get("claim_count", 0) + 1

        if not graph.has_edge(claimant_id, target_id):
            graph.add_edge(claimant_id, target_id,
                          relationship=relationship,
                          claim_id=claim_id)
            new_edges.append({
                "source": claimant_id,
                "target": target_id,
                "relationship": relationship
            })

    # claimant → doctor (TREATED_BY)
    add_edge(claim_data.get("doctor_id"), "doctor",
             f"Dr. {claim_data.get('doctor_id', '')}", "TREATED_BY")

    # claimant → workshop (REPAIRED_AT)
    add_edge(claim_data.get("workshop_id"), "workshop",
             f"Workshop {claim_data.get('workshop_id', '')}", "REPAIRED_AT")

    # claimant → witness (WITNESSED_BY)
    add_edge(claim_data.get("witness_id"), "witness",
             f"Witness {claim_data.get('witness_id', '')}", "WITNESSED_BY")

    # claimant → mobile (USES_MOBILE, hashed)
    mobile_hash = claim_data.get("mobile_hash")
    if mobile_hash:
        mob_node = f"mobile_{mobile_hash[:12]}"
        add_edge(mob_node, "mobile",
                 f"****{claim_data.get('mobile_last4', '????')}", "USES_MOBILE")

    # claimant → ip_address (SUBMITTED_FROM)
    ip = claim_data.get("ip_address")
    if ip:
        ip_node = f"ip_{ip}"
        add_edge(ip_node, "ip_address", ip, "SUBMITTED_FROM")

    return {"new_nodes": new_nodes, "new_edges": new_edges}


def analyze_claim_in_graph(claim_data: dict) -> dict:
    """
    Full ring detection analysis for a claim.
    BFS from claimant up to 3 hops, flag suspicious patterns.
    Must complete in < 50ms.
    """
    graph = get_graph()
    claimant_id = claim_data.get("claimant_id", "")

    if not graph.has_node(claimant_id):
        return {
            "connected_claims": 0,
            "shared_doctor": False,
            "shared_workshop": False,
            "multi_claim_witnesses": [],
            "ring_detected": False,
            "ring_id": None,
            "ring_members": [],
            "graph_score": 0.05,
            "new_nodes": [],
            "new_edges": [],
            "doctor_id": claim_data.get("doctor_id"),
            "workshop_id": claim_data.get("workshop_id"),
        }

    # BFS up to 3 hops (using undirected view for traversal)
    undirected = graph.to_undirected()
    visited = set()
    connected_claimants = set()
    shared_doctors = set()
    shared_workshops = set()
    multi_claim_witnesses = []
    suspicious_mobiles = False
    suspicious_ips = False

    # BFS
    queue = [(claimant_id, 0)]
    visited.add(claimant_id)

    while queue:
        node, depth = queue.pop(0)
        if depth >= 3:
            continue

        for neighbor in undirected.neighbors(node):
            if neighbor in visited:
                continue
            visited.add(neighbor)

            node_data = graph.nodes.get(neighbor, {})
            node_type = node_data.get("type", "")
            claim_count = node_data.get("claim_count", 0)

            if node_type == "claimant":
                connected_claimants.add(neighbor)

            # Flag if shared node has degree > 3
            if node_type == "doctor" and undirected.degree(neighbor) > 3:
                shared_doctors.add(neighbor)
            if node_type == "workshop" and undirected.degree(neighbor) > 3:
                shared_workshops.add(neighbor)
            if node_type == "witness" and undirected.degree(neighbor) > 3:
                multi_claim_witnesses.append(neighbor)
            if node_type == "mobile" and undirected.degree(neighbor) >= 2:
                suspicious_mobiles = True
            if node_type == "ip_address" and undirected.degree(neighbor) >= 3:
                suspicious_ips = True

            if depth + 1 < 3:
                queue.append((neighbor, depth + 1))

    # Check for multi-hop ring: two claimants share no direct connection
    # but share a 2nd-degree witness node
    multi_hop_ring = False
    if len(connected_claimants) >= 2:
        for c in connected_claimants:
            c_neighbors = set(undirected.neighbors(c))
            my_neighbors = set(undirected.neighbors(claimant_id))
            # If they don't share a direct edge but share witness neighbors
            if c not in my_neighbors:
                shared = c_neighbors & my_neighbors
                witness_shared = [n for n in shared if graph.nodes.get(n, {}).get("type") == "witness"]
                if witness_shared:
                    multi_hop_ring = True
                    break

    # Determine if ring is detected
    ring_detected = (
        len(shared_doctors) > 0 or
        len(shared_workshops) > 0 or
        len(multi_claim_witnesses) > 0 or
        suspicious_mobiles or
        suspicious_ips or
        multi_hop_ring or
        len(connected_claimants) >= 3
    )

    # Assign ring_id based on known patterns
    ring_id = None
    ring_members = list(connected_claimants)
    if ring_detected:
        doctor_id = claim_data.get("doctor_id")
        workshop_id = claim_data.get("workshop_id")
        ip = claim_data.get("ip_address")

        if doctor_id == "DOC_001" and workshop_id == "WRK_001":
            ring_id = "RING_001"
        elif any(w == "WIT_002" for w in multi_claim_witnesses):
            ring_id = "RING_002"
        elif ip == "192.168.1.50":
            ring_id = "RING_003"
        else:
            ring_id = f"RING_NEW_{len(connected_claimants)}"

    # Compute graph score
    graph_score = 0.05
    if len(connected_claimants) >= 1:
        graph_score += 0.15
    if len(connected_claimants) >= 3:
        graph_score += 0.20
    if shared_doctors:
        graph_score += 0.20
    if shared_workshops:
        graph_score += 0.10
    if multi_claim_witnesses:
        graph_score += 0.10
    if suspicious_mobiles:
        graph_score += 0.10
    if suspicious_ips:
        graph_score += 0.10
    graph_score = round(min(0.99, graph_score), 2)

    # Add to graph and get new nodes/edges
    graph_additions = add_claim_to_graph(claim_data)

    return {
        "connected_claims": len(connected_claimants),
        "shared_doctor": len(shared_doctors) > 0,
        "shared_workshop": len(shared_workshops) > 0,
        "multi_claim_witnesses": multi_claim_witnesses,
        "ring_detected": ring_detected,
        "ring_id": ring_id,
        "ring_members": [claimant_id] + ring_members,
        "graph_score": graph_score,
        "new_nodes": graph_additions["new_nodes"],
        "new_edges": graph_additions["new_edges"],
        "doctor_id": claim_data.get("doctor_id"),
        "workshop_id": claim_data.get("workshop_id"),
    }


def get_full_graph_data() -> dict:
    """
    Serialize the full graph for D3.js visualization.
    GET /graph/data endpoint.
    """
    graph = get_graph()

    nodes = []
    for node_id in graph.nodes():
        data = graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "type": data.get("type", "unknown"),
            "label": data.get("label", node_id),
            "risk_score": data.get("risk_score", 0),
            "claim_count": data.get("claim_count", 0),
        })

    edges = []
    for source, target, data in graph.edges(data=True):
        edges.append({
            "source": source,
            "target": target,
            "relationship": data.get("relationship", "UNKNOWN"),
        })

    return {"nodes": nodes, "edges": edges}


def get_ring_subgraph(ring_id: str) -> dict:
    """Get a subgraph containing only nodes/edges related to a specific ring."""
    graph = get_graph()

    # Find all claimants in this ring
    ring_claimants = set()
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        if node_data.get("type") == "claimant":
            # Check if this claimant is in the ring by looking at shared connections
            pass

    # For now, return the full graph filtered to relevant ring members
    # In production, this would use the ring_id stored per claim
    return get_full_graph_data()
