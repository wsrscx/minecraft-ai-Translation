import os
import json
import zipfile
import shutil
import tempfile
import re
import requests
from pathlib import Path
from datetime import datetime

class MinecraftTranslator:
    def __init__(self, api_url, api_key, model):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.temp_dir = None
        self.progress_callback = None
    
    def translate_mod(self, mod_path, mod_type="auto", options=None, progress_callback=None):
        """
        翻译Minecraft MOD
        
        Args:
            mod_path: MOD的JAR文件路径
            mod_type: MOD类型 (auto, fabric, forge, neoforge)
            options: 翻译选项
            progress_callback: 进度回调函数
            
        Returns:
            输出的汉化MOD文件路径
        """
        self.progress_callback = progress_callback
        
        if options is None:
            options = {
                "translate_desc": True,
                "translate_tooltip": True,
                "translate_gui": True
            }
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="minecraft_translator_")
        self._update_progress(5, "创建临时工作目录")
        
        try:
            # 解压MOD文件
            extract_dir = os.path.join(self.temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            self._update_progress(10, f"解压MOD文件: {os.path.basename(mod_path)}")
            with zipfile.ZipFile(mod_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 检测MOD类型
            if mod_type == "auto":
                mod_type = self._detect_mod_type(extract_dir)
                self._update_progress(15, f"检测到MOD类型: {mod_type}")
            
            # 查找语言文件
            self._update_progress(20, "查找语言文件")
            lang_files = self._find_lang_files(extract_dir, mod_type)
            
            if not lang_files:
                raise Exception("未找到可翻译的语言文件")
            
            self._update_progress(25, f"找到 {len(lang_files)} 个语言文件")
            
            # 翻译语言文件
            translated_files = []
            total_files = len(lang_files)
            
            for i, lang_file in enumerate(lang_files):
                progress = 25 + (i / total_files) * 50
                self._update_progress(progress, f"翻译文件 ({i+1}/{total_files}): {os.path.basename(lang_file)}")
                
                # 创建中文语言文件路径
                zh_lang_file = self._get_zh_lang_path(lang_file)
                os.makedirs(os.path.dirname(zh_lang_file), exist_ok=True)
                
                # 翻译文件
                self._translate_lang_file(lang_file, zh_lang_file, options)
                translated_files.append(zh_lang_file)
            
            # 打包新的MOD文件
            self._update_progress(80, "打包汉化MOD文件")
            output_path = self._create_output_path(mod_path, "_汉化版")
            
            with zipfile.ZipFile(output_path, 'w') as zipf:
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, extract_dir)
                        zipf.write(file_path, arcname)
            
            self._update_progress(95, "汉化MOD文件打包完成")
            return output_path
            
        finally:
            # 清理临时目录
            self._update_progress(100, "清理临时文件")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def translate_minecraft(self, mc_path, options=None, progress_callback=None):
        """
        翻译Minecraft版本
        
        Args:
            mc_path: Minecraft版本文件夹路径
            options: 翻译选项
            progress_callback: 进度回调函数
            
        Returns:
            输出的汉化资源包路径
        """
        self.progress_callback = progress_callback
        
        if options is None:
            options = {
                "translate_items": True,
                "translate_entities": True,
                "translate_advancements": True,
                "translate_misc": True
            }
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="minecraft_translator_")
        self._update_progress(5, "创建临时工作目录")
        
        try:
            # 检查Minecraft版本文件夹
            # 首先检查常规的assets目录
            assets_dir = os.path.join(mc_path, "assets")
            
            # 如果常规assets目录不存在，尝试查找jar文件并从中提取assets
            if not os.path.exists(assets_dir):
                # 查找版本jar文件
                jar_files = [f for f in os.listdir(mc_path) if f.endswith(".jar")]
                if jar_files:
                    jar_path = os.path.join(mc_path, jar_files[0])
                    # 解压jar文件到临时目录
                    jar_extract_dir = os.path.join(self.temp_dir, "jar_extracted")
                    os.makedirs(jar_extract_dir, exist_ok=True)
                    
                    self._update_progress(10, f"从JAR文件提取资源: {os.path.basename(jar_path)}")
                    with zipfile.ZipFile(jar_path, 'r') as zip_ref:
                        zip_ref.extractall(jar_extract_dir)
                    
                    # 检查解压后的目录中是否有assets
                    extracted_assets_dir = os.path.join(jar_extract_dir, "assets")
                    if os.path.exists(extracted_assets_dir):
                        assets_dir = extracted_assets_dir
                    else:
                        raise Exception(f"无效的Minecraft版本文件夹: {mc_path}，未找到assets目录")
                else:
                    raise Exception(f"无效的Minecraft版本文件夹: {mc_path}，未找到assets目录或版本JAR文件")
            
            # 创建资源包结构
            pack_dir = os.path.join(self.temp_dir, "resourcepack")
            os.makedirs(pack_dir, exist_ok=True)
            
            # 创建资源包元数据
            self._create_resourcepack_metadata(pack_dir)
            
            # 查找语言文件
            self._update_progress(15, "查找语言文件")
            lang_files = self._find_minecraft_lang_files(assets_dir)
            
            if not lang_files:
                raise Exception("未找到可翻译的语言文件")
            
            self._update_progress(20, f"找到 {len(lang_files)} 个语言文件")
            
            # 翻译语言文件
            translated_files = []
            total_files = len(lang_files)
            
            for i, lang_file in enumerate(lang_files):
                progress = 20 + (i / total_files) * 60
                self._update_progress(progress, f"翻译文件 ({i+1}/{total_files}): {os.path.basename(lang_file)}")
                
                # 创建中文语言文件路径
                rel_path = os.path.relpath(lang_file, assets_dir)
                zh_lang_file = os.path.join(pack_dir, "assets", rel_path.replace(".json", "_zh_cn.json"))
                os.makedirs(os.path.dirname(zh_lang_file), exist_ok=True)
                
                # 翻译文件
                self._translate_minecraft_lang_file(lang_file, zh_lang_file, options)
                translated_files.append(zh_lang_file)
            
            # 打包资源包
            self._update_progress(85, "打包汉化资源包")
            output_dir = os.path.dirname(mc_path)
            output_name = f"汉化资源包_{os.path.basename(mc_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_path = os.path.join(output_dir, output_name)
            
            shutil.make_archive(output_path, 'zip', pack_dir)
            final_path = f"{output_path}.zip"
            
            self._update_progress(95, "汉化资源包打包完成")
            return final_path
            
        finally:
            # 清理临时目录
            self._update_progress(100, "清理临时文件")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _detect_mod_type(self, extract_dir):
        """
        检测MOD类型
        """
        # 检查是否为Fabric MOD
        if os.path.exists(os.path.join(extract_dir, "fabric.mod.json")):
            return "fabric"
        
        # 检查是否为NeoForge MOD
        if os.path.exists(os.path.join(extract_dir, "META-INF", "mods.toml")):
            # 检查mods.toml内容以区分NeoForge和Forge
            with open(os.path.join(extract_dir, "META-INF", "mods.toml"), 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if "neoforge" in content.lower():
                    return "neoforge"
                else:
                    return "forge"
        
        # 默认为Forge
        return "forge"
    
    def _find_lang_files(self, extract_dir, mod_type):
        """
        查找MOD中的语言文件
        """
        lang_files = []
        
        # 根据MOD类型查找语言文件
        if mod_type == "fabric":
            # Fabric MOD通常将语言文件放在assets/<modid>/lang/目录下
            assets_dir = os.path.join(extract_dir, "assets")
            if os.path.exists(assets_dir):
                for mod_dir in os.listdir(assets_dir):
                    lang_dir = os.path.join(assets_dir, mod_dir, "lang")
                    if os.path.exists(lang_dir):
                        for file in os.listdir(lang_dir):
                            if file.endswith(".json") and not file.startswith("zh_"):
                                lang_files.append(os.path.join(lang_dir, file))
        
        elif mod_type in ["forge", "neoforge"]:
            # Forge/NeoForge MOD通常将语言文件放在assets/<modid>/lang/目录下
            assets_dir = os.path.join(extract_dir, "assets")
            if os.path.exists(assets_dir):
                for mod_dir in os.listdir(assets_dir):
                    lang_dir = os.path.join(assets_dir, mod_dir, "lang")
                    if os.path.exists(lang_dir):
                        for file in os.listdir(lang_dir):
                            if file.endswith(".json") and not file.startswith("zh_"):
                                lang_files.append(os.path.join(lang_dir, file))
        
        return lang_files
    
    def _find_minecraft_lang_files(self, assets_dir):
        """
        查找Minecraft中的语言文件
        """
        lang_files = []
        
        # 遍历assets目录查找语言文件
        for root, _, files in os.walk(assets_dir):
            if os.path.basename(root) == "lang":
                for file in files:
                    if file.endswith(".json") and not file.startswith("zh_"):
                        lang_files.append(os.path.join(root, file))
        
        return lang_files
    
    def _get_zh_lang_path(self, lang_file):
        """
        获取中文语言文件路径
        """
        dir_name = os.path.dirname(lang_file)
        file_name = os.path.basename(lang_file)
        
        # 替换语言代码为zh_cn
        if "_" in file_name:
            # 如果文件名包含语言代码（如en_us.json）
            zh_file_name = "zh_cn.json"
        else:
            # 如果文件名不包含语言代码，添加前缀
            zh_file_name = "zh_cn_" + file_name
        
        return os.path.join(dir_name, zh_file_name)
    
    def _translate_lang_file(self, src_file, dst_file, options):
        """
        翻译语言文件
        """
        try:
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                lang_data = json.load(f)
            
            # 过滤需要翻译的键值对
            to_translate = {}
            for key, value in lang_data.items():
                # 跳过命令相关的文本
                if key.startswith("commands.") or "command" in key.lower():
                    continue
                
                # 根据选项过滤
                if not options.get("translate_desc", True) and ".desc" in key:
                    continue
                
                if not options.get("translate_tooltip", True) and ".tooltip" in key:
                    continue
                
                if not options.get("translate_gui", True) and ".gui" in key:
                    continue
                
                # 只翻译字符串值
                if isinstance(value, str) and value.strip() and not value.isdigit():
                    # 跳过已经是中文的文本
                    if self._is_chinese(value):
                        continue
                    
                    to_translate[key] = value
            
            # 批量翻译
            translated = self._batch_translate(to_translate)
            
            # 合并翻译结果
            result = {}
            for key, value in lang_data.items():
                if key in translated:
                    result[key] = translated[key]
                else:
                    result[key] = value
            
            # 写入翻译后的文件
            with open(dst_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            return True
            
        except Exception as e:
            print(f"翻译文件 {src_file} 时出错: {str(e)}")
            return False
    
    def _translate_minecraft_lang_file(self, src_file, dst_file, options):
        """
        翻译Minecraft语言文件
        """
        try:
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                lang_data = json.load(f)
            
            # 过滤需要翻译的键值对
            to_translate = {}
            for key, value in lang_data.items():
                # 跳过命令相关的文本
                if key.startswith("commands.") or "command" in key.lower():
                    continue
                
                # 根据选项过滤
                if not options.get("translate_items", True) and "item." in key:
                    continue
                
                if not options.get("translate_entities", True) and "entity." in key:
                    continue
                
                if not options.get("translate_advancements", True) and "advancements." in key:
                    continue
                
                if not options.get("translate_misc", True) and not any(x in key for x in ["item.", "entity.", "advancements."]):
                    continue
                
                # 只翻译字符串值
                if isinstance(value, str) and value.strip() and not value.isdigit():
                    # 跳过已经是中文的文本
                    if self._is_chinese(value):
                        continue
                    
                    to_translate[key] = value
            
            # 批量翻译
            translated = self._batch_translate(to_translate)
            
            # 合并翻译结果
            result = {}
            for key, value in lang_data.items():
                if key in translated:
                    result[key] = translated[key]
                else:
                    result[key] = value
            
            # 写入翻译后的文件
            with open(dst_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            return True
            
        except Exception as e:
            print(f"翻译文件 {src_file} 时出错: {str(e)}")
            return False
    
    def _batch_translate(self, text_dict, batch_size=20):
        """
        批量翻译文本
        
        Args:
            text_dict: 要翻译的文本字典 {key: text}
            batch_size: 每批翻译的文本数量
            
        Returns:
            翻译后的文本字典 {key: translated_text}
        """
        if not text_dict:
            return {}
        
        result = {}
        keys = list(text_dict.keys())
        total_batches = (len(keys) + batch_size - 1) // batch_size
        
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i:i+batch_size]
            batch_texts = [text_dict[key] for key in batch_keys]
            
            # 构建批量翻译的提示
            prompt = self._create_translation_prompt(batch_texts)
            
            # 调用API进行翻译
            try:
                # 更新进度
                batch_num = i // batch_size + 1
                self._update_progress(None, f"翻译批次 {batch_num}/{total_batches} ({len(batch_keys)} 个文本)")
                
                # 调用API
                self._update_progress(None, f"正在调用翻译API...")
                translated_texts = self._call_translation_api(prompt, batch_texts)
                
                # 将翻译结果添加到结果字典中
                for j, key in enumerate(batch_keys):
                    if j < len(translated_texts):
                        result[key] = translated_texts[j]
                    else:
                        # 如果翻译结果不足，保留原文
                        result[key] = text_dict[key]
                
                self._update_progress(None, f"批次 {batch_num} 翻译完成")
                
            except Exception as e:
                error_msg = str(e)
                self._update_progress(None, f"批量翻译时出错: {error_msg}")
                print(f"批量翻译时出错: {error_msg}")
                
                # 出错时保留原文
                for key in batch_keys:
                    result[key] = text_dict[key]
                
                # 如果是第一批就失败，可能是API配置问题，直接抛出异常
                if i == 0:
                    raise Exception(f"调用翻译API时出错: {error_msg}")
            
        return result
    
    def _create_translation_prompt(self, texts):
        """
        创建翻译提示
        """
        prompt = """你是一个专业的Minecraft游戏翻译专家，请将以下Minecraft游戏或MOD中的英文（或其他非中文语言）文本翻译成简体中文。

翻译要求：
1. 保持Minecraft的游戏术语风格
2. 对于物品名称、生物名称等，使用Minecraft中已有的官方中文翻译
3. 保留原文中的格式标记（如%s, %d, {0}, $1等占位符）
4. 不要翻译命令名称和技术术语
5. 翻译要简洁、准确、符合中文表达习惯
6. 直接输出翻译结果，每行一个翻译，不要有多余的解释

以下是需要翻译的文本：
"""
        
        for text in texts:
            prompt += f"{text}\n"
        
        prompt += "\n请按照原文顺序，直接输出翻译结果，每行一个翻译："
        
        return prompt
    
    def _call_translation_api(self, prompt, original_texts):
        """
        调用翻译API
        """
        # 打印API调用信息，便于调试
        print(f"正在调用翻译API...")
        print(f"使用模型: {self.model}")
        
        # 确保API URL是正确的
        api_url = self.api_url
        # 移除可能的尾部斜杠
        if api_url.endswith("/"):
            api_url = api_url[:-1]
        
        print(f"使用API端点: {api_url}")
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 准备请求数据 - 按照Ollama API格式
        data = {
            "model": self.model,
            "prompt": f"你是一个专业的Minecraft游戏翻译专家，擅长将游戏文本翻译成简体中文。\n\n{prompt}",
            "stream": False
        }
        
        try:
            # 发送POST请求
            print(f"发送请求到: {api_url}")
            response = requests.post(api_url, headers=headers, json=data, timeout=60)
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API返回错误状态码: {response.status_code} - {response.reason}"
                if response.text:
                    error_msg += f"\n响应内容: {response.text[:200]}..."
                raise Exception(error_msg)
            
            # 解析JSON响应
            try:
                result = response.json()
                print("成功解析API响应为JSON")
            except ValueError as json_err:
                # 如果返回的是HTML而不是JSON，可能是API URL错误
                if "<!doctype html>" in response.text.lower():
                    raise Exception(f"API URL可能指向了Web界面而不是API端点。请检查API URL配置。\n响应内容: {response.text[:200]}...")
                else:
                    raise Exception(f"无法解析API响应为JSON: {json_err}\n响应内容: {response.text[:200]}...")
            
            # 处理翻译结果 - 根据API响应格式提取内容
            content = ""
            
            # 尝试不同的响应格式
            if "response" in result:
                # 标准Ollama格式
                content = result["response"]
                print("使用Ollama响应格式解析结果")
            elif "results" in result and len(result["results"]) > 0:
                # OpenWebUI格式
                content = result["results"][0]["text"]
                print("使用OpenWebUI响应格式解析结果")
            elif "choices" in result and len(result["choices"]) > 0:
                # OpenAI格式
                if "message" in result["choices"][0]:
                    content = result["choices"][0]["message"]["content"]
                elif "text" in result["choices"][0]:
                    content = result["choices"][0]["text"]
                else:
                    print(f"警告: 未知的API响应格式: {result}")
                    return original_texts
            else:
                print(f"警告: 无法识别的API响应格式: {result}")
                return original_texts
            
            # 解析翻译结果
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            
            # 过滤掉可能的非翻译行（如解释性文本）
            translated_texts = []
            for line in lines:
                if not line.startswith("原文") and not line.startswith("翻译") and not line.startswith("注"):
                    translated_texts.append(line)
            
            # 确保翻译结果数量与原文数量一致
            if len(translated_texts) < len(original_texts):
                print(f"警告: 翻译结果数量 ({len(translated_texts)}) 少于原文数量 ({len(original_texts)})")
                # 对于缺失的翻译，使用原文
                while len(translated_texts) < len(original_texts):
                    translated_texts.append(original_texts[len(translated_texts)])
            
            return translated_texts[:len(original_texts)]
            
        except Exception as e:
            error_msg = str(e)
            print(f"调用翻译API时出错: {error_msg}")
            # 将错误信息传递给上层函数
            raise Exception(f"调用翻译API时出错: {error_msg}")
    
    def _create_resourcepack_metadata(self, pack_dir):
        """
        创建资源包元数据
        """
        # 创建pack.mcmeta文件
        pack_mcmeta = {
            "pack": {
                "pack_format": 9,  # 适用于较新版本的Minecraft
                "description": "§6AI自动汉化资源包\n§7由Minecraft翻译器生成"
            }
        }
        
        with open(os.path.join(pack_dir, "pack.mcmeta"), 'w', encoding='utf-8') as f:
            json.dump(pack_mcmeta, f, ensure_ascii=False, indent=4)
        
        # 创建assets目录
        os.makedirs(os.path.join(pack_dir, "assets"), exist_ok=True)
    
    def _create_output_path(self, input_path, suffix):
        """
        创建输出文件路径
        """
        dir_name = os.path.dirname(input_path)
        file_name = os.path.basename(input_path)
        name, ext = os.path.splitext(file_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{name}{suffix}_{timestamp}{ext}"
        
        return os.path.join(dir_name, new_name)
    
    def _is_chinese(self, text):
        """
        检查文本是否包含中文字符
        """
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def _update_progress(self, progress=None, message=None):
        """
        更新进度
        """
        if self.progress_callback:
            self.progress_callback(progress if progress is not None else 0, message)
        elif message:
            print(message)