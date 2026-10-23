import type { EngineInterface, Register, Timer } from 'claude-code'

// dopemux-pulse: a read-only ADHD status line and focus clock.
//
// The only network call is one GET of `<engineUrl>/api/v1/state`. No process,
// no file write, no prompt or tool hook, no model call. Every hook body is
// wrapped so an exception never reaches the person.
//
// The engine's static reader follows `$` only through functions declared at
// the top of this file, so the helpers below take `$` and the session's state
// object as arguments instead of closing over them.

const DEFAULT_ENGINE_URL = 'http://127.0.0.1:3025'
const MINUTE = 60_000
const POLL_MS = MINUTE
const FETCH_TIMEOUT_MS = 2_000
const DEFAULT_FOCUS_MINUTES = 25
const MIN_FOCUS_MINUTES = 5
const MAX_FOCUS_MINUTES = 120
const NUDGE_AFTER_MINUTES = 90

type EngineView =
  | { kind: 'connecting' }
  | { kind: 'ok'; energy: string; attention: string }
  | { kind: 'down'; httpStatus?: number }
  | { kind: 'malformed' }
  | { kind: 'bad-url' }

type FocusBlock = { startedAt: number; minutes: number; timers: Timer[] }

// One module load's state. Module-local on purpose: a reload starts fresh and
// nothing is persisted.
type Pulse = {
  baseUrl: string | undefined
  sessionStartedAt: number | undefined
  isEnded: boolean
  isPolling: boolean
  view: EngineView
  wasUp: boolean | undefined
  pollTimer: Timer | undefined
  focus: FocusBlock | undefined
  continuousSince: number | undefined
  nudgeTimer: Timer | undefined
}

// The engine's own words, shown as given but never trusted: letters, digits,
// space, `_` and `-`, at most 24 of them.
function word(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined
  const clean = value.replace(/[^\p{L}\p{N} _-]/gu, '').trim().slice(0, 24)
  return clean === '' ? undefined : clean
}

// `energy` and `attention` are the engine's current keys; `energy_level` and
// `attention_state` are the aliases a coordinated engine fix adds.
function parseState(text: string): EngineView {
  let body: unknown
  try {
    body = JSON.parse(text)
  } catch {
    return { kind: 'malformed' }
  }
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    return { kind: 'malformed' }
  }
  const state = body as Record<string, unknown>
  const energy = word(state.energy) ?? word(state.energy_level)
  const attention = word(state.attention) ?? word(state.attention_state)
  if (energy === undefined && attention === undefined) return { kind: 'malformed' }
  return { kind: 'ok', energy: energy ?? '?', attention: attention ?? '?' }
}

// Whole minutes only: `/pulse-focus` takes "", "25", " 45 " and nothing else.
function parseMinutes(args: string): number | undefined {
  const trimmed = args.trim()
  if (trimmed === '') return DEFAULT_FOCUS_MINUTES
  if (!/^\d{1,4}$/.test(trimmed)) return undefined
  const minutes = Number(trimmed)
  return minutes >= MIN_FOCUS_MINUTES && minutes <= MAX_FOCUS_MINUTES ? minutes : undefined
}

function engineUrl(option: unknown): string | undefined {
  const raw = option === undefined ? DEFAULT_ENGINE_URL : option
  if (typeof raw !== 'string') return undefined
  const trimmed = raw.trim().replace(/\/+$/, '')
  return /^https?:\/\/[^\s/]+/i.test(trimmed) ? trimmed : undefined
}

