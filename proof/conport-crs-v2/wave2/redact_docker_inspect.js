#!/usr/bin/env node
// Reads Docker inspect JSON only from stdin; emits a fixed safe projection.
const fs = require("fs");

const allowedLabels = new Set([
  "com.docker.compose.project",
  "com.docker.compose.service",
  "com.docker.compose.project.working_dir",
  "dopemux.catalog_service",
  "dopemux.scope",
  "dopemux.transport",
  "dopemux.project_id",
  "dopemux.workspace_id",
  "dopemux.worktree_root",
]);
const allowedEnv = new Set([
  "DOPEMUX_PROJECT_ID",
  "DOPEMUX_WORKSPACE_ID",
  "DOPEMUX_INSTANCE_ID",
  "MCP_SERVER_PORT",
]);
const secretKey = /SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE_KEY|MASTER_KEY|COOKIE|AUTH|CREDENTIAL|DSN|DATABASE_URL|POSTGRES_URL|REDIS_URL|QDRANT_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY/i;

function environment(entries = []) {
  return entries.map((entry) => {
    const separator = entry.indexOf("=");
    const key = separator < 0 ? entry : entry.slice(0, separator);
    const value = separator < 0 ? "" : entry.slice(separator + 1);
    if (secretKey.test(key)) return { key, classification: "SECRET_REDACTED" };
    if (allowedEnv.has(key)) return { key, classification: "ALLOWLISTED", value };
    return { key, classification: "NON_SECRET_VALUE_OMITTED" };
  });
}

function project(item) {
  const labels = Object.fromEntries(Object.entries(item.Config?.Labels || {})
    .filter(([key]) => allowedLabels.has(key)));
  return {
    container_id: item.Id,
    name: (item.Name || "").replace(/^\//, ""),
    image_id: item.Image,
    image_reference: item.Config?.Image || null,
    image_manifest_digest: item.ImageManifestDescriptor?.digest || null,
    state: item.State?.Status || "UNKNOWN",
    health: item.State?.Health?.Status || "UNKNOWN",
    restart_policy: item.HostConfig?.RestartPolicy?.Name || "UNKNOWN",
    network_mode: item.HostConfig?.NetworkMode || "UNKNOWN",
    ports: item.NetworkSettings?.Ports || {},
    mounts: (item.Mounts || []).map(({ Type, Name, Source, Destination, RW }) => ({
      type: Type, name: Name || null, source: Source || null, destination: Destination, read_write: Boolean(RW),
    })),
    compose_and_dopemux_labels: labels,
    environment: environment(item.Config?.Env),
    entrypoint: "REDACTED_NOT_REQUIRED_FOR_FREEZE_DECISION",
    command: "REDACTED_NOT_REQUIRED_FOR_FREEZE_DECISION",
  };
}

const input = JSON.parse(fs.readFileSync(0, "utf8"));
process.stdout.write(`${JSON.stringify((Array.isArray(input) ? input : [input]).map(project), null, 2)}\n`);
