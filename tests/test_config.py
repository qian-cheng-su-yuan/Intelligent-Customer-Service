from intelligent_customer_service.config import Settings


def test_settings_defaults_to_qwen_dashscope_provider(tmp_path):
    settings = Settings(dashscope_api_key="sk-test", database_path=tmp_path / "service.db")

    assert settings.llm_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert settings.llm_model == "qwen-plus"
    assert settings.api_key == "sk-test"
    assert settings.database_path == tmp_path / "service.db"


def test_settings_requires_api_key_for_live_llm(tmp_path):
    settings = Settings(dashscope_api_key="", llm_api_key="", database_path=tmp_path / "service.db")

    assert settings.api_key == ""
