# Dopemux Terminal IDE Architecture

**Version**: 1.0
**Date**: September 17, 2025
**Category**: Terminal Interface Implementation

## Overview

Dopemux's Terminal IDE transforms the command-line development experience through modern terminal UI frameworks while maintaining the efficiency and scriptability of traditional workflows. This specification integrates cutting-edge terminal tools with ADHD-accommodated design principles to create a next-generation development environment that rivals GUI IDEs in functionality while preserving terminal power-user workflows.

## Technology Stack Foundation

### Core Framework: Ratatui

**Ratatui** serves as Dopemux's primary terminal UI foundation, providing the sub-10ms response times critical for ADHD attention preservation and IDE-quality interactions.

```rust
// Dopemux Terminal IDE Core Architecture
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    widgets::{Block, Borders, Paragraph},
    Terminal,
};

use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};

pub struct DopemuxTerminalIDE {
    terminal: Terminal<CrosstermBackend<io::Stdout>>,
    adhd_orchestrator: ADHDOrchestrator,
    editor_manager: EditorManager,
    file_manager: FileManager,
    git_integration: GitIntegration,
    cognitive_monitor: CognitiveLoadMonitor,
}

impl DopemuxTerminalIDE {
    pub async fn new(config: DopemuxConfig) -> Result<Self, DopemuxError> {
        // Initialize terminal with ADHD optimizations
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;

        let backend = CrosstermBackend::new(stdout);
        let terminal = Terminal::new(backend)?;

        // Initialize ADHD-aware components
        let adhd_orchestrator = ADHDOrchestrator::new(config.adhd_profile);
        let cognitive_monitor = CognitiveLoadMonitor::new(&adhd_orchestrator);

        Ok(Self {
            terminal,
            adhd_orchestrator,
            editor_manager: EditorManager::new(&config.editor_config),
            file_manager: FileManager::new(&config.file_config),
            git_integration: GitIntegration::new(&config.git_config),
            cognitive_monitor,
        })
    }

    pub async fn run(&mut self) -> Result<(), DopemuxError> {
        let mut app_state = AppState::new();

        loop {
            // ADHD-aware rendering
            self.render_with_cognitive_optimization(&mut app_state)?;

            // Handle events with attention preservation
            if let Event::Key(key) = event::read()? {
                match self.handle_key_event(key, &mut app_state).await? {
                    EventResult::Quit => break,
                    EventResult::Continue => continue,
                    EventResult::AttentionBreak => {
                        self.handle_attention_break(&mut app_state).await?;
                    }
                }
            }
        }

        // Cleanup
        disable_raw_mode()?;
        execute!(
            self.terminal.backend_mut(),
            LeaveAlternateScreen,
            DisableMouseCapture
        )?;
        self.terminal.show_cursor()?;

        Ok(())
    }

    fn render_with_cognitive_optimization(&mut self, app_state: &mut AppState) -> Result<(), DopemuxError> {
        let cognitive_state = self.cognitive_monitor.get_current_state();

        self.terminal.draw(|frame| {
            // Adaptive layout based on cognitive load
            let layout = if cognitive_state.cognitive_load > 0.8 {
                self.create_simplified_layout(frame.size())
            } else if cognitive_state.attention_state == AttentionState::Hyperfocus {
                self.create_focus_optimized_layout(frame.size())
            } else {
                self.create_standard_layout(frame.size())
            };

            // Render components with ADHD accommodations
            self.render_editor_pane(frame, layout[0], app_state, &cognitive_state);
            self.render_file_explorer(frame, layout[1], app_state, &cognitive_state);
            self.render_status_bar(frame, layout[2], app_state, &cognitive_state);

            // Render attention indicators
            if cognitive_state.needs_break {
                self.render_break_suggestion(frame, frame.size());
            }
        })?;

        Ok(())
    }
}
```

### ADHD-Optimized Layout Management

```yaml
layout_optimization:
  adaptive_layouts:
    simplified_layout:
      trigger: "cognitive_load > 0.8 OR attention_state == 'scattered'"
      configuration:
        panes: 2  # Reduce visual complexity
        sidebar_width: "25%"
        main_content: "75%"
        status_bar: "minimal"
        distractions: "hidden"

    focus_optimized_layout:
      trigger: "attention_state == 'hyperfocus'"
      configuration:
        panes: 1  # Maximize focus area
        sidebar: "hidden"
        main_content: "100%"
        status_bar: "minimal"
        notifications: "suppressed"

    standard_layout:
      trigger: "balanced attention state"
      configuration:
        panes: 3  # Full feature set
        sidebar_width: "20%"
        main_content: "60%"
        auxiliary_pane: "20%"
        status_bar: "full"

  pane_management:
    resize_behavior:
      smooth_transitions: "200ms ease-out transitions for reduced visual stress"
      attention_preservation: "Maintain focus on active pane during resize"
      cognitive_anchoring: "Visual anchors to preserve spatial memory"

    focus_indicators:
      active_pane_highlighting: "Subtle blue border (2px) for active pane"
      inactive_pane_dimming: "10% opacity reduction for inactive panes"
      transition_animations: "Smooth focus transitions (150ms)"
```

