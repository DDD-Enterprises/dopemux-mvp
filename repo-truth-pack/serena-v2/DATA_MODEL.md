# DATA_MODEL.md — Serena v2

Analyzed ref: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

## 1. Storage Layer Summary

| Store | Type | Module | Connection | Purpose |
|-------|------|--------|------------|---------|
| PostgreSQL (intelligence) | Durable | `intelligence/database.py` | asyncpg | Code elements, relationships, navigation patterns, learning profiles, strategies |
| PostgreSQL (ConPort) | Durable | `conport_client_unified.py` | `ConPortDBClient` via shared `ConPortClient` | Decisions, progress, custom data, session state |
| Redis | Cache/Ephemeral | `navigation_cache.py` | `redis.asyncio` | LSP results, symbol cache, navigation breadcrumbs, focus state |
| Redis Streams | Event | `eventbus_consumer.py` | Redis streams | Decision cache from dopecon-bridge events |
| In-memory | Ephemeral | `mcp_server.py:421` | Python object | `current_focus_mode` (resets on restart) |
| In-memory LRU | Cache | `pattern_learner.py:26` | `PatternCache` | Pattern cache with TTL |

## 2. PostgreSQL — Intelligence Database

Source: `intelligence/schema.sql` (350 lines, 6 tables)

### 2.1 `code_elements`
Primary entity for code intelligence.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | SERIAL | PK | Auto-incrementing ID |
| `file_path` | TEXT | NOT NULL | Source file path |
| `element_name` | TEXT | NOT NULL | Symbol name |
| `element_type` | VARCHAR(50) | NOT NULL | function, class, variable, method, etc. |
| `language` | VARCHAR(20) | NOT NULL | Programming language |
| `start_line` | INTEGER | NOT NULL | Start line |
| `end_line` | INTEGER | NOT NULL | End line |
| `start_column` | INTEGER | DEFAULT 0 | Start column |
| `end_column` | INTEGER | DEFAULT 0 | End column |
| `complexity_score` | REAL | CHECK 0.0-1.0 | ADHD complexity score |
| `complexity_level` | VARCHAR(20) | DEFAULT 'simple' | simple/moderate/complex/very_complex |
| `cognitive_load_factor` | REAL | DEFAULT 0.0 | ADHD cognitive burden |
| `tree_sitter_metadata` | JSONB | DEFAULT '{}' | AST node details |
| `structural_signature` | TEXT | — | Hash of structural patterns |
| `access_frequency` | INTEGER | DEFAULT 0 | Navigation frequency |
| `last_accessed` | TIMESTAMPTZ | DEFAULT NOW() | Last navigation time |
| `average_session_time` | REAL | DEFAULT 0.0 | Avg time spent |
| `adhd_insights` | JSONB | DEFAULT '[]' | ADHD-specific insights |
| `focus_recommendations` | JSONB | DEFAULT '[]' | Focus suggestions |
| `content_hash` | VARCHAR(64) | — | Change detection hash |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | — |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Auto-updated via trigger |

**Unique constraint**: `(file_path, element_name, start_line, end_line)`

### 2.2 `code_relationships`
Code dependency graph with cognitive load scoring.

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| `id` | SERIAL | PK | — |
| `source_element_id` | INTEGER | FK → code_elements(id) CASCADE | Source element |
| `target_element_id` | INTEGER | FK → code_elements(id) CASCADE | Target element |
| `relationship_type` | VARCHAR(50) | NOT NULL | calls, imports, inherits, defines, uses |
| `strength` | REAL | CHECK 0.0-1.0 | Relationship strength |
| `confidence` | REAL | CHECK 0.0-1.0 | Detection confidence |
| `context_type` | VARCHAR(30) | DEFAULT 'direct' | direct/indirect/conditional/loop |
| `cognitive_load` | REAL | DEFAULT 0.0 | Mental burden |
| `complexity_increase` | REAL | DEFAULT 0.0 | Added complexity |
| `adhd_navigation_difficulty` | VARCHAR(20) | DEFAULT 'easy' | easy/moderate/hard/overwhelming |
| `traversal_frequency` | INTEGER | DEFAULT 0 | Navigation frequency |
| `detection_method` | VARCHAR(50) | — | tree_sitter/lsp/static_analysis/user_behavior |
| `analysis_metadata` | JSONB | DEFAULT '{}' | — |

**Unique constraint**: `(source_element_id, target_element_id, relationship_type)`

