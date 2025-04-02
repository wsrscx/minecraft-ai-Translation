import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import json
import zipfile
import shutil
import re
from pathlib import Path

from minecraft_translator import MinecraftTranslator
from config import Config

class MinecraftTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft 自动汉化工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 加载配置
        self.config = Config()
        
        # 初始化翻译器
        api_url = self.config.get_api_url()
        api_key = self.config.get("api_key", "") if self.config.get("use_api_key", False) else None
        model = self.config.get("model", "qwen2.5:1.5b")
        
        self.translator = MinecraftTranslator(
            api_url=api_url,
            api_key=api_key,
            model=model
        )
        
        self.setup_ui()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡
        tab_control = ttk.Notebook(main_frame)
        
        # MOD汉化选项卡
        mod_tab = ttk.Frame(tab_control)
        tab_control.add(mod_tab, text="MOD汉化")
        
        # MC版本汉化选项卡
        mc_tab = ttk.Frame(tab_control)
        tab_control.add(mc_tab, text="MC版本汉化")
        
        # 设置选项卡
        settings_tab = ttk.Frame(tab_control)
        tab_control.add(settings_tab, text="设置")
        
        tab_control.pack(expand=True, fill=tk.BOTH)
        
        # 设置MOD汉化选项卡内容
        self.setup_mod_tab(mod_tab)
        
        # 设置MC版本汉化选项卡内容
        self.setup_mc_tab(mc_tab)
        
        # 设置设置选项卡内容
        self.setup_settings_tab(settings_tab)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    
    def setup_mod_tab(self, parent):
        # MOD文件选择
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(file_frame, text="MOD文件:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mod_path_var = tk.StringVar()
        mod_entry = ttk.Entry(file_frame, textvariable=self.mod_path_var, width=50)
        mod_entry.grid(row=0, column=1, padx=5, pady=5)
        
        browse_button = ttk.Button(file_frame, text="浏览...", command=self.browse_mod_file)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 支持的MOD类型
        mod_type_frame = ttk.LabelFrame(parent, text="MOD类型")
        mod_type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mod_type_var = tk.StringVar(value="auto")
        ttk.Radiobutton(mod_type_frame, text="自动检测", variable=self.mod_type_var, value="auto").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mod_type_frame, text="Fabric", variable=self.mod_type_var, value="fabric").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mod_type_frame, text="Forge", variable=self.mod_type_var, value="forge").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mod_type_frame, text="NeoForge", variable=self.mod_type_var, value="neoforge").pack(anchor=tk.W, padx=5, pady=2)
        
        # 翻译选项
        options_frame = ttk.LabelFrame(parent, text="翻译选项")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.translate_desc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译描述文本", variable=self.translate_desc_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.translate_tooltip_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译提示文本", variable=self.translate_tooltip_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.translate_gui_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译界面文本", variable=self.translate_gui_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # 开始翻译按钮
        start_button = ttk.Button(parent, text="开始汉化", command=self.start_mod_translation)
        start_button.pack(pady=10)
    
    def setup_mc_tab(self, parent):
        # MC版本文件夹选择
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(folder_frame, text="MC版本文件夹:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.mc_path_var = tk.StringVar()
        mc_entry = ttk.Entry(folder_frame, textvariable=self.mc_path_var, width=50)
        mc_entry.grid(row=0, column=1, padx=5, pady=5)
        
        browse_button = ttk.Button(folder_frame, text="浏览...", command=self.browse_mc_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 翻译选项
        options_frame = ttk.LabelFrame(parent, text="翻译选项")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.translate_items_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译物品名称", variable=self.translate_items_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.translate_entities_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译实体名称", variable=self.translate_entities_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.translate_advancements_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译进度文本", variable=self.translate_advancements_var).pack(anchor=tk.W, padx=5, pady=2)
        
        self.translate_misc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="翻译其他文本", variable=self.translate_misc_var).pack(anchor=tk.W, padx=5, pady=2)
        
        # 开始翻译按钮
        start_button = ttk.Button(parent, text="开始汉化", command=self.start_mc_translation)
        start_button.pack(pady=10)
    
    def setup_settings_tab(self, parent):
        # API设置框架
        settings_frame = ttk.LabelFrame(parent, text="Ollama API设置")
        settings_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # API地址
        api_host_frame = ttk.Frame(settings_frame)
        api_host_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_host_frame, text="API地址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_host_var = tk.StringVar(value=self.config.get("api_url", "http://localhost"))
        api_host_entry = ttk.Entry(api_host_frame, textvariable=self.api_host_var, width=40)
        api_host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # API端口
        api_port_frame = ttk.Frame(settings_frame)
        api_port_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_port_frame, text="API端口:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_port_var = tk.StringVar(value=self.config.get("api_port", "11434"))
        api_port_entry = ttk.Entry(api_port_frame, textvariable=self.api_port_var, width=10)
        api_port_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 模型名称
        model_frame = ttk.Frame(settings_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="模型名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.model_var = tk.StringVar(value=self.config.get("model", "qwen2.5:1.5b"))
        model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=30)
        model_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # API密钥（带复选框）
        api_key_frame = ttk.Frame(settings_frame)
        api_key_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.use_api_key_var = tk.BooleanVar(value=self.config.get("use_api_key", False))
        use_api_key_cb = ttk.Checkbutton(api_key_frame, text="使用API密钥", variable=self.use_api_key_var, command=self.toggle_api_key)
        use_api_key_cb.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.api_key_var = tk.StringVar(value=self.config.get("api_key", ""))
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key_var, width=40, state="disabled" if not self.use_api_key_var.get() else "normal")
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 保存设置按钮
        save_button = ttk.Button(parent, text="保存设置", command=self.save_settings)
        save_button.pack(pady=10)
        
        # 测试连接按钮
        test_button = ttk.Button(parent, text="测试连接", command=self.test_connection)
        test_button.pack(pady=5)
    
    def browse_mod_file(self):
        file_path = filedialog.askopenfilename(
            title="选择MOD文件",
            filetypes=[("JAR文件", "*.jar"), ("所有文件", "*.*")]
        )
        if file_path:
            self.mod_path_var.set(file_path)
            self.log(f"已选择MOD文件: {file_path}")
    
    def browse_mc_folder(self):
        folder_path = filedialog.askdirectory(title="选择MC版本文件夹")
        if folder_path:
            self.mc_path_var.set(folder_path)
            self.log(f"已选择MC版本文件夹: {folder_path}")
    
    def start_mod_translation(self):
        mod_path = self.mod_path_var.get()
        if not mod_path or not os.path.exists(mod_path):
            messagebox.showerror("错误", "请选择有效的MOD文件")
            return
        
        # 获取MOD类型
        mod_type = self.mod_type_var.get()
        
        # 获取翻译选项
        options = {
            "translate_desc": self.translate_desc_var.get(),
            "translate_tooltip": self.translate_tooltip_var.get(),
            "translate_gui": self.translate_gui_var.get()
        }
        
        # 在新线程中启动翻译，避免UI卡顿
        self.status_var.set("正在汉化MOD...")
        self.progress_var.set(0)
        
        threading.Thread(
            target=self.run_mod_translation,
            args=(mod_path, mod_type, options),
            daemon=True
        ).start()
    
    def run_mod_translation(self, mod_path, mod_type, options):
        try:
            self.log(f"开始汉化MOD: {os.path.basename(mod_path)}")
            self.log(f"MOD类型: {mod_type if mod_type != 'auto' else '自动检测'}")
            
            # 调用翻译器进行翻译
            output_path = self.translator.translate_mod(
                mod_path=mod_path,
                mod_type=mod_type,
                options=options,
                progress_callback=self.update_progress
            )
            
            self.log(f"汉化完成! 输出文件: {output_path}")
            self.status_var.set("汉化完成")
            self.progress_var.set(100)
            
            # 显示成功消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"MOD汉化完成!\n输出文件: {output_path}"))
        
        except Exception as e:
            error_msg = str(e)
            self.log(f"汉化过程中出错: {error_msg}")
            self.status_var.set("汉化失败")
            self.root.after(0, lambda error=error_msg: messagebox.showerror("错误", f"汉化过程中出错: {error}"))
    
    def start_mc_translation(self):
        mc_path = self.mc_path_var.get()
        if not mc_path or not os.path.exists(mc_path):
            messagebox.showerror("错误", "请选择有效的MC版本文件夹")
            return
        
        # 获取翻译选项
        options = {
            "translate_items": self.translate_items_var.get(),
            "translate_entities": self.translate_entities_var.get(),
            "translate_advancements": self.translate_advancements_var.get(),
            "translate_misc": self.translate_misc_var.get()
        }
        
        # 在新线程中启动翻译，避免UI卡顿
        self.status_var.set("正在汉化MC版本...")
        self.progress_var.set(0)
        
        threading.Thread(
            target=self.run_mc_translation,
            args=(mc_path, options),
            daemon=True
        ).start()
    
    def run_mc_translation(self, mc_path, options):
        try:
            self.log(f"开始汉化MC版本: {os.path.basename(mc_path)}")
            
            # 调用翻译器进行翻译
            output_path = self.translator.translate_minecraft(
                mc_path=mc_path,
                options=options,
                progress_callback=self.update_progress
            )
            
            self.log(f"汉化完成! 输出资源包: {output_path}")
            self.status_var.set("汉化完成")
            self.progress_var.set(100)
            
            # 显示成功消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"MC版本汉化完成!\n输出资源包: {output_path}"))
        
        except Exception as e:
            error_msg = str(e)
            self.log(f"汉化过程中出错: {error_msg}")
            self.status_var.set("汉化失败")
            self.root.after(0, lambda error=error_msg: messagebox.showerror("错误", f"汉化过程中出错: {error}"))
    
    def update_progress(self, progress, message=None):
        self.progress_var.set(progress)
        if message:
            self.log(message)
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        print(message)
    
    def toggle_api_key(self):
        """切换API密钥输入框的状态"""
        if self.use_api_key_var.get():
            self.api_key_entry.config(state="normal")
        else:
            self.api_key_entry.config(state="disabled")
    
    def save_settings(self):
        """保存设置到配置文件"""
        try:
            # 获取设置值
            api_url = self.api_host_var.get().strip()
            api_port = self.api_port_var.get().strip()
            model = self.model_var.get().strip()
            use_api_key = self.use_api_key_var.get()
            api_key = self.api_key_var.get().strip() if use_api_key else ""
            
            # 验证输入
            if not api_url:
                messagebox.showerror("错误", "API地址不能为空")
                return
            
            if not api_port.isdigit():
                messagebox.showerror("错误", "API端口必须是数字")
                return
            
            if not model:
                messagebox.showerror("错误", "模型名称不能为空")
                return
            
            if use_api_key and not api_key:
                messagebox.showerror("错误", "启用API密钥后，密钥不能为空")
                return
            
            # 保存到配置
            self.config.set("api_url", api_url)
            self.config.set("api_port", api_port)
            self.config.set("model", model)
            self.config.set("use_api_key", use_api_key)
            self.config.set("api_key", api_key)
            
            # 更新翻译器
            self.translator.api_url = self.config.get_api_url()
            self.translator.api_key = api_key if use_api_key else None
            self.translator.model = model
            
            self.log("设置已保存")
            messagebox.showinfo("成功", "设置已保存")
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"保存设置时出错: {error_msg}")
            messagebox.showerror("错误", f"保存设置时出错: {error_msg}")
    
    def test_connection(self):
        """测试与Ollama API的连接"""
        try:
            # 获取当前设置
            api_url = self.config.get_api_url()
            api_key = self.api_key_var.get().strip() if self.use_api_key_var.get() else None
            model = self.model_var.get().strip()
            
            self.log(f"正在测试连接: {api_url}")
            self.status_var.set("正在测试连接...")
            
            # 在新线程中测试连接，避免UI卡顿
            threading.Thread(
                target=self._run_connection_test,
                args=(api_url, api_key, model),
                daemon=True
            ).start()
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"测试连接时出错: {error_msg}")
            self.status_var.set("连接测试失败")
            messagebox.showerror("错误", f"测试连接时出错: {error_msg}")
    
    def _run_connection_test(self, api_url, api_key, model):
        """在后台线程中运行连接测试"""
        try:
            # 准备请求头
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # 准备请求数据 - 简单的测试提示
            data = {
                "model": model,
                "prompt": "你好",
                "stream": False
            }
            
            # 发送请求
            import requests
            response = requests.post(api_url, headers=headers, json=data, timeout=10)
            
            # 检查响应
            if response.status_code == 200:
                self.log("连接测试成功！")
                self.status_var.set("连接测试成功")
                self.root.after(0, lambda: messagebox.showinfo("成功", "连接测试成功！Ollama API可以正常访问。"))
            else:
                error_msg = f"API返回错误: {response.status_code} - {response.text[:200]}"
                self.log(error_msg)
                self.status_var.set("连接测试失败")
                self.root.after(0, lambda: messagebox.showerror("错误", f"连接测试失败: {error_msg}"))
                
        except Exception as e:
            error_msg = str(e)
            self.log(f"连接测试失败: {error_msg}")
            self.status_var.set("连接测试失败")
            self.root.after(0, lambda: messagebox.showerror("错误", f"连接测试失败: {error_msg}"))

def main():
    root = tk.Tk()
    app = MinecraftTranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()