## Modern Text Editing Integration

### Micro Editor Integration

**Micro** provides the familiar, modern editing experience within Dopemux's terminal IDE, with extensive ADHD accommodations.

```rust
pub struct MicroEditorIntegration {
    micro_process: Option<Child>,
    editor_config: MicroConfig,
    adhd_adaptations: ADHDEditorAdaptations,
    syntax_highlighter: SyntaxHighlighter,
}

impl MicroEditorIntegration {
    pub async fn new(adhd_profile: &ADHDProfile) -> Self {
        let editor_config = MicroConfig {
            // ADHD-optimized defaults
            auto_save: true,
            save_interval: Duration::from_secs(30), // Frequent auto-save
            tab_size: 4,
            soft_wrap: true,
            line_numbers: true,
            syntax_highlighting: true,
            color_scheme: adhd_profile.preferred_color_scheme.clone(),

            // Cognitive load optimizations
            word_wrap: true,
            show_whitespace: false, // Reduce visual noise
            highlight_current_line: true,
            bracket_matching: true,

            // Attention preservation
            auto_close_brackets: true,
            smart_paste: true,
            undo_limit: 1000, // Extended undo for exploration
        };

        let adhd_adaptations = ADHDEditorAdaptations {
            cognitive_load_monitoring: true,
            attention_break_reminders: true,
            context_preservation: true,
            error_simplification: true,
            progress_celebration: true,
        };

        Self {
            micro_process: None,
            editor_config,
            adhd_adaptations,
            syntax_highlighter: SyntaxHighlighter::new(),
        }
    }

    pub async fn open_file(&mut self, file_path: &Path, context: &EditorContext) -> Result<(), EditorError> {
        // Preserve context before opening new file
        if let Some(current_file) = &context.current_file {
            self.preserve_editor_context(current_file).await?;
        }

        // Launch Micro with ADHD-optimized configuration
        let micro_args = self.build_micro_args(file_path, &context.adhd_state);

        let mut cmd = Command::new("micro");
        cmd.args(&micro_args);
        cmd.env("MICRO_CONFIG_HOME", &self.get_config_path());

        // Set ADHD-specific environment variables
        if context.adhd_state.attention_state == AttentionState::Scattered {
            cmd.env("MICRO_SIMPLE_MODE", "true");
            cmd.env("MICRO_REDUCED_FEATURES", "true");
        }

        self.micro_process = Some(cmd.spawn()?);

        // Monitor editor interaction for cognitive load
        self.start_cognitive_monitoring(context).await?;

        Ok(())
    }

    fn build_micro_args(&self, file_path: &Path, adhd_state: &ADHDState) -> Vec<String> {
        let mut args = vec![
            file_path.to_string_lossy().to_string(),
            "+set".to_string(),
            "autosu".to_string(), // Enable auto-save
            "true".to_string(),
        ];

        // ADHD-specific configurations
        match adhd_state.attention_state {
            AttentionState::Hyperfocus => {
                args.extend_from_slice(&[
                    "+set".to_string(),
                    "statusline".to_string(),
                    "false".to_string(), // Minimize distractions
                ]);
            },
            AttentionState::Scattered => {
                args.extend_from_slice(&[
                    "+set".to_string(),
                    "softwrap".to_string(),
                    "true".to_string(), // Reduce horizontal scrolling
                    "+set".to_string(),
                    "scrollmargin".to_string(),
                    "5".to_string(), // Better context visibility
                ]);
            },
            _ => {}
        }

        args
    }

    async fn preserve_editor_context(&self, file_path: &Path) -> Result<(), EditorError> {
        // Save current cursor position, selection, and editing context
        let context = EditorContextSnapshot {
            file_path: file_path.to_path_buf(),
            cursor_position: self.get_cursor_position().await?,
            selection: self.get_current_selection().await?,
            undo_history: self.get_undo_history().await?,
            timestamp: SystemTime::now(),
        };

        self.context_store.save_context(context).await?;
        Ok(())
    }
}
```

### Helix Editor Alternative

For users preferring modal editing, **Helix** integration provides modern Vim-like functionality with zero-configuration LSP support.