async function renderStatus($: EngineInterface, s: Pulse): Promise<void> {
  if (s.isEnded) return
  const now = await $.clock.now()
  const parts: string[] = []

  if (s.focus === undefined) {
    parts.push('🎯 idle')
  } else {
    const elapsed = Math.floor((now - s.focus.startedAt) / MINUTE)
    parts.push(
      elapsed >= s.focus.minutes
        ? `🎯 ${s.focus.minutes}/${s.focus.minutes} done`
        : `🎯 ${elapsed}/${s.focus.minutes}`,
    )
  }

  const view = s.view
  switch (view.kind) {
    case 'ok':
      parts.push(`⚡ ${view.energy}`, `🧠 ${view.attention}`)
      break
    case 'down':
      parts.push(
        view.httpStatus === undefined
          ? '🔌 ADHD engine unreachable'
          : `🔌 ADHD engine unreachable (HTTP ${view.httpStatus})`,
      )
      break
    case 'malformed':
      parts.push('⚠ ADHD engine state malformed')
      break
    case 'bad-url':
      parts.push('⚠ ADHD engine URL is not http(s)')
      break
    case 'connecting':
      parts.push('⏳ ADHD engine: connecting')
      break
  }

  const sessionMinutes =
    s.sessionStartedAt === undefined ? 0 : Math.floor((now - s.sessionStartedAt) / MINUTE)
  parts.push(`⏱ ${sessionMinutes}m`)

  $.ui.status(parts.join(' · '))
}

async function fetchState($: EngineInterface, s: Pulse): Promise<EngineView> {
  if (s.baseUrl === undefined) return { kind: 'bad-url' }
  let timer: Timer | undefined
  try {
    const timeout = new Promise<'timeout'>(resolve => {
      timer = $.clock.after(FETCH_TIMEOUT_MS, () => resolve('timeout'))
    })
    const response = await Promise.race([$.http.fetch(`${s.baseUrl}/api/v1/state`), timeout])
    if (response === 'timeout') return { kind: 'down' }
    if (!response.ok) return { kind: 'down', httpStatus: response.status }
    return parseState(response.text)
  } catch {
    return { kind: 'down' }
  } finally {
    timer?.cancel()
  }
}

async function poll($: EngineInterface, s: Pulse): Promise<void> {
  if (s.isEnded || s.isPolling) return
  s.isPolling = true
  try {
    const next = await fetchState($, s)
    if (s.isEnded) return
    s.view = next

    // Toast on a real transition only; a never-up engine is just the status.
    if (next.kind !== 'bad-url') {
      const isUp = next.kind === 'ok'
      if (s.wasUp === true && !isUp) {
        $.ui.toast(
          next.kind === 'malformed' ? 'ADHD engine state malformed' : 'ADHD engine unreachable',
        )
      } else if (s.wasUp === false && isUp) {
        $.ui.toast('ADHD engine is back')
      }
      s.wasUp = isUp
    }
    await renderStatus($, s)
  } catch {
    // A failed poll must never surface.
  } finally {
    s.isPolling = false
  }
}

function stopFocus(s: Pulse): void {
  for (const timer of s.focus?.timers ?? []) timer.cancel()
  s.focus = undefined
}

function stopContinuous(s: Pulse): void {
  s.nudgeTimer?.cancel()
  s.nudgeTimer = undefined
  s.continuousSince = undefined
}

function redraw($: EngineInterface, s: Pulse): void {
  try {
    $.ui.invalidate('ui.render')
    void renderStatus($, s).catch(() => undefined)
  } catch {
    // never surface
  }
}

