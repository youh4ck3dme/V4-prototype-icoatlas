"""
V4 Relationship Graph Service
Stores COMPANY, PERSON, ADDRESS nodes + edges.
Computes derived edges (SAME_PERSON_AS, SAME_ADDRESS_AS) at request time.
"""
import os
import re
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Set

try:
    import psycopg
    from psycopg.rows import dict_row
    PSYCOPG_VERSION = 3
except ImportError:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2


def _norm(s: str) -> str:
    s = (s or "").strip().upper()
    s = re.sub(r"[\s\u00A0]+", " ", s)
    return s


def _key_safe(s: str) -> str:
    return _norm(s).replace(" ", "_")


def _digits(s: str) -> str:
    return re.sub(r"\D+", "", s or "")


@dataclass
class GraphNode:
    id: str
    type: str
    country: Optional[str]
    label: str
    data: Dict[str, Any]


@dataclass
class GraphEdge:
    from_id: str
    to_id: str
    type: str
    weight: float
    data: Dict[str, Any]


class GraphService:
    """
    Relationship graph:
    - STORE: COMPANY, PERSON, ADDRESS nodes + edges EXECUTIVE_OF, OWNER_OF, HAS_ADDRESS
    - BUILD: request-time derived edges SAME_PERSON_AS, SAME_ADDRESS_AS
    """

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.getenv("DATABASE_URL") or os.getenv("DB_DSN")
        if not self.dsn:
            raise RuntimeError("Missing DATABASE_URL / DB_DSN for GraphService")
        
        if PSYCOPG_VERSION == 3:
            self.conn = psycopg.connect(self.dsn, row_factory=dict_row)
        else:
            self.conn = psycopg2.connect(self.dsn)

    def close(self):
        self.conn.close()

    def _cursor(self):
        if PSYCOPG_VERSION == 3:
            return self.conn.cursor()
        else:
            return self.conn.cursor(cursor_factory=RealDictCursor)

    # ---------- Canonical node keys ----------
    def company_key(self, country: str, atlas_id: str) -> str:
        return f"COMPANY:{country}:{atlas_id}"

    def person_key(self, country: str, full_name: str, birth_date: Optional[str] = None, reg_id: Optional[str] = None) -> str:
        parts = [f"PERSON:{country}", _key_safe(full_name)]
        if birth_date:
            parts.append(str(birth_date))
        if reg_id:
            parts.append(_key_safe(reg_id))
        return ":".join(parts)

    def address_key(self, country: str, street: str, city: str, postal: Optional[str] = None) -> str:
        postal = postal or ""
        return f"ADDRESS:{country}:{_key_safe(street)}:{_key_safe(city)}:{_digits(postal)}"

    # ---------- DB ops ----------
    def get_or_create_node(
        self,
        node_type: str,
        key_hash: str,
        label: str,
        country: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        data = data or {}
        data_json = json.dumps(data) if isinstance(data, dict) else data
        
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO graph_nodes (node_type, country, label, key_hash, data, updated_at)
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (key_hash) DO UPDATE
                  SET label = EXCLUDED.label,
                      data = COALESCE(graph_nodes.data, '{}'::jsonb) || EXCLUDED.data,
                      updated_at = now()
                RETURNING node_id
                """,
                (node_type, country, label, key_hash, data_json),
            )
            node_id = cur.fetchone()["node_id"]
        self.conn.commit()
        return str(node_id)

    def upsert_edge(
        self,
        from_node: str,
        to_node: str,
        edge_type: str,
        weight: float = 1.0,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_to: Optional[str] = None,
    ) -> None:
        data = data or {}
        data_json = json.dumps(data) if isinstance(data, dict) else data
        
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO graph_edges (from_node, to_node, edge_type, weight, valid_from, valid_to, data, source, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (from_node, to_node, edge_type) DO UPDATE
                  SET weight = GREATEST(graph_edges.weight, EXCLUDED.weight),
                      data = COALESCE(graph_edges.data, '{}'::jsonb) || EXCLUDED.data,
                      source = COALESCE(EXCLUDED.source, graph_edges.source),
                      valid_from = COALESCE(graph_edges.valid_from, EXCLUDED.valid_from),
                      valid_to = COALESCE(graph_edges.valid_to, EXCLUDED.valid_to),
                      updated_at = now()
                """,
                (from_node, to_node, edge_type, float(weight), valid_from, valid_to, data_json, source),
            )
        self.conn.commit()

    # ---------- Ingest company relationships ----------
    def _generate_person_key(self, name: str, country: str, extra: str = "") -> str:
        """Generates a stable unique key for a person."""
        raw = f"PERSON|{country}|{name.strip().lower()}|{extra.strip().lower()}"
        import hashlib
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def ingest_company_relationships(
        self,
        atlas_id: str,
        country: str,
        company_label: str,
        address: Optional[Dict[str, Any]] = None,
        executives: Optional[List[Dict[str, Any]]] = None,
        owners: Optional[List[Dict[str, Any]]] = None,
        source: str = "V4",
    ) -> str:
        """
        Create COMPANY node and connect PERSON/ADDRESS nodes.
        Expected:
          address: {street, city, postal_code}
          executives: [{name, role, since, until, birth_date?, reg_id?}]
          owners: [{name, role?, share?, since?, until?, birth_date?, reg_id?}]
        """
        company_node = self.get_or_create_node(
            node_type="COMPANY",
            key_hash=self.company_key(country, atlas_id),
            label=company_label or f"Company {atlas_id}",
            country=country,
            data={"atlas_id": atlas_id, "country": country},
        )

        # Address
        if address:
            street = address.get("street") or ""
            city = address.get("city") or ""
            postal = address.get("postal_code") or address.get("postal") or ""
            if street and city:
                addr_node = self.get_or_create_node(
                    node_type="ADDRESS",
                    key_hash=self.address_key(country, street, city, postal),
                    label=f"{street}, {city}",
                    country=country,
                    data={"street": street, "city": city, "postal_code": postal},
                )
                self.upsert_edge(company_node, addr_node, "HAS_ADDRESS", weight=1.0, data={}, source=source)

        # Executives
        for ex in (executives or []):
            name = ex.get("name") or ""
            if not name:
                continue
            
            # Use the new _generate_person_key for deduplication
            person_key_extra = ex.get("birth_date") or ex.get("reg_id") or ex.get("role") or ""
            person_node = self.get_or_create_node(
                node_type="PERSON",
                key_hash=self._generate_person_key(name, country, person_key_extra),
                label=name,
                country=country,
                data={"name": name, "birth_date": ex.get("birth_date"), "reg_id": ex.get("reg_id")},
            )
            self.upsert_edge(
                from_node=person_node,
                to_node=company_node,
                edge_type="EXECUTIVE_OF",
                weight=3.0,
                data={"role": ex.get("role"), "since": ex.get("since"), "until": ex.get("until")},
                source=source,
            )

        # Owners
        for ow in (owners or []):
            name = ow.get("name") or ""
            if not name:
                continue
            person_node = self.get_or_create_node(
                node_type="PERSON",
                key_hash=self.person_key(country, name, ow.get("birth_date"), ow.get("reg_id")),
                label=name,
                country=country,
                data={"name": name, "birth_date": ow.get("birth_date"), "reg_id": ow.get("reg_id")},
            )
            self.upsert_edge(
                from_node=person_node,
                to_node=company_node,
                edge_type="OWNER_OF",
                weight=5.0,
                data={"share": ow.get("share"), "since": ow.get("since"), "until": ow.get("until")},
                source=source,
            )

        return company_node

    # ---------- Build graph (company + derived related companies) ----------
    def build_company_graph(
        self,
        atlas_id: str,
        country: str,
        depth: int = 2,
        limit_related_per_anchor: int = 25,
        include_raw_nodes: bool = True,
    ) -> Dict[str, Any]:
        """
        Returns:
          nodes: company/person/address (+ related companies)
          edges: stored edges + derived edges SAME_PERSON_AS / SAME_ADDRESS_AS
        """
        start_key = self.company_key(country, atlas_id)

        with self._cursor() as cur:
            cur.execute("SELECT * FROM graph_nodes WHERE key_hash = %s", (start_key,))
            start = cur.fetchone()
            if not start:
                return {"nodes": [], "edges": [], "summary": {"note": "no graph nodes for company yet"}}

        node_map: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []
        derived_edges: List[GraphEdge] = []

        def add_node(row):
            nid = str(row["node_id"])
            if nid not in node_map:
                node_map[nid] = GraphNode(
                    id=nid,
                    type=row["node_type"],
                    country=row.get("country"),
                    label=row["label"],
                    data=row.get("data") or {},
                )

        add_node(start)
        start_id = str(start["node_id"])

        # Pull direct stored edges around company
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT e.*, nf.node_type as from_type, nt.node_type as to_type,
                       nf.label as from_label, nt.label as to_label,
                       nf.country as from_country, nt.country as to_country,
                       nf.data as from_data, nt.data as to_data
                FROM graph_edges e
                JOIN graph_nodes nf ON nf.node_id = e.from_node
                JOIN graph_nodes nt ON nt.node_id = e.to_node
                WHERE e.from_node = %s OR e.to_node = %s
                """,
                (start_id, start_id),
            )
            direct = cur.fetchall()

        person_nodes: Set[str] = set()
        address_nodes: Set[str] = set()

        for r in direct:
            add_node({"node_id": r["from_node"], "node_type": r["from_type"], "country": r["from_country"], "label": r["from_label"], "data": r["from_data"]})
            add_node({"node_id": r["to_node"], "node_type": r["to_type"], "country": r["to_country"], "label": r["to_label"], "data": r["to_data"]})

            e = GraphEdge(
                from_id=str(r["from_node"]),
                to_id=str(r["to_node"]),
                type=r["edge_type"],
                weight=float(r["weight"]),
                data=r.get("data") or {},
            )
            edges.append(e)

            if r["from_type"] == "PERSON" or r["to_type"] == "PERSON":
                pid = str(r["from_node"]) if r["from_type"] == "PERSON" else str(r["to_node"])
                person_nodes.add(pid)
            if r["from_type"] == "ADDRESS" or r["to_type"] == "ADDRESS":
                aid = str(r["from_node"]) if r["from_type"] == "ADDRESS" else str(r["to_node"])
                address_nodes.add(aid)

        # Derived: other companies sharing same PERSON/ADDRESS
        def fetch_companies_for_anchor(anchor_node_id: str) -> List[Dict[str, Any]]:
            with self._cursor() as cur:
                cur.execute(
                    """
                    SELECT e.*, n_other.node_id as other_id, n_other.label as other_label, 
                           n_other.country as other_country, n_other.data as other_data
                    FROM graph_edges e
                    JOIN graph_nodes n_other ON (
                      (e.from_node = %s AND n_other.node_id = e.to_node) OR
                      (e.to_node   = %s AND n_other.node_id = e.from_node)
                    )
                    WHERE (e.from_node = %s OR e.to_node = %s)
                      AND n_other.node_type = 'COMPANY'
                    LIMIT %s
                    """,
                    (anchor_node_id, anchor_node_id, anchor_node_id, anchor_node_id, limit_related_per_anchor),
                )
                return cur.fetchall()

        related_company_ids: Set[str] = set()

        for pid in person_nodes:
            rows = fetch_companies_for_anchor(pid)
            for r in rows:
                other_id = str(r["other_id"])
                if other_id == start_id:
                    continue
                if other_id not in node_map:
                    node_map[other_id] = GraphNode(
                        id=other_id,
                        type="COMPANY",
                        country=r.get("other_country"),
                        label=r.get("other_label"),
                        data=r.get("other_data") or {},
                    )
                related_company_ids.add(other_id)
                derived_edges.append(
                    GraphEdge(
                        from_id=start_id,
                        to_id=other_id,
                        type="SAME_PERSON_AS",
                        weight=2.0,
                        data={"via_person_node": pid},
                    )
                )

        for aid in address_nodes:
            rows = fetch_companies_for_anchor(aid)
            for r in rows:
                other_id = str(r["other_id"])
                if other_id == start_id:
                    continue
                if other_id not in node_map:
                    node_map[other_id] = GraphNode(
                        id=other_id,
                        type="COMPANY",
                        country=r.get("other_country"),
                        label=r.get("other_label"),
                        data=r.get("other_data") or {},
                    )
                related_company_ids.add(other_id)
                derived_edges.append(
                    GraphEdge(
                        from_id=start_id,
                        to_id=other_id,
                        type="SAME_ADDRESS_AS",
                        weight=1.0,
                        data={"via_address_node": aid},
                    )
                )

        out_nodes = [
            {"id": n.id, "type": n.type, "country": n.country, "label": n.label, "data": (n.data if include_raw_nodes else {})}
            for n in node_map.values()
        ]
        out_edges = [
            {"from": e.from_id, "to": e.to_id, "type": e.type, "weight": e.weight, "data": e.data}
            for e in (edges + derived_edges)
        ]

        summary = {
            "persons": len(person_nodes),
            "addresses": len(address_nodes),
            "related_companies": len(related_company_ids),
            "stored_edges": len(edges),
            "derived_edges": len(derived_edges),
        }

        return {"nodes": out_nodes, "edges": out_edges, "summary": summary}