```rust
pub struct HelixEditorIntegration {
    helix_process: Option<Child>,
    lsp_manager: LSPManager,
    tree_sitter: TreeSitterParser,
    adhd_adaptations: ADHDModalAdaptations,
}

impl HelixEditorIntegration {
    pub async fn new(adhd_profile: &ADHDProfile) -> Self {
        let adhd_adaptations = ADHDModalAdaptations {
            // Modal editing accommodations for ADHD
            mode_indicators: EnhancedModeIndicators {
                visual_prominence: true,
                color_coding: true,
                position_consistency: true,
            },

            selection_first_guidance: SelectionGuidance {
                visual_feedback: true,
                progressive_disclosure: true,
                undo_granularity: "fine",
            },

            command_palette_enhancements: CommandPaletteConfig {
                fuzzy_search: true,
                recent_commands: true,
                contextual_suggestions: true,
                adhd_friendly_descriptions: true,
            },
        };

        Self {
            helix_process: None,
            lsp_manager: LSPManager::new_with_adhd_optimizations(),
            tree_sitter: TreeSitterParser::new(),
            adhd_adaptations,
        }
    }

    pub async fn configure_lsp_with_adhd_optimizations(&mut self) -> Result<(), LSPError> {
        // Configure LSP servers with ADHD-friendly settings
        self.lsp_manager.configure_server("rust-analyzer", LSPConfig {
            // Reduce cognitive load from excessive diagnostics
            diagnostics_delay: Duration::from_millis(500),
            max_diagnostics_per_file: 10,

            // Enhance useful features
            hover_delay: Duration::from_millis(200),
            completion_trigger_characters: vec![".".to_string(), ":".to_string()],

            // ADHD-specific optimizations
            simplified_error_messages: true,
            progress_notifications: false, // Reduce distractions
            semantic_highlighting: true,
        })?;

        // Configure other language servers with similar optimizations
        self.configure_typescript_lsp().await?;
        self.configure_python_lsp().await?;

        Ok(())
    }
}
```

## File Management and Navigation

### Yazi File Manager Integration

**Yazi** provides async file management with image preview support and ADHD-optimized navigation patterns.

```rust
pub struct YaziFileManager {
    yazi_instance: YaziInstance,
    preview_manager: PreviewManager,
    navigation_history: NavigationHistory,
    cognitive_optimizer: FileNavCognitiveOptimizer,
}

impl YaziFileManager {
    pub async fn new(adhd_profile: &ADHDProfile) -> Self {
        let cognitive_optimizer = FileNavCognitiveOptimizer {
            // Reduce cognitive load in file navigation
            max_visible_items: match adhd_profile.working_memory_capacity {
                WorkingMemoryCapacity::Limited => 15,
                WorkingMemoryCapacity::Average => 25,
                WorkingMemoryCapacity::Enhanced => 40,
            },

            preview_timeout: Duration::from_millis(300),
            lazy_loading_threshold: 100,

            // Visual organization for ADHD
            color_coding_by_type: true,
            size_indicators: true,
            modification_time_grouping: true,
            git_status_integration: true,
        };

        Self {
            yazi_instance: YaziInstance::new_with_config(YaziConfig {
                async_io: true,
                preview_protocols: vec![
                    PreviewProtocol::Kitty,
                    PreviewProtocol::ITerm2,
                    PreviewProtocol::Sixel,
                ],
                lua_plugins: true,
                package_manager: true,
            }),
            preview_manager: PreviewManager::new(),
            navigation_history: NavigationHistory::new(),
            cognitive_optimizer,
        }
    }

    pub async fn navigate_with_cognitive_support(&mut self,
                                               path: &Path,
                                               context: &NavigationContext) -> Result<NavigationResult, FileManagerError> {
        // Assess cognitive load before navigation
        let cognitive_load = context.cognitive_state.current_load;

        if cognitive_load > 0.8 {
            // Simplify navigation for high cognitive load
            return self.navigate_simplified(path, context).await;
        }

        // Preserve current navigation context
        self.navigation_history.push(NavigationSnapshot {
            current_path: context.current_path.clone(),
            selected_file: context.selected_file.clone(),
            scroll_position: context.scroll_position,
            timestamp: SystemTime::now(),
        });

        // Navigate with full feature set
        let navigation_result = self.yazi_instance.navigate(path).await?;

        // Update cognitive load based on directory complexity
        let directory_complexity = self.assess_directory_complexity(&navigation_result).await?;
        self.cognitive_optimizer.update_load_assessment(directory_complexity);

        // Apply ADHD-specific optimizations
        let optimized_result = self.apply_adhd_optimizations(navigation_result, context).await?;

        Ok(optimized_result)
    }

    async fn navigate_simplified(&mut self,
                                path: &Path,
                                context: &NavigationContext) -> Result<NavigationResult, FileManagerError> {
        // Simplified navigation for scattered attention
        let simplified_config = YaziConfig {
            max_items_per_page: 10,
            preview_enabled: false,
            detailed_view: false,
            plugins_disabled: true,
        };

        let result = self.yazi_instance.navigate_with_config(path, simplified_config).await?;

        // Provide gentle guidance for next actions
        let guidance = NavigationGuidance {
            suggested_actions: vec![
                "Press Enter to open selected file",
                "Press h to go up one directory",
                "Press / to search in current directory",
            ],
            cognitive_load_tip: Some("Take a break if feeling overwhelmed"),
        };

        Ok(NavigationResult {
            files: result.files,
            current_path: result.current_path,
            guidance: Some(guidance),
        })
    }

    async fn assess_directory_complexity(&self, result: &NavigationResult) -> Result<f32, FileManagerError> {
        let mut complexity = 0.0;

        // Factor in number of items
        complexity += (result.files.len() as f32) / 100.0;

        // Factor in file type diversity
        let unique_extensions: HashSet<_> = result.files
            .iter()
            .filter_map(|f| f.extension())
            .collect();
        complexity += (unique_extensions.len() as f32) / 20.0;

        // Factor in directory depth
        complexity += (result.current_path.components().count() as f32) / 10.0;

        // Normalize to 0.0-1.0 range
        Ok(complexity.min(1.0))
    }
}
```

