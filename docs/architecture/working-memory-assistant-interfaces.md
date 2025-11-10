# Working Memory Assistant - Component Interfaces

**Version**: 1.0.0
**Date**: November 9, 2025

## Overview

This document defines the interfaces and APIs for the Working Memory Assistant components, enabling clear implementation contracts and testable integration points.

## Core Interfaces

### 1. SnapshotEngine Interface

```typescript
interface SnapshotEngine {
  // Core snapshot operations
  captureSnapshot(trigger: SnapshotTrigger): Promise<SnapshotResult>;
  getLatestSnapshot(sessionId: string): Promise<DevelopmentSnapshot | null>;
  getSnapshotHistory(sessionId: string, limit?: number): Promise<DevelopmentSnapshot[]>;

  // Trigger management
  registerTrigger(trigger: SnapshotTrigger): void;
  unregisterTrigger(triggerId: string): void;
  getActiveTriggers(): SnapshotTrigger[];

  // Performance monitoring
  getPerformanceMetrics(): SnapshotPerformanceMetrics;
}

interface SnapshotTrigger {
  id: string;
  type: 'file_operation' | 'command_execution' | 'adhd_event' | 'time_based' | 'manual';
  conditions: TriggerCondition[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  debounceMs?: number;
}

interface TriggerCondition {
  type: 'file_changed' | 'energy_dropped' | 'attention_shifted' | 'time_elapsed';
  threshold?: number;
  pattern?: string;
}

interface SnapshotResult {
  snapshotId: string;
  captureTimeMs: number;
  dataSizeBytes: number;
  compressionRatio: number;
  success: boolean;
  error?: string;
}

interface SnapshotPerformanceMetrics {
  averageCaptureTimeMs: number;
  averageCompressionRatio: number;
  totalSnapshotsCaptured: number;
  cacheHitRate: number;
  errorRate: number;
}
```

### 2. RecoveryEngine Interface

```typescript
interface RecoveryEngine {
  // Core recovery operations
  initiateRecovery(snapshotId: string): Promise<RecoverySession>;
  cancelRecovery(sessionId: string): Promise<void>;
  getRecoveryStatus(sessionId: string): Promise<RecoveryStatus>;

  // Progressive disclosure
  getEssentialContext(snapshotId: string): Promise<EssentialContext>;
  getWorkContext(snapshotId: string): Promise<WorkContext>;
  getFullContext(snapshotId: string): Promise<FullContext>;

  // Validation and feedback
  validateRecovery(snapshotId: string, userFeedback: RecoveryFeedback): Promise<ValidationResult>;
  getRecoveryAnalytics(): RecoveryAnalytics;
}

interface RecoverySession {
  sessionId: string;
  snapshotId: string;
  startTime: Date;
  estimatedCompletionTime: Date;
  currentPhase: 'initializing' | 'retrieving' | 'restoring' | 'rendering' | 'complete';
  progress: number; // 0.0-1.0
}

interface RecoveryStatus {
  sessionId: string;
  phase: string;
  progress: number;
  estimatedTimeRemainingMs: number;
  errors: string[];
  warnings: string[];
}

interface EssentialContext {
  currentFile: FileContext;
  nextAction: string;
  criticalReminders: string[];
  recoveryTimeMs: number;
}

interface WorkContext extends EssentialContext {
  recentDecisions: Decision[];
  openFiles: FileContext[];
  tmuxState: TmuxContext;
  thoughtProcess: string;
}

interface FullContext extends WorkContext {
  sessionHistory: SessionEvent[];
  adhdState: ADHDState;
  detailedGuidance: RecoveryGuidance;
}

interface RecoveryFeedback {
  accuracy: number; // 0.0-1.0
  usefulness: number; // 0.0-1.0
  missingElements: string[];
  suggestions: string[];
}

interface ValidationResult {
  accepted: boolean;
  improvements: string[];
  nextSnapshotRecommendations: string[];
}

interface RecoveryAnalytics {
  averageRecoveryTimeMs: number;
  successRate: number;
  userSatisfactionScore: number;
  commonMissingElements: string[];
  performanceByTriggerType: Record<string, number>;
}
```

