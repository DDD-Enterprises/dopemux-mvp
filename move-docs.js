const fs = require('fs');
const path = require('path');

const baseDir = '/Users/hue/code/dopemux-mvp/docs';

// Create directories
const implHistoryDir = path.join(baseDir, 'archive', 'implementation-history');
const deprecatedDir = path.join(baseDir, 'archive', 'deprecated');

fs.mkdirSync(implHistoryDir, { recursive: true });
fs.mkdirSync(deprecatedDir, { recursive: true });

// Files to move to implementation-history
const implFiles = [
    'DOPESMUX_ULTRA_UI_MVP_COMPLETION.md',
    'PHASE1_SERVICES_INTEGRATION_COMPLETED.md',
    'PHASE_3_NEXT_STEPS_PLANNING.md',
    'REORGANIZATION-2025-10-29.md',
    'RELEASE_NOTES_v0.1.0.md',
    'pm-integration-changes.md'
];

// Files to move to deprecated
const deprecatedFiles = [
    'claude-code-tools-integration-plan.md',
    'conport_enhancement_decisions.json'
];

const movedImpl = [];
const movedDep = [];
const errors = [];

// Move implementation-history files
implFiles.forEach(file => {
    const src = path.join(baseDir, file);
    const dst = path.join(implHistoryDir, file);
    try {
        if (fs.existsSync(src)) {
            fs.renameSync(src, dst);
            movedImpl.push(file);
        } else {
            errors.push(`Not found: ${file}`);
        }
    } catch (e) {
        errors.push(`Error moving ${file}: ${e.message}`);
    }
});

// Move deprecated files
deprecatedFiles.forEach(file => {
    const src = path.join(baseDir, file);
    const dst = path.join(deprecatedDir, file);
    try {
        if (fs.existsSync(src)) {
            fs.renameSync(src, dst);
            movedDep.push(file);
        } else {
            errors.push(`Not found: ${file}`);
        }
    } catch (e) {
        errors.push(`Error moving ${file}: ${e.message}`);
    }
});

console.log('✅ Successfully moved to implementation-history/:');
movedImpl.forEach(f => console.log(`  - ${f}`));

console.log('\n✅ Successfully moved to deprecated/:');
movedDep.forEach(f => console.log(`  - ${f}`));

if (errors.length > 0) {
    console.log('\n⚠️ Errors:');
    errors.forEach(e => console.log(`  - ${e}`));
}

console.log('\n📁 Contents of implementation-history/:');
fs.readdirSync(implHistoryDir).forEach(f => console.log(`  - ${f}`));

console.log('\n📁 Contents of deprecated/:');
fs.readdirSync(deprecatedDir).forEach(f => console.log(`  - ${f}`));