### Broot Integration for Project Navigation

**Broot** provides intelligent project-wide navigation with Git integration and ADHD-friendly search patterns.

```rust
pub struct BrootProjectNavigator {
    broot_instance: BrootInstance,
    search_optimizer: ADHDSearchOptimizer,
    git_integration: GitStatusIntegration,
    project_context: ProjectContext,
}

impl BrootProjectNavigator {
    pub async fn fuzzy_search_with_adhd_support(&mut self,
                                               query: &str,
                                               search_context: &SearchContext) -> Result<SearchResults, SearchError> {
        // Optimize search for ADHD cognitive patterns
        let search_config = self.search_optimizer.optimize_for_attention_state(
            query,
            search_context.attention_state
        );

        // Execute search with cognitive load considerations
        let raw_results = self.broot_instance.search(query, search_config).await?;

        // Apply ADHD-specific result processing
        let processed_results = self.process_results_for_adhd(raw_results, search_context).await?;

        // Provide search guidance if needed
        if processed_results.len() > search_context.cognitive_capacity_limit {
            return Ok(SearchResults {
                results: processed_results[..search_context.cognitive_capacity_limit].to_vec(),
                total_found: processed_results.len(),
                guidance: Some(SearchGuidance {
                    message: format!("Showing {} of {} results. Refine search to see more.",
                                   search_context.cognitive_capacity_limit,
                                   processed_results.len()),
                    suggestions: vec![
                        "Add file extension filter (e.g., .rs, .py)",
                        "Search in specific directory",
                        "Use more specific keywords",
                    ],
                }),
            });
        }

        Ok(SearchResults {
            results: processed_results,
            total_found: processed_results.len(),
            guidance: None,
        })
    }

    async fn process_results_for_adhd(&self,
                                     results: Vec<SearchResult>,
                                     context: &SearchContext) -> Result<Vec<ProcessedSearchResult>, SearchError> {
        let mut processed = Vec::new();

        for result in results {
            let mut processed_result = ProcessedSearchResult {
                file_path: result.file_path,
                relevance_score: result.relevance_score,
                git_status: self.git_integration.get_file_status(&result.file_path).await?,

                // ADHD-specific enhancements
                cognitive_complexity: self.assess_file_complexity(&result.file_path).await?,
                recent_activity: self.get_recent_activity(&result.file_path).await?,
                context_hints: self.generate_context_hints(&result.file_path, context).await?,
            };

            // Apply attention-state-specific processing
            match context.attention_state {
                AttentionState::Scattered => {
                    // Simplify information presentation
                    processed_result.context_hints = processed_result.context_hints
                        .into_iter()
                        .take(2) // Limit to 2 context hints
                        .collect();
                },
                AttentionState::Hyperfocus => {
                    // Provide comprehensive context
                    processed_result.detailed_context = Some(
                        self.generate_detailed_context(&result.file_path).await?
                    );
                },
                _ => {}
            }

            processed.push(processed_result);
        }

        Ok(processed)
    }
}
```

## Code Review and Git Integration

### Delta Diff Viewer Integration

**Delta** provides visually rich git diffs with syntax highlighting and ADHD-optimized presentation.

