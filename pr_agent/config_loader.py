import os
from os.path import abspath, dirname, join
from pathlib import Path
from typing import Optional, Dict, Any

from dynaconf import Dynaconf
from starlette_context import context

PR_AGENT_TOML_KEY = 'pr-agent'

# 定义 GitHub Actions Secret 的环境变量名称
GITHUB_SECRET_PREFIX = "PR_AGENT_"

def load_github_secrets() -> Dict[str, Any]:
    """
    从 GitHub Actions 的 Secret 中加载配置，并将 `__` 转换为分层字典结构。
    """
    secrets = {}
    for key, value in os.environ.items():
        if key.startswith(GITHUB_SECRET_PREFIX):
            # 去掉前缀，并将键转换为小写
            config_key = key[len(GITHUB_SECRET_PREFIX):].lower()

            # 将 `__` 替换为字典层级
            keys = config_key.split('__')
            current_dict = secrets
            for part in keys[:-1]:  # 遍历到倒数第二个部分
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # 最后一部分直接赋值
            current_dict[keys[-1]] = value
    return secrets

current_dir = dirname(abspath(__file__))
global_settings = Dynaconf(
    envvar_prefix=False,
    merge_enabled=True,
    settings_files=[join(current_dir, f) for f in [
        "settings/configuration.toml",
        "settings/ignore.toml",
        "settings/language_extensions.toml",
        "settings/pr_reviewer_prompts.toml",
        "settings/pr_questions_prompts.toml",
        "settings/pr_line_questions_prompts.toml",
        "settings/pr_description_prompts.toml",
        "settings/pr_code_suggestions_prompts.toml",
        "settings/pr_code_suggestions_reflect_prompts.toml",
        "settings/pr_sort_code_suggestions_prompts.toml",
        "settings/pr_information_from_user_prompts.toml",
        "settings/pr_update_changelog_prompts.toml",
        "settings/pr_custom_labels.toml",
        "settings/pr_add_docs.toml",
        "settings/custom_labels.toml",
        "settings/pr_help_prompts.toml",
        "settings/.secrets.toml",
        "settings_prod/.secrets.toml",
    ]]
)

# 加载 GitHub Actions Secret
github_secrets = load_github_secrets()
if github_secrets:
    print("Loaded GitHub Secrets:", github_secrets)
    global_settings.update(github_secrets)

def get_settings(use_context=False):
    """
    Retrieves the current settings.

    This function attempts to fetch the settings from the starlette_context's context object. If it fails,
    it defaults to the global settings defined outside of this function.

    Returns:
        Dynaconf: The current settings object, either from the context or the global default.
    """
    try:
        return context["settings"]
    except Exception:
        return global_settings


# Add local configuration from pyproject.toml of the project being reviewed
def _find_repository_root() -> Optional[Path]:
    """
    Identify project root directory by recursively searching for the .git directory in the parent directories.
    """
    cwd = Path.cwd().resolve()
    no_way_up = False
    while not no_way_up:
        no_way_up = cwd == cwd.parent
        if (cwd / ".git").is_dir():
            return cwd
        cwd = cwd.parent
    return None


def _find_pyproject() -> Optional[Path]:
    """
    Search for file pyproject.toml in the repository root.
    """
    repo_root = _find_repository_root()
    if repo_root:
        pyproject = repo_root / "pyproject.toml"
        return pyproject if pyproject.is_file() else None
    return None


pyproject_path = _find_pyproject()
if pyproject_path is not None:
    get_settings().load_file(pyproject_path, env=f'tool.{PR_AGENT_TOML_KEY}')