### 3. MemoryManager Interface

```typescript
interface MemoryManager {
  // Storage operations
  storeSnapshot(snapshot: DevelopmentSnapshot): Promise<StorageResult>;
  retrieveSnapshot(snapshotId: string): Promise<DevelopmentSnapshot>;
  deleteSnapshot(snapshotId: string): Promise<void>;

  // Optimization operations
  compressSnapshot(snapshot: DevelopmentSnapshot): Promise<CompressedSnapshot>;
  decompressSnapshot(compressed: CompressedSnapshot): Promise<DevelopmentSnapshot>;
  optimizeStorage(): Promise<OptimizationResult>;

  // Query operations
  findSnapshots(query: SnapshotQuery): Promise<DevelopmentSnapshot[]>;
  getStorageStats(): Promise<StorageStats>;

  // Maintenance operations
  cleanupOldSnapshots(retentionDays: number): Promise<CleanupResult>;
  defragmentStorage(): Promise<DefragmentResult>;
}

interface StorageResult {
  snapshotId: string;
  storagePath: string;
  sizeBytes: number;
  compressionRatio: number;
  storageTimeMs: number;
  success: boolean;
}

interface CompressedSnapshot {
  id: string;
  data: Uint8Array;
  originalSize: number;
  compressedSize: number;
  compressionAlgorithm: 'lz4' | 'zstd';
  checksum: string;
}

interface SnapshotQuery {
  sessionId?: string;
  dateRange?: { start: Date; end: Date };
  triggerType?: string;
  minComplexity?: number;
  maxComplexity?: number;
  tags?: string[];
}

interface StorageStats {
  totalSnapshots: number;
  totalSizeBytes: number;
  averageSnapshotSize: number;
  compressionRatio: number;
  storageEfficiency: number;
  oldestSnapshot: Date;
  newestSnapshot: Date;
}

interface OptimizationResult {
  snapshotsOptimized: number;
  spaceSavedBytes: number;
  timeSpentMs: number;
  compressionImproved: boolean;
}

interface CleanupResult {
  snapshotsDeleted: number;
  spaceFreedBytes: number;
  errors: string[];
}

interface DefragmentResult {
  fragmentsConsolidated: number;
  performanceImproved: number; // percentage
  timeSpentMs: number;
}
```

## Integration Interfaces

### 4. ADHD Engine Integration

```typescript
interface ADHDEngineIntegration {
  // State monitoring
  getCurrentADHDState(): Promise<ADHDState>;
  subscribeToStateChanges(callback: (oldState: ADHDState, newState: ADHDState) => void): string;
  unsubscribeFromStateChanges(subscriptionId: string): void;

  // Energy management
  getEnergyLevel(): Promise<number>;
  predictEnergyDropTime(): Promise<Date | null>;
  getEnergyPattern(): Promise<EnergyPattern>;

  // Attention management
  getAttentionState(): Promise<AttentionState>;
  getAttentionSpanRemaining(): Promise<number>; // minutes
  predictAttentionShift(): Promise<Date | null>;

  // Cognitive load
  getCognitiveLoad(): Promise<number>;
  getLoadTrend(): Promise<CognitiveLoadTrend>;

  // Break management
  shouldTakeBreak(): Promise<boolean>;
  getRecommendedBreakDuration(): Promise<number>; // minutes
  scheduleBreakReminder(when: Date, duration: number): Promise<string>;
}

interface ADHDState {
  energyLevel: number; // 0.0-1.0
  attentionState: 'focused' | 'scattered' | 'transitioning';
  cognitiveLoad: number; // 0.0-1.0
  sessionDuration: number; // minutes
  breakRecommended: boolean;
  fatigueLevel: number; // 0.0-1.0
}

interface EnergyPattern {
  currentLevel: number;
  trend: 'increasing' | 'decreasing' | 'stable';
  peakTimes: Date[];
  lowTimes: Date[];
  averageDaily: number[];
}

interface AttentionState {
  current: 'focused' | 'scattered' | 'transitioning';
  spanRemaining: number; // minutes
  quality: number; // 0.0-1.0
  distractions: string[];
}

interface CognitiveLoadTrend {
  current: number;
  direction: 'increasing' | 'decreasing' | 'stable';
  rateOfChange: number; // per minute
  projectedPeak: Date | null;
}
```

