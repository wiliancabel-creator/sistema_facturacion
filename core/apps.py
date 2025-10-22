from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'          # asegúrate de que coincide con INSTALLED_APPS
    label = 'core'

    def ready(self):
        # importa tu módulo de señales con ruta completa
        import core.signals
