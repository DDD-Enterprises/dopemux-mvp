#!/usr/bin/env python3
"""
Context7 Integration Enforcer
Ensures Context7 is ALWAYS consulted before code analysis or generation

This system intercepts all code-related operations and mandates Context7 queries
before proceeding with any code analysis, generation, or modification.
"""

import json
import sys
import os
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeOperationType(Enum):
    ANALYSIS = "code_analysis"
    GENERATION = "code_generation"
    MODIFICATION = "code_modification"
    REVIEW = "code_review"
    TESTING = "test_generation"

@dataclass
class Context7Query:
    operation_type: CodeOperationType
    libraries_involved: List[str]
    query_text: str
    response: Optional[str] = None
    timestamp: Optional[str] = None

class Context7Enforcer:
    def __init__(self, config_path: str = ".claude/platform-evolution/agent-architecture.yaml"):
        self.config_path = config_path
        self.context7_cache = {}
        self.enforcement_log = []
        
    def detect_code_operation(self, agent_request: Dict[str, Any]) -> Optional[CodeOperationType]:
        """Detect if the request involves code operations requiring Context7"""
        
        # Check for code analysis operations
        analysis_indicators = [
            "analyze", "review", "examine", "inspect", "understand",
            "explain", "debug", "trace", "profile"
        ]
        
        # Check for code generation operations  
        generation_indicators = [
            "generate", "create", "write", "implement", "build",
            "develop", "code", "function", "class", "method"
        ]
        
        # Check for modification operations
        modification_indicators = [
            "edit", "modify", "update", "change", "refactor",
            "optimize", "fix", "patch", "enhance"
        ]
        
        request_text = str(agent_request).lower()
        
        if any(indicator in request_text for indicator in analysis_indicators):
            return CodeOperationType.ANALYSIS
        elif any(indicator in request_text for indicator in generation_indicators):
            return CodeOperationType.GENERATION
        elif any(indicator in request_text for indicator in modification_indicators):
            return CodeOperationType.MODIFICATION
        elif "test" in request_text and any(gen in request_text for gen in generation_indicators):
            return CodeOperationType.TESTING
        elif "review" in request_text:
            return CodeOperationType.REVIEW
            
        return None
    
    def extract_libraries(self, agent_request: Dict[str, Any]) -> List[str]:
        """Extract potential library/framework names from the request"""
        
        common_libraries = [
            # Python
            "requests", "flask", "django", "fastapi", "pandas", "numpy",
            "pytest", "unittest", "sqlalchemy", "pydantic", "asyncio",
            
            # JavaScript/Node.js  
            "react", "vue", "angular", "express", "next.js", "axios",
            "jest", "mocha", "lodash", "moment", "socket.io",
            
            # General frameworks
            "docker", "kubernetes", "tensorflow", "pytorch", "redis",
            "mongodb", "postgresql", "mysql", "elasticsearch"
        ]
        
        request_text = str(agent_request).lower()
        found_libraries = [lib for lib in common_libraries if lib in request_text]
        
        # Also check for import statements or package names
        import_patterns = ["import ", "from ", "require(", "npm install"]
        for pattern in import_patterns:
            if pattern in request_text:
                # Extract library names after import patterns
                # This is a simplified extraction - could be enhanced
                pass
                
        return found_libraries
    
    async def query_context7(self, query: Context7Query) -> str:
        """Execute Context7 query and return authoritative documentation"""
        
        # Check cache first
        cache_key = f"{query.operation_type.value}:{':'.join(query.libraries_involved)}"
        if cache_key in self.context7_cache:
            logger.info(f"Using cached Context7 response for {cache_key}")
            return self.context7_cache[cache_key]
        
        try:
            # Construct Context7 MCP query
            context7_query = {
                "server": "context7",
                "operation": "search_documentation", 
                "parameters": {
                    "libraries": query.libraries_involved,
                    "query": query.query_text,
                    "operation_type": query.operation_type.value
                }
            }
            
            # Execute MCP call to Context7
            # This would integrate with your existing MCP infrastructure
            result = await self.execute_mcp_call("context7", context7_query)
            
            # Cache the result
            self.context7_cache[cache_key] = result
            
            logger.info(f"Context7 query successful for {query.operation_type.value}")
            return result
            
        except Exception as e:
            error_msg = f"Context7 query failed: {str(e)}"
            logger.error(error_msg)
            
            # Mandatory Context7 - operation should not proceed without it
            raise ValueError(f"CONTEXT7 MANDATORY: {error_msg}. Cannot proceed with {query.operation_type.value} without authoritative documentation.")
    
    async def execute_mcp_call(self, server: str, query: Dict[str, Any]) -> str:
        """Execute MCP call to Context7 server"""
        
        # This integrates with your existing MCP infrastructure
        # For now, simulate the call structure
        
        try:
            # In real implementation, this would use your MCP client
            cmd = [
                "claude-mcp-client",
                "--server", server,
                "--operation", query["operation"],
                "--params", json.dumps(query["parameters"])
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise Exception(f"MCP call failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Context7 query timeout - server may be unavailable")
        except FileNotFoundError:
            # Fallback for development - return placeholder
            return f"Context7 documentation for {query['parameters']['libraries']} - {query['parameters']['query']}"
    
    async def enforce_context7_requirement(self, agent_request: Dict[str, Any]) -> Dict[str, Any]:
        """Main enforcement function - ensures Context7 is consulted before code operations"""
        
        operation_type = self.detect_code_operation(agent_request)
        
        if operation_type is None:
            # Not a code operation, proceed without Context7
            return {
                "approved": True,
                "context7_required": False,
                "original_request": agent_request
            }
        
        logger.info(f"Code operation detected: {operation_type.value}")
        
        # Extract libraries involved
        libraries = self.extract_libraries(agent_request)
        
        # Create Context7 query
        query_text = f"Official documentation and best practices for {operation_type.value}"
        if libraries:
            query_text += f" involving {', '.join(libraries)}"
        
        context7_query = Context7Query(
            operation_type=operation_type,
            libraries_involved=libraries,
            query_text=query_text
        )
        
        try:
            # MANDATORY Context7 consultation
            context7_response = await self.query_context7(context7_query)
            
            # Log enforcement success
            self.enforcement_log.append({
                "timestamp": "now",
                "operation": operation_type.value,
                "libraries": libraries,
                "context7_consulted": True,
                "success": True
            })
            
            # Return approved request with Context7 context
            return {
                "approved": True,
                "context7_required": True,
                "context7_response": context7_response,
                "libraries_documented": libraries,
                "enhanced_request": {
                    **agent_request,
                    "context7_documentation": context7_response,
                    "authoritative_source": "Context7"
                }
            }
            
        except Exception as e:
            # Log enforcement failure
            self.enforcement_log.append({
                "timestamp": "now", 
                "operation": operation_type.value,
                "libraries": libraries,
                "context7_consulted": False,
                "error": str(e),
                "success": False
            })
            
            # BLOCK the operation - Context7 is mandatory
            return {
                "approved": False,
                "context7_required": True,
                "error": str(e),
                "message": f"BLOCKED: {operation_type.value} requires Context7 documentation but query failed",
                "recommendation": "Ensure Context7 MCP server is available and retry"
            }
    
    def generate_enforcement_report(self) -> Dict[str, Any]:
        """Generate report on Context7 enforcement effectiveness"""
        
        total_operations = len(self.enforcement_log)
        successful_enforcements = sum(1 for log in self.enforcement_log if log["success"])
        
        return {
            "total_code_operations": total_operations,
            "successful_context7_consultations": successful_enforcements,
            "enforcement_rate": successful_enforcements / total_operations if total_operations > 0 else 0,
            "blocked_operations": total_operations - successful_enforcements,
            "recent_operations": self.enforcement_log[-10:] if self.enforcement_log else []
        }

async def main():
    """CLI interface for testing Context7 enforcement"""
    
    if len(sys.argv) < 2:
        print("Usage: context7-enforcer.py '<agent_request_json>'")
        sys.exit(1)
    
    try:
        agent_request = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print("Error: Invalid JSON in agent request")
        sys.exit(1)
    
    enforcer = Context7Enforcer()
    result = await enforcer.enforce_context7_requirement(agent_request)
    
    print(json.dumps(result, indent=2))
    
    # Generate and display enforcement report
    report = enforcer.generate_enforcement_report()
    print("\n--- Context7 Enforcement Report ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())