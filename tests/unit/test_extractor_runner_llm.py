import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from dopemux.extractor.runner import PipelineRunner

@pytest.fixture
def runner(tmp_path):
    # Setup extractor service dir with some dummy prompts
    extractor_dir = tmp_path / 'services' / 'repo-truth-extractor'
    extractor_dir.mkdir(parents=True)
    (extractor_dir / 'PHASE_A_REPO_CONTROL_PLANE.md').write_text('Prompt A')
    
    output_dir = tmp_path / 'out'
    output_dir.mkdir()
    
    # Mock ContextGatherer
    with patch('dopemux.extractor.runner.ContextGatherer') as mock_gatherer:
        mock_gatherer.return_value.get_context_for_phase.return_value = 'Context content'
        return PipelineRunner(
            project_root=tmp_path,
            output_dir=output_dir
        )

def test_run_phase_llm_success(runner):
    with patch('litellm.completion') as mock_completion:
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'LLM Response Content'
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response
        
        runner.run_phase('A', dry_run=False)
        
        response_file = runner.output_dir / 'PHASE_A_REPO_CONTROL_PLANE_RESPONSE.md'
        assert response_file.exists()
        assert response_file.read_text() == 'LLM Response Content'
        
        trace_file = runner.output_dir / 'PHASE_A_REPO_CONTROL_PLANE_TRACE.md'
        assert trace_file.exists()
        assert 'Prompt A' in trace_file.read_text()
        assert 'Context content' in trace_file.read_text()

def test_run_phase_llm_fallback_text(runner):
    with patch('litellm.completion') as mock_completion:
        mock_response = MagicMock()
        mock_choice = MagicMock()
        # Mock choice without message attribute
        mock_choice.configure_mock(**{'message.content': None})
        del mock_choice.message
        mock_choice.text = 'Legacy LLM Response'
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response
        
        runner.run_phase('A', dry_run=False)
        
        response_file = runner.output_dir / 'PHASE_A_REPO_CONTROL_PLANE_RESPONSE.md'
        assert response_file.exists()
        assert response_file.read_text() == 'Legacy LLM Response'

def test_run_phase_llm_exception_fallback(runner):
    with patch('litellm.completion', side_effect=Exception('API Error')):
        # Should not raise
        runner.run_phase('A', dry_run=False)
        
        # Should have generated trace file
        trace_file = runner.output_dir / 'PHASE_A_REPO_CONTROL_PLANE_TRACE.md'
        assert trace_file.exists()
        assert 'Prompt A' in trace_file.read_text()
