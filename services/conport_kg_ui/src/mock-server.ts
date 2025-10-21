/**
 * Mock API Server for Dope Decision Graph UI Development (formerly ConPort KG UI)
 * Simulates Integration Bridge /kg endpoints with fixture data
 *
 * Usage:
 *   npm run mock-server
 *   # Server runs on http://localhost:3016
 */

import http from 'http';
import fixtureData from './fixtures/decisions.json';
import type { DecisionCard, DecisionSummary, Relationship } from './types';

const PORT = 3016;

interface FixtureData {
  decisions: DecisionSummary[];
  relationships: Relationship[];
}

const fixtures = fixtureData as FixtureData;

// Helper: Find decision by ID
function findDecision(id: number): DecisionSummary | undefined {
  return fixtures.decisions.find(d => d.id === id);
}

// Helper: Get related decision IDs (1-hop or 2-hop)
function getRelatedIds(id: number, maxHops: number): Set<number> {
  const related = new Set<number>();
  const queue: Array<{id: number, hop: number}> = [{id, hop: 0}];
  const visited = new Set<number>([id]);

  while (queue.length > 0) {
    const current = queue.shift()!;

    if (current.hop >= maxHops) continue;

    // Find all relationships involving current ID
    fixtures.relationships.forEach(rel => {
      let neighborId: number | null = null;

      if (rel.source_id === current.id) {
        neighborId = rel.target_id;
      } else if (rel.target_id === current.id) {
        neighborId = rel.source_id;
      }

      if (neighborId && !visited.has(neighborId)) {
        visited.add(neighborId);
        related.add(neighborId);
        queue.push({id: neighborId, hop: current.hop + 1});
      }
    });
  }

  return related;
}

// Helper: Get relationships for a decision
function getRelationships(id: number): Relationship[] {
  return fixtures.relationships.filter(
    rel => rel.source_id === id || rel.target_id === id
  ).map(rel => ({
    ...rel,
    direction: rel.source_id === id ? 'outgoing' as const : 'incoming' as const
  }));
}

// Request handler
const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Source-Plane');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url || '', `http://localhost:${PORT}`);
  const path = url.pathname;

  console.log(`[Mock API] ${req.method} ${path}`);

  // GET /kg/decisions/recent?limit=3
  if (path === '/kg/decisions/recent') {
    const limit = parseInt(url.searchParams.get('limit') || '3', 10);
    const recentDecisions = fixtures.decisions.slice(0, limit).map(d => ({
      id: d.id,
      summary: d.summary,
      timestamp: d.timestamp,
      related_count: d.related_count,
      tags: d.tags
    }));

    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({
      decisions: recentDecisions,
      count: recentDecisions.length,
      tier: 1
    }));
    return;
  }

  // GET /kg/decisions/:id/summary
  const summaryMatch = path.match(/^\/kg\/decisions\/(\d+)\/summary$/);
  if (summaryMatch) {
    const id = parseInt(summaryMatch[1], 10);
    const decision = findDecision(id);

    if (!decision) {
      res.writeHead(404, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({error: 'Decision not found'}));
      return;
    }

    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify(decision));
    return;
  }

  // GET /kg/decisions/:id/neighborhood?max_hops=1&limit_per_hop=10
  const neighborhoodMatch = path.match(/^\/kg\/decisions\/(\d+)\/neighborhood$/);
  if (neighborhoodMatch) {
    const id = parseInt(neighborhoodMatch[1], 10);
    const maxHops = parseInt(url.searchParams.get('max_hops') || '1', 10);
    const limitPerHop = parseInt(url.searchParams.get('limit_per_hop') || '10', 10);

    const center = findDecision(id);
    if (!center) {
      res.writeHead(404, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({error: 'Decision not found'}));
      return;
    }

    // Get 1-hop neighbors
    const hop1Ids = getRelatedIds(id, 1);
    const hop1Neighbors = Array.from(hop1Ids)
      .map(nid => findDecision(nid))
      .filter((d): d is DecisionSummary => d !== undefined)
      .slice(0, limitPerHop)
      .map(d => ({
        id: d.id,
        summary: d.summary,
        timestamp: d.timestamp,
        related_count: d.related_count,
        tags: d.tags
      }));

    // Get 2-hop neighbors (if maxHops >= 2)
    let hop2Neighbors: DecisionCard[] = [];
    if (maxHops >= 2) {
      const hop2Ids = getRelatedIds(id, 2);
      // Exclude center and 1-hop neighbors
      hop2Ids.delete(id);
      hop1Ids.forEach(h1 => hop2Ids.delete(h1));

      hop2Neighbors = Array.from(hop2Ids)
        .map(nid => findDecision(nid))
        .filter((d): d is DecisionSummary => d !== undefined)
        .slice(0, limitPerHop)
        .map(d => ({
          id: d.id,
          summary: d.summary,
          timestamp: d.timestamp,
          related_count: d.related_count,
          tags: d.tags
        }));
    }

    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({
      center: {
        id: center.id,
        summary: center.summary,
        timestamp: center.timestamp,
        related_count: center.related_count,
        tags: center.tags
      },
      hop_1_neighbors: hop1Neighbors,
      hop_2_neighbors: hop2Neighbors,
      total_neighbors: hop1Neighbors.length + hop2Neighbors.length,
      is_expanded: maxHops >= 2,
      tier: 2
    }));
    return;
  }

  // GET /kg/decisions/:id/context
  const contextMatch = path.match(/^\/kg\/decisions\/(\d+)\/context$/);
  if (contextMatch) {
    const id = parseInt(contextMatch[1], 10);
    const decision = findDecision(id);

    if (!decision) {
      res.writeHead(404, {'Content-Type': 'application/json'});
      res.end(JSON.stringify({error: 'Decision not found'}));
      return;
    }

    const relationships = getRelationships(id);
    const relatedIds = new Set<number>();
    relationships.forEach(rel => {
      relatedIds.add(rel.source_id === id ? rel.target_id : rel.source_id);
    });

    const relatedDecisions = Array.from(relatedIds)
      .map(rid => findDecision(rid))
      .filter((d): d is DecisionSummary => d !== undefined)
      .map(d => ({
        id: d.id,
        summary: d.summary,
        timestamp: d.timestamp,
        related_count: d.related_count,
        tags: d.tags
      }));

    res.writeHead(200, {'Content-Type': 'application/json'});
    res.end(JSON.stringify({
      decision,
      direct_relationships: relationships,
      related_decisions: relatedDecisions,
      total_related: relatedDecisions.length,
      cognitive_load: decision.cognitive_load,
      tier: 3
    }));
    return;
  }

  // 404 for unknown endpoints
  res.writeHead(404, {'Content-Type': 'application/json'});
  res.end(JSON.stringify({error: 'Endpoint not found'}));
});

server.listen(PORT, () => {
  console.log(`\n🎭 Mock API Server running on http://localhost:${PORT}`);
  console.log(`   Ready to serve Dope Decision Graph UI with fixture data`);
  console.log(`   Press Ctrl+C to stop\n`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n👋 Shutting down mock server...');
  server.close(() => {
    console.log('✅ Server stopped\n');
    process.exit(0);
  });
});
