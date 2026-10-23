import type { EngineInterface, Register, Timer } from 'claude-code'

// dopemux-route-ledger (core): records which model each Agent call REQUESTED,
// which model each model step OBSERVED (the API-reported `usage.model`), and
// each advisor server-tool-use, as JSONL receipts under `receiptDir`.
//
// Read-only. No network, no process, no model call, no prompt or command hook,
// and no rewrite, deny or retry of anything: `tool.call`, `agent.spawn` and
// `turn.step` all pass `e` and the result on unchanged. Prompts, file contents
// and tool output never reach a receipt. Every hook body is wrapped so an
// exception cannot surface.
//
// Receipt files. `$.fs.write` replaces a whole file and there is no append, so
// the design is READ-MODIFY-WRITE FROM AN IN-MEMORY SEGMENT LIST: every receipt
// is pushed onto the current segment's array and the whole segment is
// rewritten. All work (rehydrate, record, write) runs on one promise chain so
// writes never overlap, and a flush queued behind several records writes them
// once. A segment rolls to `<sessionId>.<n>.jsonl` at `maxReceiptsPerFile`.
// Nothing on this chain is ever awaited by a `tool.call` or `turn.step` hook.
// A failed write is counted (`receiptsFailed`) and left dirty: the next flush
// rewrites it whole, so there is no retry loop.
//
// No `$.state`: a hot reload re-runs `register` and `session.start`, and the
// tallies are rebuilt from this session's own receipt files there.
//
// The engine's static reader follows `$` only through functions declared at
// the top level, so helpers take `$` and the ledger as arguments.

const SCHEMA_VERSION = 'dopemux.route_ledger.receipt.v1'
const RUNNER = 'claude-code-agent'
const UNKNOWN = 'UNKNOWN'
const STATE_DIR = '.control-tower/state'
const DEFAULT_RECEIPT_DIR = '.control-tower/state/route-ledger'
const DEFAULT_MAX_RECEIPTS = 500
const MIN_MAX_RECEIPTS = 50
const MAX_MAX_RECEIPTS = 5000
const DESCRIPTION_MAX = 80
// `$.fs.write` and `$.fs.read` reject over 4 MiB: roll well before that.
const SEGMENT_BYTES_MAX = 3_500_000
// A burst of receipts redraws the status line once, this long after the first.
const STATUS_DEBOUNCE_MS = 500
const TOAST_MS = 8000
const ROUTE_ROWS_MAX = 60
const SHORT_ID = 8

type Family = 'S' | 'O' | 'H' | 'F' | 'other'
type Effort = string | number

type Config = {
  receiptDir: string
  unpinnedAgent: 'warn' | 'off'
  childAdvisorBudget: number
  sessionAdvisorBudget: number
  maxReceiptsPerFile: number
}

// The shape a supervisor merges into a GEC v2 ExecutionBinding. A receipt is
// NOT a valid binding (that schema has about 23 required keys; the mod knows
// five of them).
type BindingFields = {
  selection: { runner: string; model: string; effort: string }
  effort_requested: string
  effort_observed: string
  response_claimed_model: string
  provider_attested_model: string
  independence_class: string
}

type Usage = {
  input_tokens: number
  output_tokens: number
  cache_read_input_tokens: number
  cache_creation_input_tokens: number
}

type ReceiptCommon = {
  schema_version: string
  seq: number
  session_id: string
  recorded_at: string
  agent_id: string | null
}

type AgentRequestReceipt = ReceiptCommon & {
  kind: 'agent_request'
  tool_use_id: string
  requested_model: string | null
  requested_effort: Effort | null
  subagent_type: string | null
  description: string
  pinned: boolean
  inherits: boolean
  // Joined from `agent.spawn` by tool_use_id; null until (unless) it fires.
  spawned_agent_id: string | null
  resolved_model: string | null
  binding_fields: BindingFields
}

type StepObservedReceipt = ReceiptCommon & {
  kind: 'step_observed'
  turn_id: string
  step_index: number
  requested_model: string | null
  requested_effort: Effort | null
  observed_model: string
  match: boolean | null
  usage: Usage | null
  binding_fields: BindingFields
}

type AdvisorCallReceipt = ReceiptCommon & {
  kind: 'advisor_call'
  advisor_use_id: string
  started_at: number
  ended_at: number | null
  loop: 'main' | 'agent'
}

type Receipt = AgentRequestReceipt | StepObservedReceipt | AdvisorCallReceipt

type Segment = {
  n: number
  path: string
  receipts: Receipt[]
  bytes: number
  dirty: boolean
}

