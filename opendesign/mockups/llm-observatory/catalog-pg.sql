CREATE SCHEMA IF NOT EXISTS fastest_catalog;
REVOKE ALL ON SCHEMA fastest_catalog FROM PUBLIC;

CREATE TABLE IF NOT EXISTS fastest_catalog.snapshot (
  id text PRIMARY KEY,
  document jsonb NOT NULL
);

CREATE TABLE IF NOT EXISTS fastest_catalog.current_snapshot (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  snapshot_id text NOT NULL REFERENCES fastest_catalog.snapshot(id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.seed_document (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  path text,
  sha256 text NOT NULL,
  content text NOT NULL,
  PRIMARY KEY (snapshot_id,path)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.gpu (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  parent_id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id),
  FOREIGN KEY (snapshot_id,parent_id) REFERENCES fastest_catalog.gpu DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS fastest_catalog.vendor_spec (
  snapshot_id text,
  gpu_id text,
  source_url text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,gpu_id),
  FOREIGN KEY (snapshot_id,gpu_id) REFERENCES fastest_catalog.gpu
);

CREATE TABLE IF NOT EXISTS fastest_catalog.machine (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.machine_gpu (
  snapshot_id text,
  machine_id text,
  gpu_id text,
  PRIMARY KEY (snapshot_id,machine_id,gpu_id),
  FOREIGN KEY (snapshot_id,machine_id) REFERENCES fastest_catalog.machine,
  FOREIGN KEY (snapshot_id,gpu_id) REFERENCES fastest_catalog.gpu
);

CREATE TABLE IF NOT EXISTS fastest_catalog.machine_part (
  snapshot_id text,
  machine_id text,
  ordinal integer,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,machine_id,ordinal),
  FOREIGN KEY (snapshot_id,machine_id) REFERENCES fastest_catalog.machine
);

CREATE TABLE IF NOT EXISTS fastest_catalog.topology_media (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.topology_revision (
  snapshot_id text,
  machine_id text,
  revision_id text NOT NULL CHECK (revision_id ~ '^topology-[a-f0-9]{64}$'),
  ordinal integer NOT NULL CHECK (ordinal > 0),
  source_path text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,machine_id,revision_id),
  UNIQUE (snapshot_id,machine_id),
  UNIQUE (snapshot_id,ordinal),
  FOREIGN KEY (snapshot_id,machine_id) REFERENCES fastest_catalog.machine,
  FOREIGN KEY (snapshot_id,source_path) REFERENCES fastest_catalog.seed_document
);

CREATE TABLE IF NOT EXISTS fastest_catalog.topology_node (
  snapshot_id text,
  machine_id text,
  revision_id text,
  slot integer CHECK (slot > 0),
  kind text NOT NULL CHECK (kind IN ('card', 'host')),
  gpu_id text,
  photo_id text,
  document jsonb NOT NULL,
  CHECK (kind <> 'host' OR (gpu_id IS NULL AND photo_id IS NULL)),
  PRIMARY KEY (snapshot_id,machine_id,revision_id,slot),
  FOREIGN KEY (snapshot_id,machine_id,revision_id) REFERENCES fastest_catalog.topology_revision,
  FOREIGN KEY (snapshot_id,gpu_id) REFERENCES fastest_catalog.gpu,
  FOREIGN KEY (snapshot_id,photo_id) REFERENCES fastest_catalog.topology_media
);

CREATE TABLE IF NOT EXISTS fastest_catalog.topology_link (
  snapshot_id text,
  machine_id text,
  revision_id text,
  ordinal integer CHECK (ordinal > 0),
  from_slot integer NOT NULL,
  to_slot integer NOT NULL CHECK (to_slot <> from_slot),
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,machine_id,revision_id,ordinal),
  FOREIGN KEY (snapshot_id,machine_id,revision_id,from_slot) REFERENCES fastest_catalog.topology_node,
  FOREIGN KEY (snapshot_id,machine_id,revision_id,to_slot) REFERENCES fastest_catalog.topology_node
);

CREATE TABLE IF NOT EXISTS fastest_catalog.model_repository (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.model_artifact (
  snapshot_id text,
  repository_id text,
  ordinal integer,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,repository_id,ordinal),
  FOREIGN KEY (snapshot_id,repository_id) REFERENCES fastest_catalog.model_repository
);

CREATE TABLE IF NOT EXISTS fastest_catalog.model_discovery (
  snapshot_id text,
  collection text,
  rank integer,
  repository_id text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,collection,rank),
  UNIQUE (snapshot_id,collection,repository_id),
  FOREIGN KEY (snapshot_id,repository_id) REFERENCES fastest_catalog.model_repository
);

CREATE TABLE IF NOT EXISTS fastest_catalog.runtime (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.topic (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  facet text,
  name text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id, facet, name)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.discovery_source (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  url text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id, url)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.source_video (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.video_inventory_position (
  snapshot_id text,
  position integer,
  source_id text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,position),
  FOREIGN KEY (snapshot_id,source_id) REFERENCES fastest_catalog.source_video
);

CREATE TABLE IF NOT EXISTS fastest_catalog.test_series (
  snapshot_id text,
  id text,
  source_id text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id),
  FOREIGN KEY (snapshot_id,source_id) REFERENCES fastest_catalog.source_video
);

CREATE TABLE IF NOT EXISTS fastest_catalog.research_model (
  snapshot_id text REFERENCES fastest_catalog.snapshot(id),
  id text,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id)
);

CREATE TABLE IF NOT EXISTS fastest_catalog.research_observation (
  snapshot_id text,
  id text,
  series_id text NOT NULL,
  source_id text NOT NULL,
  machine_id text,
  research_model_id text,
  lexical_value text NOT NULL,
  unit text NOT NULL,
  document jsonb NOT NULL,
  PRIMARY KEY (snapshot_id,id),
  FOREIGN KEY (snapshot_id,series_id) REFERENCES fastest_catalog.test_series,
  FOREIGN KEY (snapshot_id,source_id) REFERENCES fastest_catalog.source_video,
  FOREIGN KEY (snapshot_id,machine_id) REFERENCES fastest_catalog.machine,
  FOREIGN KEY (snapshot_id,research_model_id) REFERENCES fastest_catalog.research_model
);
