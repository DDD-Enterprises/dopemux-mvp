#!/usr/bin/env node
/**
 * CLI Entry Point for ConPort Knowledge Graph Terminal UI
 * Part of CONPORT-KG-2025 Phase 9
 *
 * Usage:
 *   npm run dev    (development mode with tsx)
 *   npm start      (production mode with compiled JS)
 *
 * Environment:
 *   KG_API_URL - Integration Bridge URL (default: http://localhost:3016/kg)
 */

import React from 'react';
import {render} from 'ink';
import {App} from './App.js';

// Render the terminal UI
render(<App />);
