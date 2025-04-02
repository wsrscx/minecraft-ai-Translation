import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        # 配置文件路径
        self.config_dir = os.path.join(os.path.expanduser("~"), ".minecraft_translator")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # 默认配置
        self.default_config = {
            "api_url": "http://localhost:11434/api/generate",
            "api_port": "11434",
            "model": "qwen2.5:1.5b",
            "api_key": "",
            "use_api_key": False
        }
        
        # 当前配置
        self.current_config = self.load_config()
    
    def load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 如果配置文件存在，则加载它
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 确保所有默认配置项都存在
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                # 创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
        except Exception as e:
            print(f"加载配置文件时出错: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self, config):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # 更新当前配置
            self.current_config = config
            return True
        except Exception as e:
            print(f"保存配置文件时出错: {str(e)}")
            return False
    
    def get(self, key, default=None):
        """获取配置项"""
        return self.current_config.get(key, default)
    
    def set(self, key, value):
        """设置配置项并保存"""
        self.current_config[key] = value
        return self.save_config(self.current_config)
    
    def get_api_url(self):
        """获取完整的API URL"""
        base_url = self.current_config.get("api_url", "http://localhost:11434/api/generate")
        
        # 如果URL中已经包含端口，则直接返回
        if "://" in base_url and ":" in base_url.split("://")[1].split("/")[0]:
            return base_url
        
        # 否则，添加端口
        port = self.current_config.get("api_port", "11434")
        if "://" in base_url:
            protocol, rest = base_url.split("://")
            host = rest.split("/")[0]
            path = "/".join(rest.split("/")[1:]) if "/" in rest else ""
            
            # 构建带端口的URL
            if path:
                return f"{protocol}://{host}:{port}/{path}"
            else:
                return f"{protocol}://{host}:{port}"
        else:
            return f"{base_url}:{port}"