### 5. ConPort Integration

```typescript
interface ConPortIntegration {
  // Decision context
  getRecentDecisions(limit?: number): Promise<Decision[]>;
  getDecisionsByTags(tags: string[]): Promise<Decision[]>;
  searchDecisions(query: string): Promise<Decision[]>;

  // Progress tracking
  getCurrentTasks(): Promise<ProgressEntry[]>;
  getTaskHierarchy(taskId: string): Promise<ProgressEntry[]>;
  updateTaskProgress(taskId: string, status: ProgressStatus): Promise<void>;

  // Pattern recognition
  findRelevantPatterns(context: string): Promise<SystemPattern[]>;
  getPatternsByTags(tags: string[]): Promise<SystemPattern[]>;
  searchPatterns(query: string): Promise<SystemPattern[]>;

  // Knowledge graph
  linkSnapshotToDecision(snapshotId: string, decisionId: string): Promise<void>;
  getLinkedItems(itemId: string, itemType: ConPortItemType): Promise<LinkedItem[]>;
  createSemanticLink(source: ConPortItem, target: ConPortItem, relationship: string): Promise<void>;
}

interface Decision {
  id: string;
  summary: string;
  rationale: string;
  implementationDetails?: string;
  tags: string[];
  timestamp: Date;
  confidence: number;
}

interface ProgressEntry {
  id: string;
  description: string;
  status: ProgressStatus;
  parentId?: string;
  estimatedComplexity: number;
  actualTimeSpent?: number;
  linkedDecisions: string[];
}

type ProgressStatus = 'TODO' | 'IN_PROGRESS' | 'DONE' | 'BLOCKED';

interface SystemPattern {
  id: string;
  name: string;
  description: string;
  tags: string[];
  usage: string;
  adhdBenefit?: string;
}

interface ConPortItem {
  id: string;
  type: ConPortItemType;
  content: any;
}

type ConPortItemType = 'decision' | 'progress_entry' | 'system_pattern' | 'custom_data';

interface LinkedItem {
  item: ConPortItem;
  relationship: string;
  strength: number;
  createdAt: Date;
}
```

### 6. Serena Integration