// One Agent the ledger knows of: from its request, its spawn, or its steps.
type AgentRecord = {
  toolUseId: string | null
  agentId: string | null
  requestedModel: string | null
  observedModel: string | null
  // null: no request seen (the agent was only seen stepping).
  pinned: boolean | null
  inherits: boolean
  receipt?: AgentRequestReceipt
}

// One module load's state; W02 extends it in place. Module-local on purpose:
// a reload starts fresh and `session.start` rebuilds it from the receipt files.
type Ledger = {
  config: Config
  sessionId: string | undefined
  fileStem: string | undefined
  isEnded: boolean
  isReady: boolean
  receiptsEnabled: boolean
  receiptsDisabledReason: string | undefined
  // Receipts that could not be recorded: a failed write, or no timestamp.
  receiptsFailed: number
  // Receipt files that exist but could not be read, so were not rewritten.
  segmentsUnreadable: number
  receiptDir: string | undefined
  // The current segment's path.
  receiptFile: string | undefined
  segments: Segment[]
  nextSegmentN: number
  nextSeq: number
  advisorMain: number
  advisorByAgent: Record<string, number>
  advisorSeen: Set<string>
  agents: Record<string, AgentRecord>
  toasted: Set<string>
  // A pending debounced status redraw, if any.
  statusTimer: Timer | undefined
  chain: Promise<void>
  flushQueued: boolean
}

type Summary = {
  agents: { S: number; O: number; H: number; F: number; other: number }
  unpinned: number
  advisorTotal: number
  advisorMain: number
  advisorByAgent: Record<string, number>
  receiptsEnabled: boolean
  receiptsFailed: number
  receiptFile: string | undefined
}

type Settings = Readonly<Record<string, unknown>>

// Facts read from a `tool.call` for Agent, a `turn.step` and an `agent.spawn`
// before anything is queued, so the queued work holds plain values.
type AgentCallFacts = {
  callerAgentId: string | null
  toolUseId: string
  model: string | null
  effort: Effort | null
  subagentType: string | null
  description: string
  at: number
}

type StepFacts = {
  agentId: string | null
  turnId: string
  index: number
  requestedModel: string | null
  requestedEffort: Effort | null
  observedModel: string
  usage: Usage | null
  advisors: { id: string; startedAt: number; endedAt: number | null }[]
  at: number
}

// ------------------------------------------------------------------ pure parts

function integerOr(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isInteger(value) ? value : fallback
}

// A bad value falls back to its default; nothing here throws.
export function parseConfig(options: Settings): Config {
  const dir = typeof options.receiptDir === 'string' ? options.receiptDir.trim() : ''
  const cap = integerOr(options.maxReceiptsPerFile, DEFAULT_MAX_RECEIPTS)
  return {
    receiptDir: dir === '' ? DEFAULT_RECEIPT_DIR : dir,
    unpinnedAgent: options.unpinnedAgent === 'off' ? 'off' : 'warn',
    childAdvisorBudget: integerOr(options.childAdvisorBudget, 0),
    sessionAdvisorBudget: integerOr(options.sessionAdvisorBudget, -1),
    maxReceiptsPerFile: Math.min(MAX_MAX_RECEIPTS, Math.max(MIN_MAX_RECEIPTS, cap)),
  }
}

export function newLedger(options: Settings): Ledger {
  return {
    config: parseConfig(options),
    sessionId: undefined,
    fileStem: undefined,
    isEnded: false,
    isReady: false,
    receiptsEnabled: false,
    receiptsDisabledReason: undefined,
    receiptsFailed: 0,
    segmentsUnreadable: 0,
    receiptDir: undefined,
    receiptFile: undefined,
    segments: [],
    nextSegmentN: 0,
    nextSeq: 0,
    advisorMain: 0,
    advisorByAgent: {},
    advisorSeen: new Set(),
    agents: {},
    toasted: new Set(),
    statusTimer: undefined,
    chain: Promise.resolve(),
    flushQueued: false,
  }
}

// Glyph rule shared with W02: the lower-cased model text decides.
export function familyOf(model: string | null | undefined): Family {
  const text = (typeof model === 'string' ? model : '').toLowerCase()
  if (text.includes('sonnet')) return 'S'
  if (text.includes('opus')) return 'O'
  if (text.includes('haiku')) return 'H'
  if (text.includes('fable')) return 'F'
  return 'other'
}

