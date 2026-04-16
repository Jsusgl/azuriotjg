import os
import importlib
import sys
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PluginManager")

class PluginManager:
    def __init__(self, plugin_dir='plugins'):
        self.plugin_dir = plugin_dir
        self.plugins = {}
        self.plugin_instances = {}
        self.lock = threading.Lock()
        
        # Ensure plugin dir is in path
        abs_plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), plugin_dir))
        if abs_plugin_dir not in sys.path:
            sys.path.insert(0, abs_plugin_dir)

    def discover_plugins(self):
        """Finds all python files in the plugin directory"""
        discovered = []
        abs_plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), self.plugin_dir))
        if not os.path.exists(abs_plugin_dir):
            os.makedirs(abs_plugin_dir, exist_ok=True)
            
        for d in os.listdir(abs_plugin_dir):
            if d.endswith('.py') and not d.startswith('__'):
                plugin_name = d[:-3]
                discovered.append(plugin_name)
        return discovered

    def load_plugin(self, plugin_name):
        with self.lock:
            try:
                if plugin_name in self.plugins:
                    importlib.reload(self.plugins[plugin_name])
                else:
                    self.plugins[plugin_name] = importlib.import_module(plugin_name)
                
                # Assume each plugin has a `setup(plugin_manager)` function
                if hasattr(self.plugins[plugin_name], 'setup'):
                    instance = self.plugins[plugin_name].setup(self)
                    self.plugin_instances[plugin_name] = instance
                    logger.info(f"Plugin loaded: {plugin_name}")
                    return True
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                
            return False

    def unload_plugin(self, plugin_name):
        with self.lock:
            try:
                if plugin_name in self.plugin_instances:
                    instance = self.plugin_instances[plugin_name]
                    if hasattr(instance, 'teardown'):
                        instance.teardown()
                    del self.plugin_instances[plugin_name]
                    logger.info(f"Plugin unloaded: {plugin_name}")
                    return True
            except Exception as e:
                logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def get_plugin(self, plugin_name):
        return self.plugin_instances.get(plugin_name)

    def get_all_status(self):
        status = []
        discovered = self.discover_plugins()
        with self.lock:
            for p in discovered:
                instance = self.plugin_instances.get(p)
                
                p_module = self.plugins.get(p)
                if not p_module:
                    try:
                        p_module = importlib.import_module(p)
                        # We don't save it to self.plugins to avoid keeping it fully active if it wasn't loaded via load_plugin
                    except Exception:
                        pass
                
                human_name = getattr(p_module, 'PLUGIN_NAME', p.replace('_', ' ').title()) if p_module else p.replace('_', ' ').title()
                version = getattr(p_module, 'PLUGIN_VERSION', '1.0.0') if p_module else '1.0.0'
                
                if instance:
                    # plugin is loaded/active
                    p_status = instance.get_status() if hasattr(instance, 'get_status') else "unknown"
                    state = "active"
                else:
                    p_status = "offline"
                    state = "inactive"
                
                status.append({
                    "name": p,
                    "human_name": human_name,
                    "version": version,
                    "state": state,
                    "status_detail": p_status
                })
        return status