```rust
pub struct DeltaDiffIntegration {
    delta_config: DeltaConfig,
    syntax_themes: SyntaxThemeManager,
    cognitive_optimizer: DiffCognitiveOptimizer,
    review_context: ReviewContextManager,
}

impl DeltaDiffIntegration {
    pub async fn new(adhd_profile: &ADHDProfile) -> Self {
        let delta_config = DeltaConfig {
            // ADHD-optimized diff presentation
            side_by_side: adhd_profile.visual_processing_preference == VisualProcessing::SideBySide,
            syntax_theme: adhd_profile.preferred_syntax_theme.clone(),
            line_numbers: true,

            // Cognitive load optimizations
            word_diff_regex: Some(r"\w+".to_string()), // Highlight word-level changes
            max_line_distance: 0.6, // Improve change detection
            minus_style: "red bold".to_string(),
            plus_style: "green bold".to_string(),

            // ADHD-specific features
            hyperlinks: true, // Enable navigation to hosting providers
            navigate: true, // Enable n/N navigation
            keep_plus_minus_markers: false, // Reduce visual noise
        };

        let cognitive_optimizer = DiffCognitiveOptimizer {
            max_context_lines: match adhd_profile.working_memory_capacity {
                WorkingMemoryCapacity::Limited => 3,
                WorkingMemoryCapacity::Average => 5,
                WorkingMemoryCapacity::Enhanced => 8,
            },

            chunk_size_limit: 50, // Break large diffs into chunks
            highlight_important_changes: true,
            suppress_whitespace_noise: true,
        };

        Self {
            delta_config,
            syntax_themes: SyntaxThemeManager::new(),
            cognitive_optimizer,
            review_context: ReviewContextManager::new(),
        }
    }

    pub async fn display_diff_with_cognitive_support(&mut self,
                                                    diff_data: &DiffData,
                                                    review_context: &ReviewContext) -> Result<DiffDisplay, DiffError> {
        // Assess cognitive complexity of diff
        let diff_complexity = self.assess_diff_complexity(diff_data).await?;

        // Apply cognitive optimizations based on complexity and user state
        let optimized_config = if diff_complexity > 0.8 || review_context.cognitive_load > 0.7 {
            self.create_simplified_diff_config(&self.delta_config)
        } else {
            self.delta_config.clone()
        };

        // Process diff with ADHD accommodations
        let processed_diff = self.process_diff_for_adhd(diff_data, &optimized_config).await?;

        // Create cognitive load-aware display
        let display = DiffDisplay {
            processed_diff,
            navigation_hints: self.generate_navigation_hints(&review_context.attention_state),
            complexity_indicator: Some(DiffComplexityIndicator {
                level: diff_complexity,
                recommendations: self.generate_complexity_recommendations(diff_complexity),
            }),
            break_suggestions: self.should_suggest_break(diff_complexity, review_context),
        };

        Ok(display)
    }

    async fn process_diff_for_adhd(&self,
                                  diff_data: &DiffData,
                                  config: &DeltaConfig) -> Result<ProcessedDiff, DiffError> {
        // Break large diffs into cognitively manageable chunks
        let chunks = self.cognitive_optimizer.chunk_diff(diff_data)?;

        let mut processed_chunks = Vec::new();
        for chunk in chunks {
            let processed_chunk = ProcessedDiffChunk {
                content: self.apply_delta_formatting(&chunk, config).await?,
                summary: self.generate_chunk_summary(&chunk)?,
                complexity: self.assess_chunk_complexity(&chunk)?,

                // ADHD-specific enhancements
                attention_anchors: self.create_attention_anchors(&chunk)?,
                context_preservation: self.preserve_chunk_context(&chunk)?,
            };

            processed_chunks.push(processed_chunk);
        }

        Ok(ProcessedDiff {
            chunks: processed_chunks,
            total_lines_added: diff_data.lines_added,
            total_lines_removed: diff_data.lines_removed,
            adhd_optimizations_applied: true,
        })
    }

    fn generate_navigation_hints(&self, attention_state: &AttentionState) -> Vec<NavigationHint> {
        match attention_state {
            AttentionState::Scattered => vec![
                NavigationHint {
                    key: "n".to_string(),
                    action: "Next change".to_string(),
                    description: "Move to next diff section".to_string(),
                },
                NavigationHint {
                    key: "q".to_string(),
                    action: "Quit review".to_string(),
                    description: "Save progress and exit".to_string(),
                },
            ],
            AttentionState::Hyperfocus => vec![
                NavigationHint {
                    key: "n/N".to_string(),
                    action: "Navigate changes".to_string(),
                    description: "Next/previous diff sections".to_string(),
                },
                NavigationHint {
                    key: "j/k".to_string(),
                    action: "Scroll".to_string(),
                    description: "Line-by-line navigation".to_string(),
                },
                NavigationHint {
                    key: "/".to_string(),
                    action: "Search".to_string(),
                    description: "Search within diff".to_string(),
                },
            ],
            _ => vec![
                NavigationHint {
                    key: "?".to_string(),
                    action: "Help".to_string(),
                    description: "Show all navigation options".to_string(),
                },
            ],
        }
    }
}
```

### Lazygit Integration

**Lazygit** provides comprehensive git workflow management with ADHD-accommodated interaction patterns.