### 2.3 `navigation_patterns`
User navigation sequences for adaptive learning.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | SERIAL PK | — |
| `user_session_id` | VARCHAR(100) NOT NULL | User/session identifier |
| `workspace_path` | TEXT NOT NULL | Workspace scope |
| `pattern_sequence` | JSONB NOT NULL | Navigation actions with timestamps |
| `sequence_hash` | VARCHAR(64) | Deduplication hash |
| `pattern_type` | VARCHAR(30) | exploration/debugging/implementation/review |
| `context_switches` | INTEGER | Context switch count |
| `total_duration_ms` | INTEGER | Total pattern time |
| `effectiveness_score` | REAL CHECK 0.0-1.0 | — |
| `completion_status` | VARCHAR(20) | complete/incomplete/abandoned |
| `attention_span_seconds` | INTEGER | Continuous attention time |
| `cognitive_fatigue_score` | REAL | Fatigue level |
| `focus_mode_used` | BOOLEAN | ADHD focus mode active |
| `adhd_accommodations` | JSONB | Accommodations applied |
| `pattern_frequency` | INTEGER | Occurrence count |

### 2.4 `learning_profiles`
Personalized ADHD navigation optimization profiles.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | SERIAL PK | — |
| `user_session_id` | VARCHAR(100) NOT NULL | User identifier |
| `workspace_path` | TEXT NOT NULL | Workspace scope |
| `preferred_complexity_level` | VARCHAR(20) | simple/moderate/complex |
| `optimal_result_limit` | INTEGER DEFAULT 10 | ADHD-optimal results |
| `attention_span_minutes` | INTEGER DEFAULT 25 | Typical focus duration |
| `context_switch_tolerance` | INTEGER DEFAULT 3 | Comfortable switches/session |
| `progressive_disclosure_preference` | BOOLEAN DEFAULT TRUE | — |
| `preferred_navigation_patterns` | JSONB | Effective patterns |
| `avoid_patterns` | JSONB | Fatigue-causing patterns |
| `learning_convergence_score` | REAL | System learning quality |
| `peak_performance_times` | JSONB | Optimal work hours |
| `fatigue_indicators` | JSONB | Learned fatigue patterns |

**Unique constraint**: `(user_session_id, workspace_path)`

### 2.5 `navigation_strategies`
Proven navigation strategies for reuse.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | SERIAL PK | — |
| `strategy_name` | VARCHAR(100) NOT NULL | Strategy identifier |
| `strategy_type` | VARCHAR(30) NOT NULL | exploration/debugging/implementation/refactoring |
| `pattern_template` | JSONB NOT NULL | Adaptable pattern template |
| `success_rate` | REAL CHECK 0.0-1.0 | — |
| `cognitive_load_reduction` | REAL | Cognitive load improvement |
| `attention_preservation_score` | REAL | Attention preservation |
| `applicable_languages` | JSONB | Language applicability |

**Unique constraint**: `(strategy_name, strategy_type)`
**Seeded data**: 3 default strategies inserted (Progressive Function Exploration, Class Hierarchy Simplification, Focused Debugging Path)

### 2.6 `conport_integration_links`
Links between Serena code intelligence and ConPort decisions/patterns.

| Column | Type | Purpose |
|--------|------|---------|
| `id` | SERIAL PK | — |
| `serena_element_id` | INTEGER FK → code_elements(id) CASCADE | Serena element |
| `serena_element_type` | VARCHAR(50) NOT NULL | code_element/relationship/pattern/strategy |
| `conport_workspace` | TEXT NOT NULL | ConPort workspace ID |
| `conport_item_type` | VARCHAR(50) NOT NULL | decision/progress_entry/system_pattern/custom_data |
| `conport_item_id` | TEXT NOT NULL | ConPort item ID |
| `link_type` | VARCHAR(50) NOT NULL | implements_decision/relates_to_pattern/addresses_issue |
| `link_strength` | REAL CHECK 0.0-1.0 | — |
| `automated_confidence` | REAL | Auto-detection confidence |
| `user_confirmed` | BOOLEAN DEFAULT FALSE | User confirmation |

**Unique constraint**: `(serena_element_id, serena_element_type, conport_item_type, conport_item_id, link_type)`

### Database Infrastructure
- **Extensions**: `uuid-ossp`, `btree_gin`
- **Triggers**: `update_updated_at_column()` on all 6 tables
- **Connection**: asyncpg connection pool via `intelligence/database.py`

## 3. PostgreSQL — ConPort Database

Accessed via `conport_client_unified.py` → shared `ConPortClient`.

| Parameter | Value | Source |
|-----------|-------|--------|
| Host | `localhost` | Default in `ConPortDBClient.__init__` |
| Port | `5455` | Default in `ConPortDBClient.__init__` |
| Database | `dopemux_knowledge_graph` | Default in `ConPortDBClient.__init__` |
| User | `dopemux_age` | Default in `ConPortDBClient.__init__` |
| Password | `dopemux_age_dev_password` | Env `CONPORT_DB_PASSWORD` or default |

### ConPort Operations (Serena → ConPort)

