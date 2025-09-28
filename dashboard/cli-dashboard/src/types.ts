export interface DopemuxEvent {
    id?: string;
    type?: string;
    namespace?: string;
    priority?: 'CRITICAL' | 'HIGH' | 'NORMAL' | 'LOW' | 'MINIMAL';
    timestamp?: string;
    payload?: any;
    adhd_metadata?: {
        cognitive_load: 'MINIMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'EXTREME';
        attention_required: boolean;
        interruption_safe: boolean;
        focus_context?: string;
        batching_allowed?: boolean;
    };
}

export interface InstanceInfo {
    id: string;
    status: 'active' | 'idle' | 'error' | 'stopped';
    eventCount: number;
    lastSeen: string;
    port?: number;
    sessionId?: string;
    currentUser?: string;
    focusContext?: string;
}

export interface DashboardState {
    connected: boolean;
    instances: InstanceInfo[];
    events: DopemuxEvent[];
    metrics: {
        totalEvents: number;
        eventsPerSecond: number;
        avgLatency: number;
        errorRate: number;
    };
    adhdMetrics: {
        highCognitiveLoad: number;
        completions: number;
        focusChanges: number;
        interruptionsSafe: number;
    };
    selectedInstance: string | null;
    view: 'overview' | 'events' | 'instances' | 'adhd';
}