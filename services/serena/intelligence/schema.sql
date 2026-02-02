-- Serena v2 Phase 2: PostgreSQL Intelligence Schema
-- ADHD-optimized code relationship graph and learning patterns
-- Built on Layer 1 StructuralElement and complexity foundations

-- Extension for better JSON and performance
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ========================================
-- Core Code Intelligence Tables
-- ========================================

-- Code elements with enhanced intelligence metadata
CREATE TABLE code_elements (
    id SERIAL PRIMARY KEY,

    -- Basic identification (from Layer 1 StructuralElement)
    file_path TEXT NOT NULL,
    element_name TEXT NOT NULL,
    element_type VARCHAR(50) NOT NULL, -- function, class, variable, method, etc.
    language VARCHAR(20) NOT NULL,

    -- Location and scope
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_column INTEGER DEFAULT 0,
    end_column INTEGER DEFAULT 0,

    -- ADHD complexity scoring (building on Layer 1)
    complexity_score REAL DEFAULT 0.0 CHECK (complexity_score >= 0.0 AND complexity_score <= 1.0),
    complexity_level VARCHAR(20) DEFAULT 'simple', -- simple, moderate, complex, very_complex
    cognitive_load_factor REAL DEFAULT 0.0, -- ADHD-specific cognitive burden

    -- Tree-sitter structural analysis data
    tree_sitter_metadata JSONB DEFAULT '{}', -- AST node details, syntax patterns
    structural_signature TEXT, -- Hash of structural patterns for matching

    -- Usage and navigation patterns
    access_frequency INTEGER DEFAULT 0, -- How often this element is navigated to
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    average_session_time REAL DEFAULT 0.0, -- Average time spent in this element

    -- ADHD navigation insights
    adhd_insights JSONB DEFAULT '[]', -- ["complex nesting", "long function", etc.]
    focus_recommendations JSONB DEFAULT '[]', -- ADHD-specific suggestions

    -- Versioning and cache invalidation
    content_hash VARCHAR(64), -- Hash of element content for change detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Performance indexes
    UNIQUE(file_path, element_name, start_line, end_line)
);

-- Create indexes for fast ADHD navigation queries
CREATE INDEX idx_code_elements_complexity ON code_elements (complexity_level, complexity_score);
CREATE INDEX idx_code_elements_file ON code_elements (file_path);
CREATE INDEX idx_code_elements_type ON code_elements (element_type, language);
CREATE INDEX idx_code_elements_access ON code_elements (access_frequency DESC, last_accessed DESC);
CREATE INDEX idx_code_elements_cognitive_load ON code_elements (cognitive_load_factor);
CREATE INDEX idx_code_elements_tree_sitter ON code_elements USING gin (tree_sitter_metadata);

-- ========================================
-- Code Relationship Intelligence
-- ========================================

