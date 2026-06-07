from pathlib import Path


def test_readme_positions_project_as_deliverable_system():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "可交付项目" in readme
    assert "生产化延展" in readme
    assert "需要填写的信息" in readme
    assert "Windows 快速启动" in readme
    assert "Inter" + "view " + "De" + "mo" not in readme
    assert "面" + "试" + "演" + "示" not in readme


def test_operation_guide_describes_delivery_runtime():
    guide = Path("docs/operation-guide.md").read_text(encoding="utf-8")

    assert "交付运行指南" in guide
    assert "配置 API Key" in guide
    assert "启动服务" in guide
    assert "验收标准" in guide