```typescript
interface SerenaIntegration {
  // Code context
  getCurrentFile(): Promise<FileContext>;
  getCursorPosition(): Promise<CursorPosition>;
  getVisibleRange(): Promise<VisibleRange>;
  getOpenFiles(): Promise<FileContext[]>;

  // Navigation history
  getNavigationHistory(limit?: number): Promise<NavigationEvent[]>;
  getRecentDefinitions(): Promise<Definition[]>;
  getRecentReferences(): Promise<Reference[]>;

  // Code analysis
  analyzeComplexity(filePath: string): Promise<ComplexityAnalysis>;
  getFunctionSignatures(filePath: string): Promise<FunctionSignature[]>;
  getClassHierarchy(filePath: string): Promise<ClassHierarchy>;

  // Project structure
  getProjectStructure(): Promise<ProjectStructure>;
  findFiles(pattern: string): Promise<string[]>;
  getDependencies(filePath: string): Promise<DependencyInfo>;
}

interface FileContext {
  path: string;
  language: string;
  lastModified: Date;
  isModified: boolean;
  size: number;
}

interface CursorPosition {
  line: number;
  column: number;
  offset: number;
}

interface VisibleRange {
  start: { line: number; column: number };
  end: { line: number; column: number };
}

interface NavigationEvent {
  timestamp: Date;
  from: Location;
  to: Location;
  trigger: 'definition' | 'reference' | 'search' | 'manual';
}

interface Location {
  file: string;
  line: number;
  column: number;
}

interface Definition {
  name: string;
  kind: 'function' | 'class' | 'variable' | 'method';
  location: Location;
  signature?: string;
}

interface Reference {
  location: Location;
  context: string; // surrounding code
  type: 'usage' | 'definition' | 'declaration';
}

interface ComplexityAnalysis {
  overall: number; // 0.0-1.0
  breakdown: {
    nesting: number;
    branching: number;
    size: number;
    coupling: number;
  };
  recommendations: string[];
}

interface FunctionSignature {
  name: string;
  parameters: Parameter[];
  returnType?: string;
  location: Location;
  complexity: number;
}

interface Parameter {
  name: string;
  type?: string;
  defaultValue?: string;
}

interface ClassHierarchy {
  className: string;
  superclasses: string[];
  subclasses: string[];
  interfaces: string[];
}

interface ProjectStructure {
  root: string;
  directories: DirectoryInfo[];
  files: FileInfo[];
  languages: Record<string, number>; // language -> file count
}

interface DirectoryInfo {
  path: string;
  fileCount: number;
  subdirectories: string[];
}

interface FileInfo {
  path: string;
  language: string;
  size: number;
  lastModified: Date;
}

interface DependencyInfo {
  imports: string[];
  exports: string[];
  internalDependencies: string[];
  externalDependencies: string[];
}
```

## Data Types

### Core Data Types

```typescript
interface DevelopmentSnapshot {
  id: string;
  sessionId: string;
  timestamp: Date;
  interruptionType: SnapshotTriggerType;

  developmentContext: DevelopmentContext;
  cognitiveContext: CognitiveContext;
  adhdContext: ADHDContext;
  recoveryMetadata: RecoveryMetadata;

  compressedSize: number;
  checksum: string;
}

interface DevelopmentContext {
  currentFile: FileContext;
  openFiles: FileContext[];
  tmuxState: TmuxContext;
  recentCommands: CommandHistory[];
  ideState: IDEState;
}

interface CognitiveContext {
  currentTask: string;
  thoughtProcess: string;
  recentDecisions: Decision[];
  workPattern: WorkPattern;
  cognitiveLoad: number;
}

interface ADHDContext {
  energyLevel: number;
  attentionState: AttentionState;
  sessionDuration: number;
  breakRecommended: boolean;
  fatigueLevel: number;
}

interface RecoveryMetadata {
  nextAction: string;
  criticalContext: string[];
  gentleReminders: string[];
  recoveryHints: RecoveryHint[];
}

interface TmuxContext {
  activePane: string;
  paneLayout: string;
  paneHistory: PaneCommand[];
  sessionName: string;
}

interface CommandHistory {
  command: string;
  timestamp: Date;
  workingDirectory: string;
  exitCode?: number;
  duration?: number;
}

interface IDEState {
  activeView: string;
  sidebarState: 'open' | 'closed';
  terminalState: 'visible' | 'hidden';
  breakpoints: Breakpoint[];
}

interface Breakpoint {
  file: string;
  line: number;
  condition?: string;
  enabled: boolean;
}

interface RecoveryHint {
  type: 'action' | 'context' | 'reminder';
  priority: 'low' | 'medium' | 'high';
  content: string;
  actionRequired: boolean;
}

type SnapshotTriggerType = 'manual' | 'energy_low' | 'attention_shift' | 'periodic' | 'file_operation' | 'command_execution';

type WorkPattern = 'deep_focus' | 'exploration' | 'debugging' | 'refactoring' | 'planning' | 'reviewing';

type AttentionState = 'focused' | 'scattered' | 'transitioning' | 'fatigued';
```

