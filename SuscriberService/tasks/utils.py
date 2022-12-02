import os

def get_from_env(envvar, desc="", default=None):
    if envvar not in os.environ:
        if default is None:
            raise ValueError(f"Variable de entorno '{envvar}' no encontrada: {desc}")
        else:
            return default
    return os.environ[envvar].strip()