// What a supervisor merges into an ExecutionBinding. `response_claimed_model`
// is what the API reported in `usage.model`, not provider attestation, and the
// API never reports the effort, so that stays UNKNOWN.
export function toBindingFields(input: {
  requestedModel: string | null | undefined
  requestedEffort: Effort | null | undefined
  observedModel: string | null | undefined
}): BindingFields {
  const model = input.requestedModel ?? UNKNOWN
  const effort = input.requestedEffort === null || input.requestedEffort === undefined
    ? UNKNOWN
    : String(input.requestedEffort)
  return {
    selection: { runner: RUNNER, model, effort },
    effort_requested: effort,
    effort_observed: UNKNOWN,
    response_claimed_model: input.observedModel ?? UNKNOWN,
    provider_attested_model: UNKNOWN,
    independence_class: UNKNOWN,
  }
}

export function summarize(s: Ledger): Summary {
  const agents = { S: 0, O: 0, H: 0, F: 0, other: 0 }
  let unpinned = 0
  // An agent counts once: its first observed model, else its requested alias.
  for (const record of Object.values(s.agents)) {
    agents[familyOf(record.observedModel ?? record.requestedModel)] += 1
    if (record.pinned === false && !record.inherits) unpinned += 1
  }
  let advisorTotal = s.advisorMain
  for (const count of Object.values(s.advisorByAgent)) advisorTotal += count
  return {
    agents,
    unpinned,
    advisorTotal,
    advisorMain: s.advisorMain,
    advisorByAgent: { ...s.advisorByAgent },
    receiptsEnabled: s.receiptsEnabled,
    receiptsFailed: s.receiptsFailed,
    receiptFile: s.receiptFile,
  }
}

function normalizeModel(model: string): string {
  return model.trim().toLowerCase().replace(/-\d{8}$/, '')
}

// null when either side is unknown. A dated id matches its undated request, and
// a bare family alias (`sonnet`) matches any model of that family.
function sameModel(requested: string | null, observed: string): boolean | null {
  if (requested === null || observed === UNKNOWN) return null
  if (normalizeModel(requested) === normalizeModel(observed)) return true
  const alias = requested.trim().toLowerCase()
  if (alias === 'sonnet' || alias === 'opus' || alias === 'haiku' || alias === 'fable') {
    return observed.toLowerCase().includes(alias)
  }
  return false
}

function sanitizeStem(sessionId: string): string {
  return sessionId.replace(/[^A-Za-z0-9_-]/g, '_').slice(0, 120)
}

function hasDotDot(dir: string): boolean {
  return dir.split(/[\\/]+/).includes('..')
}

function text(value: unknown): string | null {
  return typeof value === 'string' && value !== '' ? value : null
}

