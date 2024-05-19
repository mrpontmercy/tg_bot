from typing import Any
import jinja2

from config import TEMPLATE_DIR


def render_template(template_name: str, data: dict | None = None):
    if data is None:
        data = {}

    template = _template_env().get_template(template_name)
    render = template.render(**data).replace("<br>", "\n")
    return render


def _template_env():
    if not getattr(_template_env, "template_env", None):
        loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
        env = jinja2.Environment(
            loader=loader,
            trim_blocks=True,
            autoescape=True,
            lstrip_blocks=True,
        )
        _template_env.template_env = env

    return _template_env.template_env
