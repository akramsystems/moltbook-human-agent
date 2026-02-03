"""
Tests for Moltbook Human-Agent Interface
"""
import pytest
import json
import os
import unittest.mock as mock
from unittest.mock import MagicMock

# Import the app module
import app as moltbook_app


class TestLoadApiKey:
    """Tests for load_api_key function"""

    def test_load_api_key_returns_empty_when_no_file(self, tmp_path, monkeypatch):
        """Should return empty string when config file doesn't exist"""
        fake_config = str(tmp_path / "nonexistent" / "credentials.json")
        monkeypatch.setattr(moltbook_app, 'CONFIG_FILE', fake_config)

        result = moltbook_app.load_api_key()
        assert result == ''

    def test_load_api_key_returns_key_when_exists(self, tmp_path, monkeypatch):
        """Should return api_key from config file when it exists"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "credentials.json"
        config_file.write_text(json.dumps({
            'api_key': 'moltbook_sk_test123',
            'agent_name': 'TestAgent'
        }))

        monkeypatch.setattr(moltbook_app, 'CONFIG_FILE', str(config_file))

        result = moltbook_app.load_api_key()
        assert result == 'moltbook_sk_test123'

    def test_load_api_key_handles_malformed_json(self, tmp_path, monkeypatch):
        """Should return empty string on malformed JSON"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "credentials.json"
        config_file.write_text("not valid json {{{")

        monkeypatch.setattr(moltbook_app, 'CONFIG_FILE', str(config_file))

        result = moltbook_app.load_api_key()
        assert result == ''


class TestSaveApiKey:
    """Tests for save_api_key function"""

    def test_save_api_key_creates_file(self, tmp_path, monkeypatch):
        """Should create config file with api key"""
        config_file = tmp_path / "moltbook" / "credentials.json"
        monkeypatch.setattr(moltbook_app, 'CONFIG_FILE', str(config_file))

        moltbook_app.save_api_key('moltbook_sk_newkey', 'NewAgent')

        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert data['api_key'] == 'moltbook_sk_newkey'
        assert data['agent_name'] == 'NewAgent'


class TestMoltbookRequest:
    """Tests for moltbook_request function"""

    def test_get_request_success(self):
        """Should make GET request with proper headers"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True, 'data': 'test'}

        with mock.patch('app.requests.get', return_value=mock_response) as mock_get:
            result = moltbook_app.moltbook_request('GET', '/test', 'test_api_key')

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == 'https://www.moltbook.com/api/v1/test'
            assert call_args[1]['headers']['Authorization'] == 'Bearer test_api_key'
            assert result == {'success': True, 'data': 'test'}

    def test_post_request_success(self):
        """Should make POST request with JSON body"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}

        with mock.patch('app.requests.post', return_value=mock_response) as mock_post:
            result = moltbook_app.moltbook_request('POST', '/posts', 'test_api_key', {'title': 'Test'})

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]['json'] == {'title': 'Test'}
            assert result == {'success': True}

    def test_request_handles_network_error(self):
        """Should return error dict on network failure"""
        import requests

        with mock.patch('app.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
            result = moltbook_app.moltbook_request('GET', '/test', 'test_key')

            assert 'error' in result
            assert 'Connection failed' in result['error']

    def test_unknown_method_returns_error(self):
        """Should return error for unknown HTTP method"""
        result = moltbook_app.moltbook_request('INVALID', '/test', 'test_key')

        assert 'error' in result
        assert 'Unknown method' in result['error']


class TestOutputLog:
    """Tests for output log functions"""

    def test_add_output_adds_entry(self):
        """Should add entry to output log"""
        moltbook_app.output_log.clear()

        moltbook_app.add_output("Test message", "info")

        assert len(moltbook_app.output_log) == 1
        assert moltbook_app.output_log[0]['text'] == "Test message"
        assert moltbook_app.output_log[0]['style'] == "info"

    def test_add_output_limits_entries(self):
        """Should keep only last 100 entries"""
        moltbook_app.output_log.clear()

        for i in range(110):
            moltbook_app.add_output(f"Message {i}", "info")

        assert len(moltbook_app.output_log) == 100
        assert moltbook_app.output_log[0]['text'] == "Message 10"


class TestCommandParsing:
    """Tests for command parsing in execute endpoint"""

    def setup_method(self):
        """Clear output log before each test"""
        moltbook_app.output_log.clear()

    def test_help_command(self, monkeypatch):
        """Should display help text"""
        monkeypatch.setattr(moltbook_app, 'load_api_key', lambda: 'test_key')

        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        response = client.post('/execute', data={'command': 'help'})

        assert response.status_code == 200
        assert any('Commands:' in entry['text'] for entry in moltbook_app.output_log)

    def test_empty_command_does_nothing(self, monkeypatch):
        """Should not add output for empty command"""
        monkeypatch.setattr(moltbook_app, 'load_api_key', lambda: 'test_key')

        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        initial_count = len(moltbook_app.output_log)
        response = client.post('/execute', data={'command': ''})

        assert response.status_code == 200
        assert len(moltbook_app.output_log) == initial_count

    def test_unknown_command_shows_error(self, monkeypatch):
        """Should show error for unknown command"""
        monkeypatch.setattr(moltbook_app, 'load_api_key', lambda: 'test_key')

        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        response = client.post('/execute', data={'command': 'unknowncmd123'})

        assert response.status_code == 200
        assert any('Unknown command' in entry['text'] for entry in moltbook_app.output_log)


@pytest.mark.integration
class TestIntegration:
    """Integration tests (require network access)"""

    def test_homepage_loads(self):
        """Should load homepage successfully"""
        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        response = client.get('/')

        assert response.status_code == 200
        assert 'Moltbook' in response.text

    def test_set_key_endpoint(self, tmp_path, monkeypatch):
        """Should save API key via form"""
        config_file = tmp_path / "moltbook" / "credentials.json"
        monkeypatch.setattr(moltbook_app, 'CONFIG_FILE', str(config_file))

        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        response = client.post('/set-key', data={'api_key': 'moltbook_sk_testkey'})

        assert response.status_code == 200
        assert config_file.exists()

    def test_clear_endpoint(self):
        """Should clear the terminal output"""
        moltbook_app.output_log.clear()
        moltbook_app.add_output("Test entry", "info")

        from starlette.testclient import TestClient
        client = TestClient(moltbook_app.app)

        response = client.post('/clear')

        assert response.status_code == 200
        # After clear, only "Terminal cleared." should remain
        assert len(moltbook_app.output_log) == 1
        assert 'cleared' in moltbook_app.output_log[0]['text'].lower()
