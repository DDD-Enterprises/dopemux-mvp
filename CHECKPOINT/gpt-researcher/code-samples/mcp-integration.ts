/**
 * MCP Integration patterns for GPT-Researcher in Dopemux
 *
 * This shows how to integrate the gptr-mcp server with Dopemux's MCP infrastructure
 */

import { MCPClient } from '@dopemux/mcp-client';

// MCP Tool interfaces for GPT-Researcher
interface QuickSearchArgs {
  query: string;
  max_results?: number;
}

interface DeepResearchArgs {
  query: string;
  report_type?: 'basic' | 'detailed' | 'deep';
  depth?: number;
  breadth?: number;
}

interface WriteReportArgs {
  context: string;
  report_type?: 'markdown' | 'pdf' | 'docx';
  tone?: 'professional' | 'casual' | 'academic';
}

interface ResearchResourceArgs {
  url: string;
  extract_content?: boolean;
}

// Dopemux MCP Research Client
export class DopemuxResearchClient {
  private mcpClient: MCPClient;
  private serverName = 'gpt-researcher';

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
  }

  /**
   * Quick search for immediate insights (5-10 seconds)
   */
  async quickSearch(query: string, maxResults: number = 10): Promise<SearchResult[]> {
    try {
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'quick_search',
        arguments: {
          query,
          max_results: maxResults
        } as QuickSearchArgs
      });

      return this.parseSearchResults(result);
    } catch (error) {
      throw new ResearchError(`Quick search failed: ${error.message}`, 'QUICK_SEARCH_ERROR');
    }
  }

  /**
   * Deep research with tree exploration (3-7 minutes)
   */
  async deepResearch(
    query: string,
    options: {
      reportType?: 'basic' | 'detailed' | 'deep';
      depth?: number;
      breadth?: number;
      onProgress?: (progress: ResearchProgress) => void;
    } = {}
  ): Promise<DeepResearchResult> {
    try {
      // Start deep research
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'deep_research',
        arguments: {
          query,
          report_type: options.reportType || 'detailed',
          depth: options.depth || 3,
          breadth: options.breadth || 5
        } as DeepResearchArgs
      });

      return this.parseDeepResearchResult(result);
    } catch (error) {
      throw new ResearchError(`Deep research failed: ${error.message}`, 'DEEP_RESEARCH_ERROR');
    }
  }

  /**
   * Research specific web resource
   */
  async researchResource(url: string, extractContent: boolean = true): Promise<ResourceResult> {
    try {
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'research_resource',
        arguments: {
          url,
          extract_content: extractContent
        } as ResearchResourceArgs
      });

      return this.parseResourceResult(result);
    } catch (error) {
      throw new ResearchError(`Resource research failed: ${error.message}`, 'RESOURCE_ERROR');
    }
  }

  /**
   * Generate formatted report from research context
   */
  async writeReport(
    context: string,
    options: {
      reportType?: 'markdown' | 'pdf' | 'docx';
      tone?: 'professional' | 'casual' | 'academic';
    } = {}
  ): Promise<ReportResult> {
    try {
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'write_report',
        arguments: {
          context,
          report_type: options.reportType || 'markdown',
          tone: options.tone || 'professional'
        } as WriteReportArgs
      });

      return this.parseReportResult(result);
    } catch (error) {
      throw new ResearchError(`Report generation failed: ${error.message}`, 'REPORT_ERROR');
    }
  }

  /**
   * Get research sources and citations
   */
  async getResearchSources(researchId: string): Promise<ResearchSource[]> {
    try {
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'get_research_sources',
        arguments: { research_id: researchId }
      });

      return this.parseResearchSources(result);
    } catch (error) {
      throw new ResearchError(`Failed to get sources: ${error.message}`, 'SOURCES_ERROR');
    }
  }

  /**
   * Get full research context
   */
  async getResearchContext(researchId: string, includeSources: boolean = true): Promise<ResearchContext> {
    try {
      const result = await this.mcpClient.callTool({
        server: this.serverName,
        tool: 'get_research_context',
        arguments: {
          research_id: researchId,
          include_sources: includeSources
        }
      });

      return this.parseResearchContext(result);
    } catch (error) {
      throw new ResearchError(`Failed to get context: ${error.message}`, 'CONTEXT_ERROR');
    }
  }

  // Result parsing methods
  private parseSearchResults(result: any): SearchResult[] {
    if (!result.content || !Array.isArray(result.content)) {
      return [];
    }

    return result.content.map((item: any) => ({
      title: item.title || 'Untitled',
      url: item.href || item.url || '#',
      snippet: item.body || item.content || '',
      relevance: item.relevance || 0.5
    }));
  }

  private parseDeepResearchResult(result: any): DeepResearchResult {
    return {
      id: result.research_id || this.generateId(),
      query: result.query || '',
      report: result.report || '',
      sources: this.parseResearchSources(result.sources || []),
      context: result.context || [],
      metadata: {
        timeSpent: result.time_spent || 0,
        cost: result.cost || 0,
        depth: result.depth || 0,
        breadth: result.breadth || 0
      }
    };
  }

  private parseResourceResult(result: any): ResourceResult {
    return {
      url: result.url || '',
      title: result.title || 'Untitled',
      content: result.content || '',
      metadata: {
        wordCount: result.word_count || 0,
        lastModified: result.last_modified ? new Date(result.last_modified) : new Date(),
        contentType: result.content_type || 'text/html'
      }
    };
  }

  private parseReportResult(result: any): ReportResult {
    return {
      content: result.content || '',
      format: result.format || 'markdown',
      metadata: {
        wordCount: result.word_count || 0,
        generatedAt: new Date(),
        sections: result.sections || []
      }
    };
  }

  private parseResearchSources(sources: any): ResearchSource[] {
    if (!Array.isArray(sources)) return [];

    return sources.map((source: any) => ({
      url: source.url || source.href || '',
      title: source.title || 'Untitled',
      snippet: source.snippet || source.body || '',
      relevance: source.relevance || 0.5,
      accessedAt: source.accessed_at ? new Date(source.accessed_at) : new Date()
    }));
  }

  private parseResearchContext(result: any): ResearchContext {
    return {
      id: result.id || this.generateId(),
      query: result.query || '',
      findings: result.findings || [],
      sources: this.parseResearchSources(result.sources || []),
      timeline: result.timeline || [],
      metadata: result.metadata || {}
    };
  }

  private generateId(): string {
    return `research-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// ADHD-Optimized Research Workflows
export class ADHDResearchWorkflows {
  constructor(private researchClient: DopemuxResearchClient) {}

  /**
   * Quick insight workflow (5 minutes)
   */
  async quickInsight(query: string): Promise<QuickInsightResult> {
    const startTime = Date.now();

    try {
      // Quick search for immediate results
      const searchResults = await this.researchClient.quickSearch(query, 5);

      // Generate quick summary
      const context = searchResults.map(r => `${r.title}: ${r.snippet}`).join('\n\n');
      const report = await this.researchClient.writeReport(context, {
        reportType: 'markdown',
        tone: 'professional'
      });

      const duration = (Date.now() - startTime) / 1000 / 60; // minutes

      return {
        query,
        summary: report.content,
        sources: searchResults,
        timeSpent: duration,
        type: 'quick_insight'
      };
    } catch (error) {
      throw new ResearchError(`Quick insight failed: ${error.message}`, 'WORKFLOW_ERROR');
    }
  }

  /**
   * Focused chunk workflow (25 minutes)
   */
  async focusedChunk(
    query: string,
    onProgress?: (progress: WorkflowProgress) => void
  ): Promise<FocusedChunkResult> {
    const startTime = Date.now();

    try {
      // Progress callback wrapper
      const progressWrapper = (progress: ResearchProgress) => {
        if (onProgress) {
          onProgress({
            stage: 'research',
            progress: progress.progress,
            currentActivity: progress.currentActivity,
            timeElapsed: (Date.now() - startTime) / 1000 / 60
          });
        }
      };

      // Phase 1: Deep research (20 minutes)
      onProgress?.({
        stage: 'research',
        progress: 0,
        currentActivity: 'Starting deep research',
        timeElapsed: 0
      });

      const researchResult = await this.researchClient.deepResearch(query, {
        reportType: 'detailed',
        onProgress: progressWrapper
      });

      // Phase 2: Report generation (5 minutes)
      onProgress?.({
        stage: 'synthesis',
        progress: 80,
        currentActivity: 'Generating final report',
        timeElapsed: (Date.now() - startTime) / 1000 / 60
      });

      const duration = (Date.now() - startTime) / 1000 / 60;

      // Suggest break if chunk took longer than 30 minutes
      const suggestBreak = duration > 30;

      return {
        query,
        research: researchResult,
        timeSpent: duration,
        type: 'focused_chunk',
        suggestBreak,
        nextActions: this.generateNextActions(researchResult)
      };
    } catch (error) {
      throw new ResearchError(`Focused chunk failed: ${error.message}`, 'WORKFLOW_ERROR');
    }
  }

  /**
   * Comparative analysis workflow
   */
  async comparativeAnalysis(
    subjects: string[],
    context: string,
    onProgress?: (progress: WorkflowProgress) => void
  ): Promise<ComparativeAnalysisResult> {
    const startTime = Date.now();
    const totalSteps = subjects.length + 1; // research each subject + comparison
    let currentStep = 0;

    try {
      const results: DeepResearchResult[] = [];

      // Research each subject
      for (const subject of subjects) {
        currentStep++;
        onProgress?.({
          stage: 'research',
          progress: (currentStep / totalSteps) * 80,
          currentActivity: `Researching ${subject}`,
          timeElapsed: (Date.now() - startTime) / 1000 / 60
        });

        const result = await this.researchClient.deepResearch(
          `${subject} in the context of ${context}`,
          { reportType: 'detailed' }
        );
        results.push(result);
      }

      // Generate comparative analysis
      currentStep++;
      onProgress?.({
        stage: 'synthesis',
        progress: 90,
        currentActivity: 'Generating comparative analysis',
        timeElapsed: (Date.now() - startTime) / 1000 / 60
      });

      const combinedContext = results.map(r => r.report).join('\n\n---\n\n');
      const comparativeReport = await this.researchClient.writeReport(
        `Comparative analysis of: ${subjects.join(', ')}\n\n${combinedContext}`,
        { tone: 'professional' }
      );

      const duration = (Date.now() - startTime) / 1000 / 60;

      return {
        subjects,
        context,
        individualResults: results,
        comparativeReport: comparativeReport.content,
        timeSpent: duration,
        type: 'comparative_analysis'
      };
    } catch (error) {
      throw new ResearchError(`Comparative analysis failed: ${error.message}`, 'WORKFLOW_ERROR');
    }
  }

  private generateNextActions(research: DeepResearchResult): string[] {
    // Generate suggested next actions based on research results
    const actions = [
      'Review key findings and take notes',
      'Explore related topics mentioned in the research'
    ];

    if (research.sources.length > 5) {
      actions.push('Deep dive into most relevant sources');
    }

    if (research.metadata.cost > 0.5) {
      actions.push('Take a break before continuing research');
    }

    return actions.slice(0, 3); // ADHD: Max 3 options
  }
}

// Type definitions
interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  relevance: number;
}

interface DeepResearchResult {
  id: string;
  query: string;
  report: string;
  sources: ResearchSource[];
  context: any[];
  metadata: {
    timeSpent: number;
    cost: number;
    depth: number;
    breadth: number;
  };
}

interface ResourceResult {
  url: string;
  title: string;
  content: string;
  metadata: {
    wordCount: number;
    lastModified: Date;
    contentType: string;
  };
}

interface ReportResult {
  content: string;
  format: string;
  metadata: {
    wordCount: number;
    generatedAt: Date;
    sections: string[];
  };
}

interface ResearchSource {
  url: string;
  title: string;
  snippet: string;
  relevance: number;
  accessedAt: Date;
}

interface ResearchContext {
  id: string;
  query: string;
  findings: any[];
  sources: ResearchSource[];
  timeline: any[];
  metadata: any;
}

interface ResearchProgress {
  progress: number;
  currentActivity: string;
  timeElapsed?: number;
}

interface WorkflowProgress {
  stage: 'research' | 'synthesis' | 'complete';
  progress: number;
  currentActivity: string;
  timeElapsed: number;
}

interface QuickInsightResult {
  query: string;
  summary: string;
  sources: SearchResult[];
  timeSpent: number;
  type: 'quick_insight';
}

interface FocusedChunkResult {
  query: string;
  research: DeepResearchResult;
  timeSpent: number;
  type: 'focused_chunk';
  suggestBreak: boolean;
  nextActions: string[];
}

interface ComparativeAnalysisResult {
  subjects: string[];
  context: string;
  individualResults: DeepResearchResult[];
  comparativeReport: string;
  timeSpent: number;
  type: 'comparative_analysis';
}

// Custom error class
class ResearchError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'ResearchError';
  }
}

export {
  SearchResult,
  DeepResearchResult,
  ResourceResult,
  ReportResult,
  ResearchSource,
  ResearchContext,
  ResearchProgress,
  WorkflowProgress,
  QuickInsightResult,
  FocusedChunkResult,
  ComparativeAnalysisResult,
  ResearchError
};