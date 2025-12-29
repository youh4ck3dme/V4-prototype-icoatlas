-- Relationship Graph Migration for V4 Atlas
-- Stores: COMPANY, PERSON, ADDRESS nodes + EXECUTIVE_OF, OWNER_OF, HAS_ADDRESS edges
-- Derived edges (SAME_PERSON_AS, SAME_ADDRESS_AS) are computed at request time

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS graph_nodes (
  node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_type TEXT NOT NULL,              -- COMPANY | PERSON | ADDRESS
  country TEXT,
  label TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  data JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_graph_nodes UNIQUE (key_hash)
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_country ON graph_nodes(country);

CREATE TABLE IF NOT EXISTS graph_edges (
  edge_id BIGSERIAL PRIMARY KEY,
  from_node UUID NOT NULL REFERENCES graph_nodes(node_id) ON DELETE CASCADE,
  to_node UUID NOT NULL REFERENCES graph_nodes(node_id) ON DELETE CASCADE,
  edge_type TEXT NOT NULL,              -- EXECUTIVE_OF | OWNER_OF | HAS_ADDRESS
  weight NUMERIC NOT NULL DEFAULT 1.0,
  valid_from DATE,
  valid_to DATE,
  data JSONB,
  source TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_graph_edges UNIQUE (from_node, to_node, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_from ON graph_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_graph_edges_to ON graph_edges(to_node);
CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(edge_type);