```rust
pub struct LazygitIntegration {
    lazygit_process: Option<Child>,
    git_config: GitWorkflowConfig,
    adhd_adaptations: ADHDGitAdaptations,
    workflow_tracker: GitWorkflowTracker,
}

impl LazygitIntegration {
    pub async fn new(adhd_profile: &ADHDProfile) -> Self {
        let adhd_adaptations = ADHDGitAdaptations {
            // Simplify complex git operations
            guided_workflows: true,
            operation_confirmations: true,
            undo_redo_support: true,

            // Working memory support
            operation_history: true,
            context_preservation: true,
            visual_git_graph: true,

            // Executive function aids
            commit_message_templates: true,
            branch_naming_assistance: true,
            merge_conflict_guidance: true,
        };

        let git_config = GitWorkflowConfig {
            // ADHD-friendly defaults
            auto_stage_deleted: false, // Require explicit staging
            confirm_force_push: true,
            confirm_reset: true,

            // Enhanced feedback
            show_branch_commits: true,
            show_file_tree: true,
            show_merge_conflicts: true,

            // Cognitive load management
            max_commits_shown: 50,
            max_files_per_commit: 20,
            simplified_status_view: true,
        };

        Self {
            lazygit_process: None,
            git_config,
            adhd_adaptations,
            workflow_tracker: GitWorkflowTracker::new(),
        }
    }

    pub async fn launch_with_adhd_support(&mut self,
                                         repository_path: &Path,
                                         context: &GitContext) -> Result<(), GitError> {
        // Configure Lazygit for current ADHD state
        let config_path = self.create_adhd_optimized_config(context).await?;

        // Launch Lazygit with ADHD-specific environment
        let mut cmd = Command::new("lazygit");
        cmd.current_dir(repository_path);
        cmd.env("LG_CONFIG_FILE", config_path);

        // Set ADHD-specific environment variables
        if context.attention_state == AttentionState::Scattered {
            cmd.env("LG_SIMPLE_MODE", "true");
        }

        self.lazygit_process = Some(cmd.spawn()?);

        // Start workflow tracking for learning and optimization
        self.workflow_tracker.start_session(GitSession {
            repository_path: repository_path.to_path_buf(),
            user_profile: context.adhd_profile.clone(),
            start_time: SystemTime::now(),
        });

        Ok(())
    }

    async fn create_adhd_optimized_config(&self, context: &GitContext) -> Result<PathBuf, GitError> {
        let config = LazygitConfig {
            gui: GuiConfig {
                // ADHD-optimized interface
                theme: context.adhd_profile.preferred_theme.clone(),
                language: "en".to_string(),
                time_format: "15:04".to_string(),
                short_time_format: "15:04".to_string(),

                // Cognitive load optimizations
                show_list_footer: true,
                show_file_tree: !context.cognitive_overload,
                show_random_tip: false, // Reduce distractions

                // ADHD-specific accommodations
                mouse_events: true, // Support multiple interaction modes
                skip_discard_warning: false, // Always confirm destructive operations
                skip_stash_warning: false,
            },

            git: GitConfig {
                paging: PagingConfig {
                    color_arg: "always".to_string(),
                    pager: "delta".to_string(), // Use Delta for diffs
                },

                commit: CommitConfig {
                    sign_off: false,
                    verbose: "oneline".to_string(), // Reduce commit message complexity
                },

                merge_tool: "vimdiff".to_string(),

                // ADHD workflow optimizations
                auto_fetch: Duration::from_secs(300), // Regular but not distracting
                auto_refresh: true,
                disable_start_up_population_checks: false,
            },

            update: UpdateConfig {
                method: "never".to_string(), // Prevent surprise updates during work
                days: 0,
            },
        };

        let config_path = self.get_config_directory()?.join("config.yml");
        self.write_config_file(&config_path, &config).await?;

        Ok(config_path)
    }

    pub async fn provide_git_workflow_guidance(&self,
                                              current_state: &GitRepositoryState,
                                              user_intent: &UserIntent) -> Result<WorkflowGuidance, GitError> {
        let guidance = match user_intent {
            UserIntent::MakeCommit => {
                self.generate_commit_guidance(current_state).await?
            },
            UserIntent::HandleMergeConflict => {
                self.generate_merge_conflict_guidance(current_state).await?
            },
            UserIntent::CreateBranch => {
                self.generate_branch_creation_guidance(current_state).await?
            },
            UserIntent::ReviewChanges => {
                self.generate_review_guidance(current_state).await?
            },
        };

        Ok(guidance)
    }

    async fn generate_commit_guidance(&self, state: &GitRepositoryState) -> Result<WorkflowGuidance, GitError> {
        let staged_files = state.staged_files.len();
        let unstaged_files = state.unstaged_files.len();

        let steps = if staged_files == 0 && unstaged_files > 0 {
            vec![
                GuidanceStep {
                    action: "Stage files".to_string(),
                    description: "Select files to include in commit (Space to stage)".to_string(),
                    cognitive_load: CognitiveLoad::Low,
                },
                GuidanceStep {
                    action: "Write commit message".to_string(),
                    description: "Describe what this commit accomplishes".to_string(),
                    cognitive_load: CognitiveLoad::Medium,
                },
                GuidanceStep {
                    action: "Create commit".to_string(),
                    description: "Finalize the commit (Ctrl+Enter)".to_string(),
                    cognitive_load: CognitiveLoad::Low,
                },
            ]
        } else if staged_files > 0 {
            vec![
                GuidanceStep {
                    action: "Review staged changes".to_string(),
                    description: format!("Review {} staged file(s) before committing", staged_files),
                    cognitive_load: CognitiveLoad::Medium,
                },
                GuidanceStep {
                    action: "Write commit message".to_string(),
                    description: "Describe what this commit accomplishes".to_string(),
                    cognitive_load: CognitiveLoad::Medium,
                },
                GuidanceStep {
                    action: "Create commit".to_string(),
                    description: "Finalize the commit (Ctrl+Enter)".to_string(),
                    cognitive_load: CognitiveLoad::Low,
                },
            ]
        } else {
            vec![
                GuidanceStep {
                    action: "No changes to commit".to_string(),
                    description: "All changes are already committed".to_string(),
                    cognitive_load: CognitiveLoad::Low,
                },
            ]
        };

        Ok(WorkflowGuidance {
            title: "Creating a Commit".to_string(),
            steps,
            estimated_time: Duration::from_secs(180), // 3 minutes
            cognitive_complexity: self.assess_commit_complexity(state),
            tips: vec![
                "Use present tense in commit messages (e.g., 'Add feature' not 'Added feature')".to_string(),
                "Keep first line under 50 characters for better readability".to_string(),
            ],
        })
    }
}
```

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-4)