## Error Handling

### Error Types

```typescript
class WorkingMemoryError extends Error {
  constructor(
    message: string,
    public code: WorkingMemoryErrorCode,
    public component: string,
    public recoverable: boolean = true,
    public retryAfterMs?: number
  ) {
    super(message);
  }
}

enum WorkingMemoryErrorCode {
  SNAPSHOT_CAPTURE_FAILED = 'SNAPSHOT_CAPTURE_FAILED',
  SNAPSHOT_STORAGE_FAILED = 'SNAPSHOT_STORAGE_FAILED',
  SNAPSHOT_RETRIEVAL_FAILED = 'SNAPSHOT_RETRIEVAL_FAILED',
  RECOVERY_RESTORATION_FAILED = 'RECOVERY_RESTORATION_FAILED',
  INTEGRATION_CONNECTION_FAILED = 'INTEGRATION_CONNECTION_FAILED',
  PERFORMANCE_DEGRADED = 'PERFORMANCE_DEGRADED',
  MEMORY_LIMIT_EXCEEDED = 'MEMORY_LIMIT_EXCEEDED',
  INVALID_SNAPSHOT_DATA = 'INVALID_SNAPSHOT_DATA'
}

interface ErrorRecoveryStrategy {
  errorCode: WorkingMemoryErrorCode;
  retryAttempts: number;
  backoffStrategy: 'linear' | 'exponential';
  fallbackAction?: () => Promise<void>;
  userNotification: boolean;
}
```

## Performance Contracts

### Latency Requirements

```typescript
interface PerformanceContract {
  component: string;
  operation: string;
  maxLatencyMs: number;
  percentile: number; // 95th, 99th percentile
  measurementWindow: '1m' | '5m' | '15m' | '1h';
}

const PERFORMANCE_CONTRACTS: PerformanceContract[] = [
  {
    component: 'SnapshotEngine',
    operation: 'captureSnapshot',
    maxLatencyMs: 200,
    percentile: 95,
    measurementWindow: '5m'
  },
  {
    component: 'RecoveryEngine',
    operation: 'initiateRecovery',
    maxLatencyMs: 2000,
    percentile: 99,
    measurementWindow: '15m'
  },
  {
    component: 'MemoryManager',
    operation: 'retrieveSnapshot',
    maxLatencyMs: 50,
    percentile: 95,
    measurementWindow: '1m'
  },
  {
    component: 'ADHDEngineIntegration',
    operation: 'getCurrentADHDState',
    maxLatencyMs: 100,
    percentile: 95,
    measurementWindow: '1m'
  }
];
```

### Resource Limits

```typescript
interface ResourceLimits {
  component: string;
  maxMemoryMB: number;
  maxConcurrentOperations: number;
  maxQueueDepth: number;
  cleanupIntervalMs: number;
}

const RESOURCE_LIMITS: ResourceLimits[] = [
  {
    component: 'SnapshotEngine',
    maxMemoryMB: 100,
    maxConcurrentOperations: 5,
    maxQueueDepth: 20,
    cleanupIntervalMs: 300000 // 5 minutes
  },
  {
    component: 'RecoveryEngine',
    maxMemoryMB: 200,
    maxConcurrentOperations: 3,
    maxQueueDepth: 10,
    cleanupIntervalMs: 600000 // 10 minutes
  },
  {
    component: 'MemoryManager',
    maxMemoryMB: 150,
    maxConcurrentOperations: 10,
    maxQueueDepth: 50,
    cleanupIntervalMs: 900000 // 15 minutes
  }
];
```

This interface specification provides clear contracts for implementing and testing the Working Memory Assistant components, ensuring consistent behavior and measurable performance across the system.