**Writes:**
| Operation | Module | ConPort Method | Data Category |
|-----------|--------|----------------|---------------|
| Track untracked work | `mcp_server.py:4279` | `log_progress()` | progress_entry |
| Link work metadata | `mcp_server.py:4286` | `log_custom_data()` | `untracked_work_links` |
| Save metrics snapshot | `mcp_server.py:4193` | `log_custom_data()` | `metrics_history` |
| Save user config | `untracked_work_storage.py` | `log_custom_data()` | `untracked_work_config` |
| Snooze/abandon work | `untracked_work_storage.py` | `log_custom_data()` | `untracked_work_status` |

**Reads:**
| Operation | Module | ConPort Method | Data Category |
|-----------|--------|----------------|---------------|
| Get metric history | `mcp_server.py:4070` | `get_custom_data()` | `metrics_history` |
| Get user config | `untracked_work_storage.py` | `get_custom_data()` | `untracked_work_config` |
| Match untracked work | `conport_matcher.py` | Various | progress_entries, decisions |

### Authority Boundary
- **Serena writes**: progress_entries (from tracked work), custom_data (metrics, config, work status)
- **Serena reads**: decisions, progress_entries, custom_data
- **Serena does NOT write**: decisions, system_patterns (those belong to ConPort/operator)

## 4. Redis — Navigation Cache

Source: `navigation_cache.py` (`NavigationCache`, `NavigationCacheConfig`)

### Configuration
| Parameter | Value | Source |
|-----------|-------|--------|
| URL | `redis://localhost:6379` | `NavigationCacheConfig.redis_url` |
| DB index | `1` | Separate from ConPort cache (db 0) |
| Key prefix | `serena:v2:nav` | `NavigationCacheConfig.key_prefix` |
| Max cache size | `10000` | `NavigationCacheConfig.max_cache_size` |

### TTL Configuration
| Content Type | TTL | Config Field |
|-------------|-----|-------------|
| Default | 300s (5 min) | `default_ttl` |
| Symbols | 600s (10 min) | `symbol_ttl` |
| Definitions | 1800s (30 min) | `definition_ttl` |
| References | 900s (15 min) | `reference_ttl` |
| Fallback results | 180s (3 min) | Hardcoded in `find_symbol_tool` |

### Cached Data Types
| Cache Key Pattern | Data | Used By |
|-------------------|------|---------|
| `find_symbol:{query}:{type}:{max}` | Symbol search results | `find_symbol_tool` |
| Navigation breadcrumbs | Navigation history | `NavigationCache` |
| Focus context | Current focus state | `NavigationCache` |
| Session tracking | Active session info | `NavigationCache` |

### Cache Characteristics
- **Ephemeral**: All data lost on Redis restart
- **Auto-eviction**: Via TTL expiry
- **Health check interval**: 30 seconds
- **Retry on**: `BusyLoadingError`

## 5. Redis Streams — Event Bus

Source: `eventbus_consumer.py` (`EventBusConsumer`, `DecisionCache`)

- Consumes events from dopecon-bridge via Redis streams
- `DecisionCache`: Caches decisions received from event bus
- Ephemeral: Stream data processed and cached in-memory

## 6. In-Memory State

| State | Location | Lifetime | Purpose |
|-------|----------|----------|---------|
| `current_focus_mode` | `mcp_server.py:421` | Server process | Focus state (focused/scattered/transitioning) |
| `lazy_components` | `mcp_server.py:407` | Server process | Component load state tracking |
| `initialization_errors` | `mcp_server.py:417` | Server process | Error tracking for diagnostics |
| `workspace_python_file_count` | `mcp_server.py:424` | Server process | LSP bypass decision cache |
| `PatternCache` | `pattern_learner.py:26` | Server process | LRU cache with TTL for patterns |
| `NavigationCache.navigation_history` | `navigation_cache.py:53` | Server process | Navigation breadcrumbs (also backed to Redis) |

## 7. Cross-Session Persistence Bridge

Source: `intelligence/cross_session_persistence_bridge.py` (850 lines)

- Bidirectional sync between ConPort and intelligence PostgreSQL
- Promotes learning data from ConPort to intelligence DB
- Syncs code element links back to ConPort

## 8. Pattern Recognition Storage

Source: `intelligence/pattern_recognition.py` (1050 lines)

- Stores recognized patterns in `navigation_patterns` table
- Pattern types: `NavigationPatternType` enum
- Deduplication via `sequence_hash`
- Feeds adaptive learning engine

## 9. Effectiveness Tracking Storage

Source: `intelligence/effectiveness_tracker.py` (997 lines)

- Stores effectiveness metrics in intelligence PostgreSQL
- A/B test results stored via `ABTest` dataclass
- Dimensions: `EffectivenessDimension` enum
- Feeds into `effectiveness_evolution_system.py`

## 10. File-Based State

No SQLite or local file-based state was found. All persistence goes through:
1. PostgreSQL (intelligence DB or ConPort)
2. Redis (ephemeral cache)
3. In-memory (process lifetime)