function count(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function usageOf(usage: unknown): Usage | null {
  if (typeof usage !== 'object' || usage === null) return null
  const u = usage as Record<string, unknown>
  return {
    input_tokens: count(u.input_tokens),
    output_tokens: count(u.output_tokens),
    cache_read_input_tokens: count(u.cache_read_input_tokens),
    cache_creation_input_tokens: count(u.cache_creation_input_tokens),
  }
}

function segmentText(seg: Segment): string {
  return seg.receipts.map(receipt => JSON.stringify(receipt)).join('\n') + '\n'
}

// ------------------------------------------------------------------- the ledger

// Tallies one receipt, whether it was just made or read back from a file.
// Returns false for an advisor call already counted (dedup by server-tool-use id).
function tally(s: Ledger, receipt: Receipt): boolean {
  if (receipt.seq + 1 > s.nextSeq) s.nextSeq = receipt.seq + 1

  if (receipt.kind === 'agent_request') {
    const key = receipt.spawned_agent_id ?? `tool:${receipt.tool_use_id}`
    const earlier = s.agents[key]
    s.agents[key] = {
      toolUseId: receipt.tool_use_id,
      agentId: receipt.spawned_agent_id,
      requestedModel: receipt.requested_model,
      observedModel: earlier?.observedModel ?? null,
      pinned: receipt.pinned,
      inherits: receipt.inherits,
      receipt,
    }
  } else if (receipt.kind === 'step_observed') {
    if (receipt.agent_id !== null) {
      const record = s.agents[receipt.agent_id] ?? {
        toolUseId: null,
        agentId: receipt.agent_id,
        requestedModel: null,
        observedModel: null,
        pinned: null,
        inherits: false,
      }
      s.agents[receipt.agent_id] = record
      if (record.observedModel === null && receipt.observed_model !== UNKNOWN) {
        record.observedModel = receipt.observed_model
      }
    }
  } else {
    if (s.advisorSeen.has(receipt.advisor_use_id)) return false
    s.advisorSeen.add(receipt.advisor_use_id)
    if (receipt.loop === 'main' || receipt.agent_id === null) {
      s.advisorMain += 1
    } else {
      s.advisorByAgent[receipt.agent_id] = (s.advisorByAgent[receipt.agent_id] ?? 0) + 1
    }
  }
  return true
}

function shortId(id: string): string {
  return id.slice(0, SHORT_ID)
}

function advisorTotal(s: Ledger): number {
  return summarize(s).advisorTotal
}

// `agents S×4 H×2 · advisor 1`. Pure: the whole status line from the ledger.
function statusText(s: Ledger): string {
  const sum = summarize(s)
  const order: [string, number][] = [
    ['S', sum.agents.S],
    ['O', sum.agents.O],
    ['H', sum.agents.H],
    ['F', sum.agents.F],
    ['?', sum.agents.other],
  ]
  const present = order.filter(([, n]) => n > 0).map(([glyph, n]) => `${glyph}×${n}`)
  let line = present.length === 0 ? 'agents –' : `agents ${present.join(' ')}`
  if (sum.advisorTotal > 0) {
    const { sessionAdvisorBudget, childAdvisorBudget } = s.config
    const overSession = sessionAdvisorBudget >= 0 && sum.advisorTotal > sessionAdvisorBudget
    const overChild =
      childAdvisorBudget >= 0 && Object.values(sum.advisorByAgent).some(n => n > childAdvisorBudget)
    if (overSession) line += ` · advisor ${sum.advisorTotal}/${sessionAdvisorBudget} ⚠`
    else if (overChild) line += ` · advisor ${sum.advisorTotal}/${childAdvisorBudget} ⚠`
    else line += ` · advisor ${sum.advisorTotal}`
  }
  if (!s.receiptsEnabled) line += ' · ledger off'
  if (s.receiptsFailed > 0) line += ' · receipts ✗'
  return line
}

function drawStatus($: EngineInterface, s: Ledger): void {
  if (s.isEnded) return
  try {
    $.ui.status(statusText(s))
  } catch {
    // a refused status line must not cost anything else
  }
}

// Debounced: the first call arms one timer, calls inside the window ride on it.
function scheduleStatus($: EngineInterface, s: Ledger): void {
  if (s.isEnded || s.statusTimer !== undefined) return
  try {
    s.statusTimer = $.clock.after(STATUS_DEBOUNCE_MS, () => {
      s.statusTimer = undefined
      drawStatus($, s)
    })
  } catch {
    s.statusTimer = undefined
  }
}

function toastOnce($: EngineInterface, s: Ledger, key: string, message: string): void {
  if (s.toasted.has(key)) return
  s.toasted.add(key)
  try {
    $.ui.toast(message, { timeoutMs: TOAST_MS })
  } catch {
    // a refused toast must not cost the receipt
  }
}

// Advisor budgets. The mod counts calls after the fact and cannot block them.
function budgetToasts($: EngineInterface, s: Ledger, receipt: AdvisorCallReceipt): void {
  const { childAdvisorBudget, sessionAdvisorBudget } = s.config
  if (receipt.loop === 'agent' && receipt.agent_id !== null && childAdvisorBudget >= 0) {
    const n = s.advisorByAgent[receipt.agent_id] ?? 0
    if (n > childAdvisorBudget) {
      toastOnce(
        $,
        s,
        `advisor-child:${receipt.agent_id}`,
        `route-ledger: agent ${shortId(receipt.agent_id)} made ${n} advisor calls (budget ${childAdvisorBudget}). The mod counts advisor calls and cannot block them.`,
      )
    }
  }
  if (sessionAdvisorBudget >= 0) {
    const total = advisorTotal(s)
    if (total > sessionAdvisorBudget) {
      toastOnce(
        $,
        s,
        'advisor-session',
        `route-ledger: session made ${total} advisor calls (budget ${sessionAdvisorBudget}). The mod counts advisor calls and cannot block them.`,
      )
    }
  }
}

// Called, wrapped, after every recorded receipt: toasts and the status line.
function afterRecord($: EngineInterface, s: Ledger, receipt: Receipt): void {
  if (receipt.kind === 'advisor_call') budgetToasts($, s, receipt)
  scheduleStatus($, s)
}

// ------------------------------------------------------------------ the command

function cell(value: string | null | undefined): string {
  return value === null || value === undefined || value === '' ? UNKNOWN : String(value)
}

// The last step the main loop observed, from the receipts held in memory.
function lastMainStep(s: Ledger): StepObservedReceipt | undefined {
  for (let i = s.segments.length - 1; i >= 0; i--) {
    const receipts = s.segments[i]!.receipts
    for (let j = receipts.length - 1; j >= 0; j--) {
      const r = receipts[j]!
      if (r.kind === 'step_observed' && r.agent_id === null) return r
    }
  }
  return undefined
}

function matchCell(requested: string | null, observed: string | null): string {
  if (requested === null || observed === null) return UNKNOWN
  const same = sameModel(requested, observed)
  return same === null ? UNKNOWN : same ? 'yes' : 'no'
}

function row(cells: string[]): string {
  return cells.join(' | ')
}

function routeTable(s: Ledger): string {
  const rows: string[] = []
  const main = lastMainStep(s)
  rows.push(
    row([
      'main',
      RUNNER,
      cell(main?.requested_model),
      cell(main?.observed_model),
      cell(main?.requested_effort === null || main === undefined ? null : String(main.requested_effort)),
      matchCell(main?.requested_model ?? null, main?.observed_model ?? null),
      String(s.advisorMain),
    ]),
  )
  const seen = new Set<string>()
  for (const [key, record] of Object.entries(s.agents)) {
    const id = record.agentId ?? record.receipt?.spawned_agent_id ?? null
    if (id !== null) seen.add(id)
    const effort = record.receipt?.requested_effort
    rows.push(
      row([
        id !== null ? shortId(id) : `pending:${shortId(record.toolUseId ?? key)}`,
        RUNNER,
        cell(record.requestedModel),
        cell(record.observedModel),
        effort === null || effort === undefined ? UNKNOWN : String(effort),
        matchCell(record.requestedModel, record.observedModel),
        String(id !== null ? (s.advisorByAgent[id] ?? 0) : 0),
      ]),
    )
  }
  for (const [id, n] of Object.entries(s.advisorByAgent)) {
    if (!seen.has(id) && s.agents[id] === undefined) {
      rows.push(row([shortId(id), RUNNER, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, String(n)]))
    }
  }
  const shown = rows.slice(0, ROUTE_ROWS_MAX)
  const lines = [
    row(['agent', 'runner', 'model requested', 'model observed', 'effort requested', 'match', 'advisor']),
    ...shown,
  ]
  if (rows.length > shown.length) lines.push(`+${rows.length - shown.length} more`)
  lines.push(
    'observed = the API-reported response model (response_claimed, not provider attestation); effort observed is UNKNOWN.',
    'The mod counts advisor calls and cannot block them.',
  )
  return lines.join('\n')
}

function receiptsText(s: Ledger): string {
  const counts = { agent_request: 0, step_observed: 0, advisor_call: 0 }
  for (const seg of s.segments) {
    for (const r of seg.receipts) {
      if (r.kind in counts) counts[r.kind] += 1
    }
  }
  const lines = [
    `receipt file: ${s.receiptFile ?? 'none'}`,
    `receipts: agent_request ${counts.agent_request}, step_observed ${counts.step_observed}, advisor_call ${counts.advisor_call}`,
    `receiptsEnabled ${s.receiptsEnabled}, receiptsFailed ${s.receiptsFailed}`,
  ]
  if (!s.receiptsEnabled && s.receiptsDisabledReason !== undefined) {
    lines.push(`receipts are off: ${s.receiptsDisabledReason}`)
  }
  return lines.join('\n')
}

// `/route-ledger` and its alias `/route`. Reads the ledger, writes nothing.
function routeAnswer(s: Ledger, args: unknown): string {
  const arg = typeof args === 'string' ? args.trim() : ''
  if (arg === '') return routeTable(s)
  if (arg === 'receipts') return receiptsText(s)
  return 'Usage: /route-ledger [receipts]  (no argument: the model table; receipts: the receipt file and counts)'
}

async function registerCommands($: EngineInterface): Promise<void> {
  // Each name on its own: one refusal never stops the other.
  try {
    await $.command
      .register({
        name: 'route-ledger',
        description: 'Show requested versus observed model per agent, and advisor counts.',
        argumentHint: '[receipts]',
      })
      .catch(() => undefined)
  } catch {
    // never surface
  }
  try {
    await $.command
      .register({
        name: 'route',
        description: 'Alias of /route-ledger.',
        argumentHint: '[receipts]',
      })
      .catch(() => undefined)
  } catch {
    // never surface
  }
}

function currentSegment(s: Ledger): Segment {
  const last = s.segments[s.segments.length - 1]
  const isOpen =
    last !== undefined &&
    last.n === s.nextSegmentN - 1 &&
    last.receipts.length < s.config.maxReceiptsPerFile &&
    last.bytes < SEGMENT_BYTES_MAX
  if (last !== undefined && isOpen) return last

  const n = s.nextSegmentN
  s.nextSegmentN += 1
  const name = n === 0 ? `${s.fileStem}.jsonl` : `${s.fileStem}.${n}.jsonl`
  const seg: Segment = { n, path: `${s.receiptDir}/${name}`, receipts: [], bytes: 0, dirty: false }
  s.segments.push(seg)
  return seg
}

// Writes every dirty segment whole. A failure is counted and the segment stays
// dirty, so the next flush rewrites it; nothing loops.
export async function flushSegments($: EngineInterface, s: Ledger): Promise<void> {
  if (!s.receiptsEnabled) return
  for (const seg of s.segments) {
    if (!seg.dirty) continue
    try {
      await $.fs.write(seg.path, segmentText(seg))
      seg.dirty = false
    } catch {
      s.receiptsFailed += 1
    }
  }
}

// All receipt work runs here, one task at a time, so seq order is chain order
// and writes never overlap. A task that throws loses its receipt: counted.
function enqueue(s: Ledger, task: () => Promise<void>): void {
  s.chain = s.chain.then(task).catch(() => {
    s.receiptsFailed += 1
  })
}

function scheduleFlush($: EngineInterface, s: Ledger): void {
  if (s.flushQueued) return
  s.flushQueued = true
  enqueue(s, async () => {
    s.flushQueued = false
    const failedBefore = s.receiptsFailed
    await flushSegments($, s)
    if (s.receiptsFailed !== failedBefore) scheduleStatus($, s)
  })
}

function commit($: EngineInterface, s: Ledger, receipt: Receipt): void {
  const isNew = tally(s, receipt)
  if (isNew && s.receiptsEnabled) {
    const seg = currentSegment(s)
    const line = JSON.stringify(receipt)
    seg.receipts.push(receipt)
    seg.bytes += line.length + 1
    seg.dirty = true
    s.receiptFile = seg.path
    scheduleFlush($, s)
  }
  try {
    afterRecord($, s, receipt)
  } catch {
    // never surface
  }
}

function common(s: Ledger, at: number, agentId: string | null): ReceiptCommon {
  return {
    schema_version: SCHEMA_VERSION,
    seq: s.nextSeq,
    session_id: s.sessionId ?? '',
    recorded_at: new Date(at).toISOString(),
    agent_id: agentId,
  }
}

function disable(s: Ledger, reason: string): void {
  s.receiptsEnabled = false
  s.receiptsDisabledReason = reason
}

// Resolves the session and the receipt directory, and rebuilds the tallies from
// this session's existing segment files. Never throws.
async function initSession($: EngineInterface, s: Ledger): Promise<void> {
  try {
    // Anything still unwritten from this load goes out before the rebuild.
    await flushSegments($, s)

    s.isReady = true
    const sessionId = await $.session.id()
    s.sessionId = sessionId
    const stem = sanitizeStem(sessionId)
    const dir = s.config.receiptDir.replace(/[\\/]+$/, '')
    if (stem === '') return disable(s, 'session id is empty')
    if (hasDotDot(s.config.receiptDir)) return disable(s, 'receiptDir has a .. segment')
    if (dir === '') return disable(s, 'receiptDir is the file system root')
    if (s.config.receiptDir === DEFAULT_RECEIPT_DIR) {
      // The default is never created: it is used only beside existing state.
      const hasState = await $.fs.exists(STATE_DIR).catch(() => false)
      if (!hasState) return disable(s, `${STATE_DIR} does not exist`)
    }

    s.fileStem = stem
    s.receiptDir = dir
    s.receiptsEnabled = true
    s.receiptsDisabledReason = undefined
    s.segments = []
    s.nextSegmentN = 0
    s.nextSeq = 0
    s.advisorMain = 0
    s.advisorByAgent = {}
    s.advisorSeen = new Set()
    s.agents = {}
    s.receiptFile = undefined
    await rehydrate($, s)
  } catch {
    // A failed init never surfaces; receipts stay off and the state says why.
    disable(s, 'receipt setup failed')
  }
}

async function rehydrate($: EngineInterface, s: Ledger): Promise<void> {
  const entries = await $.fs.list(s.receiptDir).catch(() => [])
  const pattern = new RegExp(`^${s.fileStem}(?:\\.(\\d+))?\\.jsonl$`)
  const found: { n: number; name: string }[] = []
  for (const entry of entries) {
    const match = pattern.exec(entry.name)
    if (match !== null) found.push({ n: match[1] === undefined ? 0 : Number(match[1]), name: entry.name })
  }
  found.sort((a, b) => a.n - b.n)

  for (const { n, name } of found) {
    s.nextSegmentN = Math.max(s.nextSegmentN, n + 1)
    const path = `${s.receiptDir}/${name}`
    let body: string
    try {
      body = (await $.fs.read(path)) as string
    } catch {
      // Present but unreadable (missing, over 4 MiB): never rewritten.
      s.segmentsUnreadable += 1
      continue
    }
    const seg: Segment = { n, path, receipts: [], bytes: 0, dirty: false }
    for (const line of body.split('\n')) {
      if (line === '') continue
      try {
        const receipt = JSON.parse(line) as Receipt
        if (receipt?.schema_version !== SCHEMA_VERSION || !Number.isInteger(receipt.seq)) continue
        seg.receipts.push(receipt)
        seg.bytes += line.length + 1
        tally(s, receipt)
      } catch {
        // a damaged line is skipped
      }
    }
    s.segments.push(seg)
    s.receiptFile = path
  }
}

async function ensureReady($: EngineInterface, s: Ledger): Promise<void> {
  if (!s.isReady) await initSession($, s)
}

async function recordAgentRequest($: EngineInterface, s: Ledger, f: AgentCallFacts): Promise<void> {
  await ensureReady($, s)
  const pinned = f.model !== null
  commit($, s, {
    ...common(s, f.at, f.callerAgentId),
    kind: 'agent_request',
    tool_use_id: f.toolUseId,
    requested_model: f.model,
    requested_effort: f.effort,
    subagent_type: f.subagentType,
    description: f.description,
    pinned,
    // A fork ignores the model parameter: it inherits, so it is not unpinned.
    inherits: f.subagentType === 'fork' && !pinned,
    spawned_agent_id: null,
    resolved_model: null,
    binding_fields: toBindingFields({
      requestedModel: f.model,
      requestedEffort: f.effort,
      observedModel: null,
    }),
  })
}

async function recordStep($: EngineInterface, s: Ledger, f: StepFacts): Promise<void> {
  await ensureReady($, s)
  commit($, s, {
    ...common(s, f.at, f.agentId),
    kind: 'step_observed',
    turn_id: f.turnId,
    step_index: f.index,
    requested_model: f.requestedModel,
    requested_effort: f.requestedEffort,
    observed_model: f.observedModel,
    match: sameModel(f.requestedModel, f.observedModel),
    usage: f.usage,
    binding_fields: toBindingFields({
      requestedModel: f.requestedModel,
      requestedEffort: f.requestedEffort,
      observedModel: f.observedModel === UNKNOWN ? null : f.observedModel,
    }),
  })
  for (const advisor of f.advisors) {
    // Deduplicated by the server-tool-use id; never counted twice.
    if (s.advisorSeen.has(advisor.id)) continue
    commit($, s, {
      ...common(s, f.at, f.agentId),
      kind: 'advisor_call',
      advisor_use_id: advisor.id,
      started_at: advisor.startedAt,
      ended_at: advisor.endedAt,
      loop: f.agentId === null ? 'main' : 'agent',
    })
  }
}

// Joins an Agent call to the agent it spawned, by tool_use_id alone.
async function recordSpawn(
  $: EngineInterface,
  s: Ledger,
  toolUseId: string,
  agentId: string,
  model: string | null,
): Promise<void> {
  await ensureReady($, s)
  const record = s.agents[`tool:${toolUseId}`]
  if (record === undefined) return
  delete s.agents[`tool:${toolUseId}`]
  const stepped = s.agents[agentId]
  record.agentId = agentId
  record.observedModel = record.observedModel ?? stepped?.observedModel ?? null
  s.agents[agentId] = record

  const receipt = record.receipt
  if (receipt === undefined) return
  receipt.spawned_agent_id = agentId
  receipt.resolved_model = model
  const seg = s.segments.find(candidate => candidate.receipts.includes(receipt))
  if (seg !== undefined) {
    seg.dirty = true
    scheduleFlush($, s)
  }
}

// ------------------------------------------------------------------- hook work

function noteAgentCall($: EngineInterface, s: Ledger, e: Readonly<Record<string, unknown>>): Promise<void> {
  const facts = readAgentCall(e)
  const isUnpinned = facts.model === null && facts.subagentType !== 'fork'
  if (isUnpinned && s.config.unpinnedAgent === 'warn' && !s.toasted.has(facts.toolUseId)) {
    if (facts.toolUseId !== '') s.toasted.add(facts.toolUseId)
    try {
      $.ui.toast(
        `route-ledger: Agent call "${facts.description}" (${facts.subagentType ?? 'default'}) has no model pinned.`,
      )
    } catch {
      // a refused toast must not cost the receipt
    }
  }
  return stampThen($, s, at => {
    facts.at = at
    enqueue(s, () => recordAgentRequest($, s, facts))
  })
}

function readAgentCall(e: Readonly<Record<string, unknown>>): AgentCallFacts {
  const effort = e.effort
  return {
    callerAgentId: text(e.agentId),
    toolUseId: typeof e.tool_use_id === 'string' ? e.tool_use_id : '',
    model: text(e.model),
    effort: typeof effort === 'string' || typeof effort === 'number' ? effort : null,
    subagentType: text(e.subagent_type),
    description: (typeof e.description === 'string' ? e.description : '').slice(0, DESCRIPTION_MAX),
    at: 0,
  }
}

// The timestamp comes from `$.clock.now()`; without one the receipt is lost and
// counted, and the hook goes on.
async function stampThen($: EngineInterface, s: Ledger, queue: (at: number) => void): Promise<void> {
  let at: number
  try {
    at = await $.clock.now()
  } catch {
    s.receiptsFailed += 1
    return
  }
  queue(at)
}

function noteStep(
  $: EngineInterface,
  s: Ledger,
  e: Readonly<Record<string, unknown>>,
  r: Readonly<Record<string, unknown>> | undefined,
): Promise<void> {
  const usage = (r?.usage ?? null) as Record<string, unknown> | null
  const serverToolUses = Array.isArray(r?.serverToolUses) ? (r?.serverToolUses as unknown[]) : []
  const advisors: StepFacts['advisors'] = []
  for (const use of serverToolUses) {
    const u = use as Record<string, unknown> | null
    if (u?.name !== 'advisor' || typeof u.id !== 'string') continue
    advisors.push({
      id: u.id,
      startedAt: typeof u.startedAt === 'number' ? u.startedAt : 0,
      endedAt: typeof u.endedAt === 'number' ? u.endedAt : null,
    })
  }
  const effort = e.effort
  const facts: StepFacts = {
    agentId: text(e.agentId),
    turnId: typeof e.turnId === 'string' ? e.turnId : '',
    index: typeof e.index === 'number' ? e.index : 0,
    requestedModel: text(e.model),
    requestedEffort: typeof effort === 'string' || typeof effort === 'number' ? effort : null,
    observedModel: text(usage?.model) ?? UNKNOWN,
    usage: usageOf(usage),
    advisors,
    at: 0,
  }
  return stampThen($, s, at => {
    facts.at = at
    enqueue(s, () => recordStep($, s, facts))
  })
}

function noteSpawn(
  $: EngineInterface,
  s: Ledger,
  e: Readonly<Record<string, unknown>>,
  r: Readonly<Record<string, unknown>> | undefined,
): void {
  const toolUseId = text(e.tool_use_id)
  const agentId = text(r?.agentId)
  if (toolUseId === null || agentId === null || r?.deny !== undefined) return
  const model = text(r?.model)
  enqueue(s, () => recordSpawn($, s, toolUseId, agentId, model))
}

export const register: Register = (on, options) => {
  const s = newLedger(options)

  on('session.start', async ($, e, next) => {
    try {
      // Not awaited: the rebuild must not hold the session's start.
      s.isEnded = false
      enqueue(s, () => initSession($, s))
      // After the rehydrate, on the same chain: the status reads rebuilt tallies.
      enqueue(s, async () => drawStatus($, s))
      void registerCommands($)
    } catch {
      // never surface
    }
    return next(e)
  })

  // Observes the requested model; changes nothing and calls `next(e)` once on
  // every path. The receipt work is queued, never awaited, ahead of it.
  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    try {
      if (!s.isEnded) await noteAgentCall($, s, e)
    } catch {
      // never surface
    }
    return next(e)
  })

  // Only joins tool_use_id to the spawned agent id and the resolved model.
  on('agent.spawn', async ($, e, next) => {
    const r = await next(e)
    try {
      if (!s.isEnded) noteSpawn($, s, e, r)
    } catch {
      // never surface
    }
    return r
  })

  // A streaming event: every chunk passes untouched and the result is returned
  // as received. Only the code after `yield*` is wrapped; errors from beneath
  // propagate unchanged.
  on('turn.step', async function* ($, e, next) {
    const r = yield* next(e)
    try {
      if (!s.isEnded) await noteStep($, s, e, r)
    } catch {
      // never surface
    }
    return r
  })

  // One handler for the canonical name and the alias.
  on('command.run', { command: 'route-ledger' }, async (_, e) => {
    try {
      return { text: routeAnswer(s, e.args) }
    } catch {
      return { text: 'route-ledger: could not read the ledger.' }
    }
  })
  on('command.run', { command: 'route' }, async (_, e) => {
    try {
      return { text: routeAnswer(s, e.args) }
    } catch {
      return { text: 'route-ledger: could not read the ledger.' }
    }
  })

  on('session.end', async ($, e, next) => {
    // /clear fires session.end with reason 'clear' but the process goes on and
    // no session.start follows: not an end.
    if (e.reason === 'clear') return next(e)
    try {
      s.isEnded = true
      s.statusTimer?.cancel()
      s.statusTimer = undefined
      $.ui.status(undefined)
      scheduleFlush($, s)
      await s.chain
    } catch {
      // never surface
    }
    return next(e)
  })
}