export const register: Register = (on, options) => {
  const s: Pulse = {
    baseUrl: engineUrl(options.engineUrl),
    sessionStartedAt: undefined,
    isEnded: false,
    isPolling: false,
    view: { kind: 'connecting' },
    wasUp: undefined,
    pollTimer: undefined,
    focus: undefined,
    continuousSince: undefined,
    nudgeTimer: undefined,
  }

  on('session.start', async ($, e, next) => {
    try {
      s.sessionStartedAt = await $.clock.now()
      await renderStatus($, s)

      // One refused registration must not stop the status line.
      await $.command
        .register({
          name: 'pulse-focus',
          description: 'Start a focus block (5-120 minutes, default 25).',
          argumentHint: '[minutes]',
        })
        .catch(() => undefined)
      await $.command
        .register({ name: 'break', description: 'End the focus block and take a break.' })
        .catch(() => undefined)
      await $.command
        .register({ name: 'done', description: 'Finish the focus block.' })
        .catch(() => undefined)

      // The first poll must not hold the session start; its answer lands in
      // the status line when it arrives.
      void poll($, s)
      s.pollTimer = $.clock.every(POLL_MS, () => {
        void poll($, s)
      })
    } catch {
      // Never surface a failure from setup.
    }
    return next(e)
  })

  on('command.run', { command: 'pulse-focus' }, async ($, e) => {
    try {
      const minutes = parseMinutes(e.args)
      if (minutes === undefined) {
        return {
          text: `Focus minutes must be a whole number from ${MIN_FOCUS_MINUTES}-${MAX_FOCUS_MINUTES} (default ${DEFAULT_FOCUS_MINUTES}). Nothing started.`,
        }
      }

      const now = await $.clock.now()
      const isRestart = s.focus !== undefined
      stopFocus(s)

      const timers: Timer[] = [
        $.clock.after(minutes * MINUTE, () => {
          try {
            $.ui.toast(
              `🎯 Your ${minutes}-minute focus block is up. /break to rest, or /done to finish.`,
              { timeoutMs: 10_000 },
            )
            redraw($, s)
          } catch {
            // never surface
          }
        }),
        // One tick a minute keeps the band and the status line current.
        $.clock.every(MINUTE, () => redraw($, s)),
      ]
      s.focus = { startedAt: now, minutes, timers }

      // Continuous focus runs from the first block after a break (or the
      // session start) until /break or /done; chained blocks do not reset it.
      if (s.continuousSince === undefined) {
        s.continuousSince = now
        s.nudgeTimer = $.clock.after(NUDGE_AFTER_MINUTES * MINUTE, () => {
          try {
            $.ui.toast(
              `You have been focused for ${NUDGE_AFTER_MINUTES} minutes straight. A short break now will help the next stretch. /break when you are ready.`,
              { timeoutMs: 10_000 },
            )
          } catch {
            // never surface
          }
        })
      }

      redraw($, s)
      return {
        text: `${isRestart ? 'Restarted: ' : ''}Focus block started for ${minutes} minutes. /break to rest, /done to finish.`,
      }
    } catch {
      return { text: 'dopemux-pulse: could not start the focus block.' }
    }
  })

  on('command.run', { command: 'break' }, async $ => {
    try {
      stopFocus(s)
      stopContinuous(s)
      redraw($, s)
      return {
        text: 'Break time. Stand up, drink some water, look away from the screen. /pulse-focus when you are ready.',
      }
    } catch {
      return { text: 'dopemux-pulse: could not record the break.' }
    }
  })

  on('command.run', { command: 'done' }, async $ => {
    try {
      if (s.focus === undefined) return { text: 'No focus block is running.' }
      const now = await $.clock.now()
      const elapsed = Math.floor((now - s.focus.startedAt) / MINUTE)
      stopFocus(s)
      stopContinuous(s)
      redraw($, s)
      return { text: `Focus block done after ${elapsed} minutes. Nice work.` }
    } catch {
      return { text: 'dopemux-pulse: could not finish the focus block.' }
    }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    let line: string | undefined
    try {
      if (!e.props.hasSurvey && s.focus !== undefined) {
        const now = await $.clock.now()
        const leftMs = s.focus.minutes * MINUTE - (now - s.focus.startedAt)
        line =
          leftMs > 0
            ? `🎯 Focus: ${Math.ceil(leftMs / MINUTE)} min left of ${s.focus.minutes} · /break · /done`
            : `🎯 Focus block done (+${Math.floor(-leftMs / MINUTE)} min). /break to rest or /done to finish.`
      }
    } catch {
      line = undefined
    }
    if (line === undefined) return next(e)

    try {
      const { Box, Text } = $.ui.resolve(e)
      return (
        <Box>
          <Text dimColor>{line}</Text>
        </Box>
      )
    } catch {
      return next(e)
    }
  })

  on('session.end', async ($, e, next) => {
    // /clear fires session.end with reason 'clear' but the process goes on and
    // no session.start follows, so the poll, status line and focus block must
    // keep running. Every other reason is a real end: cancel everything.
    if (e.reason === 'clear') return next(e)
    try {
      s.isEnded = true
      s.pollTimer?.cancel()
      s.pollTimer = undefined
      stopFocus(s)
      stopContinuous(s)
      $.ui.status(undefined)
    } catch {
      // never surface
    }
    return next(e)
  })
}
