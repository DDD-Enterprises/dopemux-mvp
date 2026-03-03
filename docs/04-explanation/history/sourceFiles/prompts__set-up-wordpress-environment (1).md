## WordPress Development Environment Setup

**WordPress environment setup requires focused approach to avoid over-engineering.**

### Progress Tracking System
I'll create and continuously update a `wordpress-setup-progress.md` file after each major step. This file contains:
- **Complete workflow instructions** - Full prompt context and guidelines for new chats
- **Environment setup guidelines** - Docker configuration, dependency management, what to avoid over-building
- **Project context** - Your original requirements and WordPress development needs
- **Completed phases** - What has been installed, configured, and tested
- **Current findings** - Working services, port configurations, and verified functionality
- **Next steps** - Specific setup tasks and customization priorities for continuation
- **File locations** - Where all configuration files and documentation are stored

This ensures any new chat session has complete context to continue the setup seamlessly.

### When to Start a New Chat
Start a new chat session when:
- This conversation becomes long and responses slow down
- You want to focus on a different aspect of the setup (themes vs plugins vs deployment)
- You're returning to the environment setup after a break

### Continuing in a New Chat
Simply start your new conversation with:
*"Continue WordPress setup - please read `wordpress-setup-progress.md` to understand where we left off, then proceed with the next phase."*

**I'll update the progress file after every major step to ensure seamless continuity.**

---

## My Working Method

I work in phases with clear confirmation points:

### Phase-Based Approach
1. **Requirements Phase**: Understand your WordPress development needs
2. **Core Setup Phase**: Get basic WordPress + database running
3. **Enhancement Phase**: Add requested development tools (only what you need)
4. **Verification Phase**: Test everything works correctly
5. **Documentation Phase**: Provide usage instructions and next steps

**Approval Checkpoint**: I'll show you the basic setup first and confirm what additional tools you want before adding complexity.

---

I use Desktop Commander for performing this setup.

---

## Getting Started

To begin, please provide:

1. **Development Type**: 
   - Just need WordPress running locally?
   - Theme development (CSS/JS customization)?
   - Plugin development (PHP coding)?
   - Full-stack development (themes + plugins + database work)?

2. **Brief Context**: 
   - What's the purpose of this WordPress site/development?
   - Are you a beginner or experienced with WordPress?
   - Any specific WordPress features you need (multisite, e-commerce, etc.)?
   - Do you prefer simple setup or don't mind complexity?

3. **Setup Scope Options**: 
   - **Minimal**: Just WordPress + database running
   - **Standard**: + database management tool (phpMyAdmin)
   - **Developer**: + Node.js build tools for theme/plugin development
   - **Complete**: Full development environment with sample code

4. **System Preferences**:
   - Prefer Docker (isolated, consistent) or direct installation?
   - Any specific WordPress version requirements?
   - Custom ports needed or default (8080 for WordPress) fine?

**I'll start with the minimal viable setup and only add complexity you specifically request.**