-- Enhanced relationships with ADHD cognitive load scoring
CREATE TABLE code_relationships (
    id SERIAL PRIMARY KEY,

    -- Relationship identification
    source_element_id INTEGER REFERENCES code_elements(id) ON DELETE CASCADE,
    target_element_id INTEGER REFERENCES code_elements(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- calls, imports, inherits, defines, uses, etc.

    -- Relationship strength and context
    strength REAL DEFAULT 0.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    confidence REAL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    context_type VARCHAR(30) DEFAULT 'direct', -- direct, indirect, conditional, loop, etc.

    -- ADHD-specific relationship metadata
    cognitive_load REAL DEFAULT 0.0, -- Mental burden of understanding this relationship
    complexity_increase REAL DEFAULT 0.0, -- How much this relationship adds to overall complexity
    adhd_navigation_difficulty VARCHAR(20) DEFAULT 'easy', -- easy, moderate, hard, overwhelming

    -- Navigation and usage patterns
    traversal_frequency INTEGER DEFAULT 0, -- How often users navigate this relationship
    average_traversal_time REAL DEFAULT 0.0, -- Time to understand the relationship
    last_traversed TIMESTAMP WITH TIME ZONE,

    -- Analysis metadata
    detection_method VARCHAR(50), -- tree_sitter, lsp, static_analysis, user_behavior
    detection_confidence REAL DEFAULT 0.0,
    analysis_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate relationships
    UNIQUE(source_element_id, target_element_id, relationship_type)
);

-- Indexes for fast relationship queries (ADHD <200ms requirement)
CREATE INDEX idx_code_relationships_source ON code_relationships (source_element_id, relationship_type);
CREATE INDEX idx_code_relationships_target ON code_relationships (target_element_id, relationship_type);
CREATE INDEX idx_code_relationships_cognitive_load ON code_relationships (cognitive_load, adhd_navigation_difficulty);
CREATE INDEX idx_code_relationships_strength ON code_relationships (strength DESC, confidence DESC);
CREATE INDEX idx_code_relationships_traversal ON code_relationships (traversal_frequency DESC, average_traversal_time);

-- ========================================
-- ADHD Navigation Pattern Learning
-- ========================================

-- Individual user navigation patterns for adaptive learning
CREATE TABLE navigation_patterns (
    id SERIAL PRIMARY KEY,

    -- Session and user identification
    user_session_id VARCHAR(100) NOT NULL, -- Can be user ID or session identifier
    workspace_path TEXT NOT NULL,

    -- Navigation sequence
    pattern_sequence JSONB NOT NULL, -- Array of navigation actions with timestamps
    sequence_hash VARCHAR(64), -- Hash for pattern matching and deduplication

    -- Pattern characteristics
    pattern_type VARCHAR(30) DEFAULT 'exploration', -- exploration, debugging, implementation, review
    context_switches INTEGER DEFAULT 0, -- Number of context switches in pattern
    total_duration_ms INTEGER DEFAULT 0, -- Total time for this pattern
    complexity_progression REAL DEFAULT 0.0, -- How complexity changed during navigation

    -- Learning effectiveness
    effectiveness_score REAL DEFAULT 0.0 CHECK (effectiveness_score >= 0.0 AND effectiveness_score <= 1.0),
    completion_status VARCHAR(20) DEFAULT 'incomplete', -- complete, incomplete, abandoned
    user_satisfaction REAL DEFAULT 0.0, -- If available from user feedback

    -- ADHD-specific pattern metadata
    attention_span_seconds INTEGER DEFAULT 0, -- Continuous attention time
    cognitive_fatigue_score REAL DEFAULT 0.0, -- Detected fatigue level
    focus_mode_used BOOLEAN DEFAULT FALSE, -- Whether ADHD focus mode was active
    interruption_count INTEGER DEFAULT 0, -- External interruptions detected

    -- ADHD accommodations used
    adhd_accommodations JSONB DEFAULT '{}', -- {progressive_disclosure: true, complexity_filtering: true}
    accommodation_effectiveness REAL DEFAULT 0.0, -- How well accommodations worked

    -- Pattern learning metadata
    pattern_frequency INTEGER DEFAULT 1, -- How often this pattern appears
    last_occurrence TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    learning_weight REAL DEFAULT 1.0, -- Weight for learning algorithm

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for pattern recognition and learning
CREATE INDEX idx_navigation_patterns_user ON navigation_patterns (user_session_id, workspace_path);
CREATE INDEX idx_navigation_patterns_hash ON navigation_patterns (sequence_hash, pattern_type);
CREATE INDEX idx_navigation_patterns_effectiveness ON navigation_patterns (effectiveness_score DESC, completion_status);
CREATE INDEX idx_navigation_patterns_adhd ON navigation_patterns (focus_mode_used, cognitive_fatigue_score);
CREATE INDEX idx_navigation_patterns_frequency ON navigation_patterns (pattern_frequency DESC, last_occurrence DESC);
CREATE INDEX idx_navigation_patterns_sequence ON navigation_patterns USING gin (pattern_sequence);

-- ========================================
-- Adaptive Learning Intelligence
-- ========================================

-- Personalized learning profiles for ADHD navigation optimization
CREATE TABLE learning_profiles (
    id SERIAL PRIMARY KEY,

    -- User identification
    user_session_id VARCHAR(100) NOT NULL,
    workspace_path TEXT NOT NULL,

    -- Learning characteristics
    preferred_complexity_level VARCHAR(20) DEFAULT 'moderate', -- simple, moderate, complex
    optimal_result_limit INTEGER DEFAULT 10, -- ADHD-optimal number of results
    attention_span_minutes INTEGER DEFAULT 25, -- Typical focused attention period
    context_switch_tolerance INTEGER DEFAULT 3, -- Comfortable context switches per session

    -- ADHD accommodation preferences
    progressive_disclosure_preference BOOLEAN DEFAULT TRUE,
    complexity_warnings_enabled BOOLEAN DEFAULT TRUE,
    gentle_guidance_enabled BOOLEAN DEFAULT TRUE,
    focus_mode_trigger_threshold REAL DEFAULT 0.7, -- Complexity threshold for focus mode

    -- Learned navigation preferences
    preferred_navigation_patterns JSONB DEFAULT '[]', -- Most effective patterns for this user
    avoid_patterns JSONB DEFAULT '[]', -- Patterns that cause fatigue or confusion
    optimal_element_types JSONB DEFAULT '[]', -- Element types this user navigates best

    -- Performance and adaptation
    average_session_duration_minutes INTEGER DEFAULT 0,
    session_count INTEGER DEFAULT 0,
    learning_convergence_score REAL DEFAULT 0.0, -- How well the system has learned this user
    adaptation_rate REAL DEFAULT 0.1, -- Learning rate for this user's patterns

    -- Cognitive load management
    peak_performance_times JSONB DEFAULT '[]', -- Times of day when user is most effective
    fatigue_indicators JSONB DEFAULT '{}', -- Learned fatigue patterns
    recovery_strategies JSONB DEFAULT '[]', -- Effective recovery approaches

    -- Timestamps and versioning
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_session TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- One profile per user per workspace
    UNIQUE(user_session_id, workspace_path)
);

-- Indexes for learning profile lookups
CREATE INDEX idx_learning_profiles_user ON learning_profiles (user_session_id, workspace_path);
CREATE INDEX idx_learning_profiles_convergence ON learning_profiles (learning_convergence_score DESC);
CREATE INDEX idx_learning_profiles_sessions ON learning_profiles (session_count DESC, last_session DESC);

-- ========================================
-- Pattern Store and Reuse Intelligence
-- ========================================

-- Successful navigation strategies for reuse
CREATE TABLE navigation_strategies (
    id SERIAL PRIMARY KEY,

    -- Strategy identification
    strategy_name VARCHAR(100) NOT NULL,
    strategy_type VARCHAR(30) NOT NULL, -- exploration, debugging, implementation, refactoring
    description TEXT,

    -- Strategy definition
    pattern_template JSONB NOT NULL, -- Template pattern that can be adapted
    success_conditions JSONB DEFAULT '{}', -- Conditions that indicate strategy success
    complexity_range JSONB DEFAULT '{"min": 0.0, "max": 1.0}', -- Complexity range this strategy works for

    -- Effectiveness metrics
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    average_completion_time_minutes INTEGER DEFAULT 0,
    user_satisfaction_score REAL DEFAULT 0.0,

    -- ADHD optimization
    cognitive_load_reduction REAL DEFAULT 0.0, -- How much this strategy reduces cognitive load
    attention_preservation_score REAL DEFAULT 0.0, -- How well it preserves attention
    interruption_resistance REAL DEFAULT 0.0, -- How well it handles interruptions

    -- Context and applicability
    applicable_languages JSONB DEFAULT '[]', -- Languages this strategy works for
    applicable_element_types JSONB DEFAULT '[]', -- Element types this strategy applies to
    required_accommodations JSONB DEFAULT '[]', -- ADHD accommodations needed

    -- Learning and evolution
    learning_confidence REAL DEFAULT 0.0, -- How confident we are in this strategy
    last_successful_use TIMESTAMP WITH TIME ZONE,
    evolution_history JSONB DEFAULT '[]', -- How the strategy has evolved

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(strategy_name, strategy_type)
);

-- Indexes for strategy matching and recommendation
CREATE INDEX idx_navigation_strategies_type ON navigation_strategies (strategy_type, success_rate DESC);
CREATE INDEX idx_navigation_strategies_effectiveness ON navigation_strategies (success_rate DESC, usage_count DESC);
CREATE INDEX idx_navigation_strategies_adhd ON navigation_strategies (cognitive_load_reduction DESC, attention_preservation_score DESC);
CREATE INDEX idx_navigation_strategies_languages ON navigation_strategies USING gin (applicable_languages);
CREATE INDEX idx_navigation_strategies_elements ON navigation_strategies USING gin (applicable_element_types);

-- ========================================
-- Integration with ConPort Knowledge Graph
-- ========================================

-- Links between Serena code intelligence and ConPort decisions/patterns
CREATE TABLE conport_integration_links (
    id SERIAL PRIMARY KEY,

    -- Serena element reference
    serena_element_id INTEGER REFERENCES code_elements(id) ON DELETE CASCADE,
    serena_element_type VARCHAR(50) NOT NULL, -- code_element, relationship, pattern, strategy

    -- ConPort reference
    conport_workspace TEXT NOT NULL, -- ConPort workspace identifier
    conport_item_type VARCHAR(50) NOT NULL, -- decision, progress_entry, system_pattern, custom_data
    conport_item_id TEXT NOT NULL, -- ConPort item identifier

    -- Link metadata
    link_type VARCHAR(50) NOT NULL, -- implements_decision, relates_to_pattern, addresses_issue
    link_strength REAL DEFAULT 0.0 CHECK (link_strength >= 0.0 AND link_strength <= 1.0),
    bidirectional BOOLEAN DEFAULT TRUE,

    -- Context and reasoning
    link_context TEXT, -- Human-readable explanation of the link
    automated_confidence REAL DEFAULT 0.0, -- Confidence if automatically detected
    user_confirmed BOOLEAN DEFAULT FALSE, -- Whether user has confirmed this link

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Prevent duplicate links
    UNIQUE(serena_element_id, serena_element_type, conport_item_type, conport_item_id, link_type)
);

-- Indexes for ConPort integration queries
CREATE INDEX idx_conport_links_serena ON conport_integration_links (serena_element_id, serena_element_type);
CREATE INDEX idx_conport_links_conport ON conport_integration_links (conport_workspace, conport_item_type, conport_item_id);
CREATE INDEX idx_conport_links_strength ON conport_integration_links (link_strength DESC, user_confirmed);

-- ========================================
-- Performance and Maintenance
-- ========================================

-- Database optimization for ADHD <200ms requirements
COMMENT ON TABLE code_elements IS 'Core code intelligence with ADHD-optimized complexity scoring';
COMMENT ON TABLE code_relationships IS 'Code relationships with cognitive load analysis for ADHD navigation';
COMMENT ON TABLE navigation_patterns IS 'User navigation pattern learning for adaptive ADHD optimization';
COMMENT ON TABLE learning_profiles IS 'Personalized ADHD navigation learning profiles';
COMMENT ON TABLE navigation_strategies IS 'Proven navigation strategies for pattern reuse';
COMMENT ON TABLE conport_integration_links IS 'Integration links with ConPort knowledge graph';

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all tables
CREATE TRIGGER update_code_elements_updated_at BEFORE UPDATE ON code_elements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_code_relationships_updated_at BEFORE UPDATE ON code_relationships FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_navigation_patterns_updated_at BEFORE UPDATE ON navigation_patterns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learning_profiles_updated_at BEFORE UPDATE ON learning_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_navigation_strategies_updated_at BEFORE UPDATE ON navigation_strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conport_integration_links_updated_at BEFORE UPDATE ON conport_integration_links FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Initial Data and Configuration
-- ========================================

-- Insert default ADHD-optimized navigation strategies
INSERT INTO navigation_strategies (strategy_name, strategy_type, description, pattern_template, applicable_languages, cognitive_load_reduction, attention_preservation_score) VALUES
('Progressive Function Exploration', 'exploration', 'Start with function signature, then expand to implementation details progressively', '{"steps": ["view_signature", "check_docstring", "examine_parameters", "explore_body"], "max_depth": 3}', '["python", "javascript", "typescript"]', 0.4, 0.6),
('Class Hierarchy Simplification', 'exploration', 'Navigate class relationships in complexity order, hiding complex inheritance initially', '{"steps": ["view_class_definition", "show_simple_methods", "reveal_complex_methods", "explore_inheritance"], "complexity_filter": true}', '["python", "typescript", "java"]', 0.5, 0.7),
('Focused Debugging Path', 'debugging', 'Follow error traces with minimal context switching and complexity filtering', '{"steps": ["locate_error", "examine_immediate_context", "trace_call_stack"], "focus_mode": true, "max_results": 5}', '["python", "javascript", "typescript", "rust"]', 0.6, 0.8);