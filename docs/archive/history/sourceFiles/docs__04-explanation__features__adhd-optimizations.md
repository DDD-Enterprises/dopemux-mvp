# 🧠 ADHD Optimizations Feature Hub

**Central hub for all ADHD-focused features, accommodations, and neurodivergent developer support in DOPEMUX.**

## 🎯 Quick Navigation

### 🚀 Getting Started
- [🏁 ADHD Setup Tutorial](../../01-tutorials/adhd-setup.md) - Configure optimizations for your needs
- [🔧 Quick Configuration](../../02-how-to/adhd-configuration.md) - Essential ADHD settings
- [⚡ Quick Reference](../../03-reference/quick-ref/adhd-tips.md) - Optimization shortcuts

### 🆘 Need Help?
- **New to ADHD features?** → [ADHD Setup Tutorial](../../01-tutorials/adhd-setup.md)
- **System not adapting?** → [Attention Tracking Guide](../../02-how-to/attention-tracking.md)
- **Lost context?** → [Session Recovery](../../02-how-to/restore-backup.md)
- **Need customization?** → [ADHD Configuration](../../02-how-to/adhd-configuration.md)

---

## 📚 Core ADHD Features

### 🎯 Attention Management
**Adaptive system that responds to your cognitive state in real-time**

#### Features
- **Real-time attention detection** - Automatically classify focused, scattered, hyperfocus, or distracted states
- **Adaptive interface** - UI complexity matches current cognitive capacity
- **State-aware responses** - Different interaction patterns for different attention states
- **Focus session tracking** - Monitor and optimize work periods