```yaml
phase_1_implementation:
  ratatui_foundation:
    deliverables:
      - "Basic Ratatui terminal UI with multi-pane layouts"
      - "ADHD-optimized layout management system"
      - "Cognitive load monitoring integration"
      - "Attention state detection framework"

    technical_tasks:
      - "Implement DopemuxTerminalIDE core structure"
      - "Create adaptive layout system with cognitive triggers"
      - "Integrate attention monitoring with keystroke analysis"
      - "Implement basic pane management with focus preservation"

  editor_integration:
    deliverables:
      - "Micro editor integration with ADHD configurations"
      - "Syntax highlighting with cognitive load optimization"
      - "Auto-save and context preservation systems"
      - "Basic file opening and editing workflows"

    technical_tasks:
      - "Implement MicroEditorIntegration with process management"
      - "Configure ADHD-specific Micro settings and environment"
      - "Create editor context preservation system"
      - "Implement cognitive load monitoring for editing sessions"

  file_management:
    deliverables:
      - "Yazi file manager integration with async operations"
      - "Basic file navigation with cognitive optimizations"
      - "Directory complexity assessment system"
      - "Navigation history and context preservation"

    technical_tasks:
      - "Implement YaziFileManager with async file operations"
      - "Create cognitive complexity assessment algorithms"
      - "Implement navigation history and bookmark systems"
      - "Integrate file preview with attention state awareness"
```

### Phase 2: Enhanced Workflows (Weeks 5-8)

```yaml
phase_2_implementation:
  git_integration:
    deliverables:
      - "Delta diff viewer with ADHD-optimized presentation"
      - "Lazygit integration with guided workflows"
      - "Git workflow guidance and template systems"
      - "Merge conflict resolution assistance"

    technical_tasks:
      - "Implement DeltaDiffIntegration with cognitive chunking"
      - "Create LazygitIntegration with ADHD configuration"
      - "Develop git workflow guidance system"
      - "Implement commit message templates and assistance"

  search_and_navigation:
    deliverables:
      - "fzf integration for universal fuzzy finding"
      - "Broot project navigation with Git integration"
      - "Search result optimization for ADHD cognitive patterns"
      - "Context-aware search suggestions and filtering"

    technical_tasks:
      - "Implement BrootProjectNavigator with ADHD search optimization"
      - "Create ADHDSearchOptimizer for result processing"
      - "Develop context-aware search guidance system"
      - "Integrate Git status information in search results"

  enhanced_editing:
    deliverables:
      - "Helix editor integration as modal alternative"
      - "LSP integration with ADHD-optimized configurations"
      - "Tree-sitter parsing for enhanced syntax understanding"
      - "Code completion and diagnostics with cognitive load management"

    technical_tasks:
      - "Implement HelixEditorIntegration with zero-config LSP"
      - "Configure LSP servers with ADHD-friendly settings"
      - "Implement tree-sitter integration for syntax analysis"
      - "Create cognitive load-aware diagnostic presentation"
```

### Phase 3: Advanced Features (Weeks 9-12)

