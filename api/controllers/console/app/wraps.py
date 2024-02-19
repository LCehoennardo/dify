from functools import wraps
from typing import Union, Optional, Callable

from controllers.console.app.error import AppNotFoundError
from core.entities.application_entities import AppMode
from extensions.ext_database import db
from libs.login import current_user
from models.model import App


def get_app_model(view: Optional[Callable] = None, *, mode: Union[AppMode, list[AppMode]] = None):
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(*args, **kwargs):
            if not kwargs.get('app_id'):
                raise ValueError('missing app_id in path parameters')

            app_id = kwargs.get('app_id')
            app_id = str(app_id)

            del kwargs['app_id']

            app_model = db.session.query(App).filter(
                App.id == app_id,
                App.tenant_id == current_user.current_tenant_id,
                App.status == 'normal'
            ).first()

            if not app_model:
                raise AppNotFoundError()

            app_mode = AppMode.value_of(app_model.mode)
            if mode is not None:
                if isinstance(mode, list):
                    modes = mode
                else:
                    modes = [mode]

                # [temp] if workflow is in the mode list, then completion should be in the mode list
                if AppMode.WORKFLOW in modes:
                    modes.append(AppMode.COMPLETION)

                if app_mode not in modes:
                    mode_values = {m.value for m in modes}
                    raise AppNotFoundError(f"App mode is not in the supported list: {mode_values}")

            kwargs['app_model'] = app_model

            return view_func(*args, **kwargs)
        return decorated_view

    if view is None:
        return decorator
    else:
        return decorator(view)