#### Documentation
- **[📖 How It Works](../adhd/attention-architecture.md)** - Understanding attention classification
- **[🔧 Setup Guide](../../02-how-to/attention-tracking.md)** - Configure attention monitoring
- **[📝 ADR-103](../../90-adr/103-attention-state-classification.md)** - Why this approach was chosen
- **[📊 API Reference](../../03-reference/api/adhd.md#attention-management)** - Technical integration

#### States & Adaptations
| State | Interface | Information | Actions |
|-------|-----------|-------------|---------|
| 🎯 **Focused** | Full details | Comprehensive | Multiple options |
| 🌪️ **Scattered** | Simplified | Essential only | Single clear step |
| 🔥 **Hyperfocus** | Streamlined | Minimal text | Direct implementation |
| 😵‍💫 **Distracted** | Gentle guidance | Supportive tone | Simple recovery |

### 💾 Context Preservation
**Never lose your mental model, even during interruptions**

#### Features
- **30-second auto-save** - Transparent context preservation without cognitive load
- **Complete state capture** - Files, positions, mental model, decisions, environment
- **<500ms restoration** - Instant recovery that preserves focus flow
- **Interruption protection** - Survive crashes, network issues, attention breaks

#### Documentation
- **[📖 Context Theory](../adhd/context-theory.md)** - Why context matters for ADHD brains
- **[🔧 Manual Save Guide](../../02-how-to/manual-context-save.md)** - Explicit context saving
- **[📝 ADR-102](../../90-adr/102-auto-save-strategy.md)** - 30-second interval decision
- **[📊 Storage Architecture](../../90-adr/003-multi-level-memory-architecture.md)** - How context is stored

#### Context Layers
- **Immediate**: Current file, cursor, selection, active variables
- **Working**: Open files, tabs, recent history, active errors
- **Session**: Project goals, completed tasks, key decisions, insights

### 🎨 Gentle User Experience
**Supportive, non-judgmental interface that reduces stress and builds confidence**

#### Features
- **Gentle error handling** - Collaborative problem-solving instead of blame
- **Progressive disclosure** - Information complexity matches cognitive capacity
- **Decision reduction** - Maximum 3 options to prevent overwhelm
- **Encouraging feedback** - Supportive language and progress celebration

#### Documentation
- **[📖 Gentle UX Principles](../adhd/gentle-ux.md)** - Design philosophy and patterns
- **[🔧 Error Recovery](../../02-how-to/error-recovery.md)** - When things go wrong
- **[📝 ADR-104](../../90-adr/104-gentle-error-handling.md)** - Gentle error approach
- **[📝 ADR-105](../../90-adr/105-progressive-disclosure-pattern.md)** - Information layering

#### Gentle Patterns
- **Supportive language**: "Let's fix this together" vs. "Error: Invalid input"
- **Context preservation**: Errors don't lose work or mental model
- **Clear guidance**: Specific next steps instead of vague suggestions
- **Emotional safety**: Non-judgmental tone reduces shame and anxiety

### ⏱️ Task Decomposition
**Break complex work into manageable 25-minute focus segments**

#### Features
- **Automatic task breakdown** - Complex features split into achievable chunks
- **25-minute optimization** - Work periods matched to average ADHD focus duration
- **Progress visualization** - Clear indicators of completion and remaining work
- **Dependency tracking** - Understand prerequisites and relationships

#### Documentation
- **[📖 Task Decomposition Science](../adhd/task-decomposition.md)** - Research behind 25-minute chunks
- **[🔧 Task Management](../../02-how-to/task-management.md)** - Create and manage ADHD-friendly tasks
- **[📊 Task API](../../03-reference/api/tasks.md)** - Technical task management
- **[🎯 Task Management Hub](task-management.md)** - Related task features

#### Decomposition Strategy
```
"Implement user authentication" →
├── Set up user model (25 min)
├── Create login endpoint (25 min)
├── Add password hashing (25 min)
├── Implement JWT tokens (25 min)
└── Add logout functionality (25 min)
```

### 🧠 Executive Function Support
**Reduce decision fatigue and provide clear structure for complex development tasks**

#### Features
- **Decision reduction** - Limit choices to prevent cognitive overload
- **Clear next steps** - Always know what to do next
- **Structure provision** - Scaffolding for complex workflows
- **Memory augmentation** - System remembers details so you don't have to

#### Documentation
- **[📖 Executive Function Support](../adhd/executive-function.md)** - How DOPEMUX supports planning and organization
- **[🔧 Workflow Setup](../../02-how-to/workflow-setup.md)** - Structure your development process
- **[📊 Progress Tracking](../../03-reference/api/progress.md)** - Monitor task completion

#### Support Patterns
- **Planning assistance**: Break goals into specific, actionable steps
- **Decision scaffolding**: Provide recommended choices with clear rationale
- **Progress tracking**: Visual indicators of completion and remaining work
- **Context bridging**: Connect current work to overall project goals

---

## 🏗️ Architecture & Implementation

### 🎛️ Configuration System
**Customize ADHD accommodations to match your individual needs**

#### Global Settings (`~/.claude/CLAUDE.md`)
```yaml
adhd_profile:
  focus_duration: 25              # minutes
  break_interval: 5               # minutes
  notification_style: gentle     # gentle/standard/minimal
  visual_complexity: minimal     # minimal/standard/comprehensive
  attention_adaptation: true     # enable real-time adaptation
```

#### Project Settings (`.dopemux/config.yaml`)
```yaml
adhd_accommodations:
  auto_save_interval: 30          # seconds
  max_options_displayed: 3        # choices
  error_handling_style: gentle   # gentle/standard/technical
  context_preservation: true     # enable comprehensive saves
```

#### Documentation
- **[📖 Configuration Hub](configuration.md)** - All configuration options
- **[🔧 ADHD Configuration Guide](../../02-how-to/adhd-configuration.md)** - Setup walkthrough
- **[📊 Config Reference](../../03-reference/config/adhd-profile.md)** - Complete schema

### 🧬 Technical Architecture
**How ADHD features are implemented and integrated**

#### Attention Monitor (`src/dopemux/adhd/attention_monitor.py`)
```python
class AttentionMonitor:
    def classify_current_state(self) -> AttentionState:
        # Analyze keystroke patterns, timing, context switches
        # Return: FOCUSED, SCATTERED, HYPERFOCUS, DISTRACTED

    def adapt_interface(self, state: AttentionState):
        # Adjust UI complexity based on cognitive capacity
```

#### Context Manager (`src/dopemux/adhd/context_manager.py`)
```python
class ContextManager:
    def auto_save_context(self):
        # Save every 30 seconds: files, positions, mental model

    def restore_session(self, session_id: str) -> Dict:
        # <500ms restoration target
```

#### Documentation
- **[📖 ADHD Architecture](../adhd/attention-architecture.md)** - System design
- **[📝 Technical ADRs](../../90-adr/README.md#adhd-optimizations-100-199)** - Design decisions
- **[📊 API Reference](../../03-reference/api/adhd.md)** - Programming interface

### 📊 Memory Integration
**How ADHD features connect to the multi-level memory system**

#### Memory Layers for ADHD
- **Redis Cache**: Real-time attention state and session context
- **PostgreSQL**: User ADHD preferences and accommodation history
- **OpenMemory**: Personal patterns and successful strategies
- **ConPort**: Project-specific ADHD accommodations

#### Documentation
- **[📖 Memory Architecture](../../90-adr/003-multi-level-memory-architecture.md)** - Overall memory design
- **[📖 OpenMemory Integration](../../90-adr/506-openmemory-integration.md)** - Personal ADHD patterns
- **[📊 Session Management Hub](session-management.md)** - Context preservation features

---

## 🎓 Learning & Research

### 📚 Understanding ADHD in Development
**Educational resources about ADHD and development workflow optimization**

#### Core Concepts
- **[Attention Management](../adhd/attention-architecture.md)** - How attention affects development workflow
- **[Context Switching Impact](../research/context-switching.md)** - Cognitive load studies
- **[Time Perception](../research/time-perception.md)** - ADHD time management challenges
- **[Working Memory](../adhd/context-theory.md)** - Why context preservation matters

#### Research Foundation
- **[Neurodiversity Research](../research/neurodiversity.md)** - Scientific background
- **[Attention Studies](../research/attention-studies.md)** - Focus research
- **[User Testing Results](../research/adhd-user-testing.md)** - Real-world validation

### 🛠️ Development Guidelines
**For developers working on ADHD features**

#### Design Principles
- **[ADHD-Centered Design](../../90-adr/101-adhd-centered-design.md)** - Core philosophy
- **[Gentle UX Patterns](../adhd/gentle-ux.md)** - Interface design guidelines
- **[Progressive Disclosure](../../90-adr/105-progressive-disclosure-pattern.md)** - Information architecture

#### Implementation Patterns
- **[ADHD Design Patterns](../patterns/adhd-patterns.md)** - Reusable solutions
- **[Testing Guidelines](../../02-how-to/adhd-testing.md)** - Test with neurodivergent users
- **[Accessibility Standards](../industry/accessibility.md)** - A11y compliance

---

## 🔗 Related Features

### 🤖 AI Integration
- **[Claude Code Integration Hub](claude-integration.md)** - AI development workflow
- **[MCP Server Ecosystem](mcp-ecosystem.md)** - External AI services

### 📊 Monitoring & Health
- **[Health Monitoring Hub](health-monitoring.md)** - System reliability
- **[Session Management Hub](session-management.md)** - Context preservation

### ⚙️ Configuration & Setup
- **[Configuration System Hub](configuration.md)** - Settings management
- **[Testing Infrastructure Hub](testing.md)** - Quality assurance

---

## 🆘 Support & Community

### 💬 Getting Help
- **Issues**: Report ADHD feature bugs or requests
- **Discussions**: Share ADHD optimization strategies
- **Documentation**: Improve ADHD-related docs
- **Testing**: Participate in neurodivergent user testing

### 🧑‍💻 Contributing
- **[ADHD Testing Guide](../../02-how-to/adhd-testing.md)** - Test with neurodivergent users
- **[Gentle UX Review](../../02-how-to/gentle-ux-review.md)** - Review interface language
- **[Accessibility Audit](../../02-how-to/accessibility-audit.md)** - Ensure inclusive design

### 📈 Metrics & Feedback
- User satisfaction scores for ADHD accommodations
- Attention state classification accuracy
- Context restoration performance
- Task completion rates with ADHD features

---

**🧠 DOPEMUX is built for ADHD developers** - every feature designed with neurodivergent cognitive patterns in mind.

*Making development accessible, one focused session at a time.*