```yaml
phase_3_implementation:
  plugin_architecture:
    deliverables:
      - "Ratatui-based plugin system for extensibility"
      - "ADHD accommodation plugin framework"
      - "Custom widget library for terminal IDE components"
      - "Plugin configuration and management system"

    technical_tasks:
      - "Design plugin architecture with Rust trait system"
      - "Implement plugin loading and lifecycle management"
      - "Create ADHD-specific plugin APIs and abstractions"
      - "Develop plugin configuration and settings management"

  theming_system:
    deliverables:
      - "24-bit color theme system with ADHD optimizations"
      - "Dynamic theme switching based on attention state"
      - "Accessibility compliance with contrast validation"
      - "Custom color palette generator for neurodivergent users"

    technical_tasks:
      - "Implement comprehensive theming system with color validation"
      - "Create attention-state-aware theme switching logic"
      - "Develop accessibility compliance checking and validation"
      - "Implement custom color palette generation algorithms"

  session_persistence:
    deliverables:
      - "tmux integration for session management"
      - "Workspace state preservation across restarts"
      - "Project context restoration with ADHD accommodations"
      - "Session analytics and optimization recommendations"

    technical_tasks:
      - "Implement tmux integration with session persistence"
      - "Create comprehensive workspace state serialization"
      - "Develop project context restoration with cognitive aids"
      - "Implement session analytics and performance monitoring"
```

### Phase 4: Optimization and Polish (Weeks 13-16)

```yaml
phase_4_implementation:
  performance_optimization:
    deliverables:
      - "Sub-10ms rendering performance for all UI updates"
      - "Lazy loading and virtualization for large file trees"
      - "Memory usage optimization for long-running sessions"
      - "Async operation optimization with priority queuing"

    technical_tasks:
      - "Profile and optimize rendering pipeline performance"
      - "Implement virtualization for large datasets"
      - "Optimize memory allocation and garbage collection"
      - "Implement priority-based async operation scheduling"

  adhd_optimization:
    deliverables:
      - "Machine learning models for attention pattern recognition"
      - "Predictive cognitive load assessment and adaptation"
      - "Personalized accommodation tuning based on usage patterns"
      - "Real-time intervention system for cognitive overload"

    technical_tasks:
      - "Implement ML models for attention state prediction"
      - "Create predictive cognitive load assessment system"
      - "Develop personalized accommodation optimization"
      - "Implement real-time cognitive intervention system"

  integration_testing:
    deliverables:
      - "Comprehensive integration test suite"
      - "ADHD user experience validation testing"
      - "Performance benchmarking and regression testing"
      - "Accessibility compliance validation"

    technical_tasks:
      - "Develop comprehensive integration test framework"
      - "Conduct ADHD user experience validation studies"
      - "Implement automated performance benchmarking"
      - "Create accessibility compliance testing automation"
```

## Success Metrics and Validation

### Performance Targets
```yaml
performance_targets:
  rendering_performance:
    target: "Sub-10ms UI updates for attention preservation"
    measurement: "Frame time monitoring with 95th percentile < 10ms"
    validation: "Automated performance testing in CI/CD"

  cognitive_load_optimization:
    target: "40% reduction in reported cognitive fatigue"
    measurement: "Pre/post session cognitive load surveys"
    validation: "Longitudinal user studies with ADHD participants"

  attention_preservation:
    target: "25% increase in sustained attention duration"
    measurement: "Session duration and task completion analytics"
    validation: "Objective attention measurement with validated scales"

  workflow_efficiency:
    target: "30% reduction in task switching overhead"
    measurement: "Time between task initiation and productive work"
    validation: "Workflow analytics and user behavior tracking"
```

### ADHD Accommodation Validation
```yaml
accommodation_validation:
  attention_management:
    metrics:
      - "Hyperfocus session duration and quality"
      - "Scattered attention support effectiveness"
      - "Context switching recovery time"
    validation_methods:
      - "Attention Network Test (ANT) integration"
      - "Continuous Performance Task (CPT) assessment"
      - "Self-reported attention quality scales"

  working_memory_support:
    metrics:
      - "Context preservation success rate"
      - "Information retrieval accuracy and speed"
      - "Cognitive load reduction measurements"
    validation_methods:
      - "N-back task performance with/without scaffolding"
      - "Working memory span assessments"
      - "Dual-task paradigm evaluations"

  executive_function_aids:
    metrics:
      - "Task completion rate improvement"
      - "Planning and organization effectiveness"
      - "Decision-making support utilization"
    validation_methods:
      - "Behavior Rating Inventory of Executive Function (BRIEF)"
      - "Task completion analytics and success rates"
      - "Goal attainment scaling assessments"
```

`★ Insight ─────────────────────────────────────`
This terminal IDE architecture transforms Dopemux from a concept into a concrete implementation plan. By leveraging Ratatui's sub-10ms rendering, Micro's familiar editing, Yazi's async file management, and Delta's beautiful diffs, we create a terminal IDE that rivals GUI tools while preserving the power-user efficiency of command-line workflows. The ADHD accommodations are woven throughout—from cognitive load monitoring to attention-aware layout adaptation—making this the first terminal IDE designed specifically for neurodivergent developers.
`─────────────────────────────────────────────────`

---

**Implementation Status**: Ready for Development
**Dependencies**: Ratatui, Rust toolchain, terminal tool ecosystem
**Estimated Development Time**: 16 weeks with dedicated team
**Success Criteria**: Sub-10ms UI responsiveness, 40% cognitive load reduction, 25% attention preservation improvement
